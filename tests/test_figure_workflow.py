import copy
from contextlib import redirect_stderr
from importlib.util import find_spec
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import fetch_papers, plan_diagram, render_diagram
from scripts.score_papers import calculate_scores


ROOT = Path(__file__).resolve().parents[1]
HAS_MPL = find_spec('matplotlib') is not None
HAS_PDF = find_spec('pymupdf') is not None
HAS_PIL = find_spec('PIL') is not None


def source():
    spec = json.loads((ROOT / 'templates' / 'multiscale-architecture.json').read_text('utf-8'))
    spec['sources'] = [item for item in spec['sources'] if item['kind'] != 'figure']
    spec['design_review']['precedents'] = []
    spec['design_review'].pop('shape_choices')
    return spec


def figure(identifier, doi, *, url='', publication='published'):
    return {
        'id': identifier, 'kind': 'figure', 'title': 'Synthetic record ' + identifier,
        'locator': 'Fig. 2', 'doi': doi, 'url': url, 'takeaway': 'Mark the decoder skip',
        'inspection': {'location': 'Figure page supplied to the test', 'publication': publication},
    }


class GroundedDesignTests(unittest.TestCase):
    def test_duplicate_and_malformed_records_cannot_meet_paper_minimum(self):
        spec = source()
        spec.pop('design_review')
        spec['sources'] += [
            figure('doi', '10.2222/example'),
            figure('same-doi', '', url='https://doi.org/10.2222/EXAMPLE'),
            figure('preprint', '10.48550/arxiv.2401.00001'),
            figure('same-preprint', '', url='https://arxiv.org/pdf/2401.00001v3.pdf'),
            figure('invalid', 'made-up-doi'),
        ]
        receipt = render_diagram.provenance(spec)
        self.assertEqual(receipt['paper_figures_inspected'], 2)
        self.assertEqual(receipt['duplicate_paper_sources'],
                         [['doi', 'same-doi'], ['preprint', 'same-preprint']])
        self.assertEqual(receipt['incomplete_figure_sources'], ['invalid'])
        with self.assertRaisesRegex(ValueError, 'found 2'):
            render_diagram.enforce_review(receipt, require_paper_figures=True)

    def test_visual_precedent_does_not_supply_method_provenance(self):
        spec = source()
        spec.pop('design_review')
        spec['sources'].append(figure('only-figure', '10.2222/example'))
        spec['edges'][0]['source_refs'] = ['only-figure']
        with self.assertRaisesRegex(ValueError, 'method, code, or dataset'):
            render_diagram.enforce_review(render_diagram.provenance(spec), require_sources=True)

    def test_relationship_must_identify_an_existing_drawn_edge(self):
        spec = source()
        item = spec['design_review']['checks'][1]
        item['elements'] = ['nodes:encoder']
        with self.assertRaisesRegex(ValueError, 'drawn edge'):
            render_diagram.validate_spec(spec)
        item['elements'] = ['edges:misspelled']
        with self.assertRaisesRegex(ValueError, 'existing diagram elements'):
            render_diagram.validate_spec(spec)

    def test_inspected_published_count_depends_on_mapped_reviews(self):
        spec = source()
        spec['sources'] += [
            figure('printed', '10.2222/printed'),
            figure('unpublished', '', url='https://arxiv.org/abs/2401.00001', publication='preprint'),
        ]
        rows = spec['design_review']['precedents']
        rows.append({'source': 'printed', 'observation': 'Shows one explicit skip',
                     'decision': 'Draw an edge into the decoder',
                     'elements': ['edges:difference-1-to-decoder-1']})
        with self.assertRaisesRegex(ValueError, 'unpublished'):
            render_diagram.enforce_review(render_diagram.provenance(spec), require_design_review=True)
        rows.append({'source': 'unpublished', 'observation': 'Uses one formula for all scales',
                     'decision': 'Omit formula from the overview',
                     'omission_reason': 'Separate scale paths answer the reader question'})
        receipt = render_diagram.provenance(spec)
        self.assertEqual(receipt['design_review']['reported_published_papers'], 1)
        render_diagram.enforce_review(receipt, require_sources=True, require_design_review=True,
                                     require_paper_figures=True, min_paper_figures=1)
        with self.assertRaisesRegex(ValueError, 'found 1'):
            render_diagram.enforce_review(receipt, require_design_review=True,
                                         require_paper_figures=True, min_paper_figures=2)

    @unittest.skipUnless(HAS_MPL and HAS_PIL, 'Optional rendering dependencies are not installed')
    def test_multiscale_example_renders_every_skip_at_target_width(self):
        spec = source()
        routes = {(e['from'], e['to']) for e in spec['edges']}
        self.assertTrue(all((f'difference-{level}', f'decoder-{level}') in routes for level in (1, 2, 3, 4)))
        self.assertTrue(all((f'decoder-{level+1}', f'decoder-{level}') in routes for level in (1, 2, 3)))
        with tempfile.TemporaryDirectory() as out:
            report = render_diagram.render(spec, out, preview_only=True, profile='ieee-double',
                                           require_sources=True, require_design_review=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        self.assertEqual(report['provenance']['design_review']['reader_checks'], 4)
        self.assertEqual(spec['canvas']['width_pt'], 457.2)


class ShortlistAndLayoutTests(unittest.TestCase):
    def test_unrated_topics_use_metadata_without_claiming_inspection(self):
        ranked = calculate_scores([
            {'title': 'Popular history survey', 'year': 2026, 'citations': 10000},
            {'title': 'Optical radar change detection', 'year': 2024, 'citations': 0},
        ], 2026, topic='optical radar change detection')
        self.assertEqual(ranked[0]['title'], 'Optical radar change detection')
        self.assertEqual(ranked[0]['topic_score_basis'], 'title_terms')
        self.assertFalse(ranked[0].get('figure_inspected'))

    def test_shortlist_preserves_provider_variety_and_reports_partial_failure(self):
        def rows(provider, count):
            return [{'title': f'Routing {provider} {i}', 'oa_status': 'green',
                     'citation_source': provider, 'pdf_url': f'https://example.org/{provider}/{i}.pdf'}
                    for i in range(count)]
        with patch.object(fetch_papers, 'fetch_openalex', return_value=rows('OpenAlex', 25)), \
                patch.object(fetch_papers, 'fetch_arxiv', return_value=rows('arXiv', 5)):
            candidates = fetch_papers.search_papers('routing', limit=5, oa_only=True)
        self.assertEqual(len(candidates), 5)
        self.assertEqual({r['citation_source'] for r in candidates}, {'OpenAlex', 'arXiv'})
        with redirect_stderr(StringIO()) as stderr, \
                patch.object(fetch_papers, 'fetch_openalex', side_effect=TimeoutError('fixture timeout')), \
                patch.object(fetch_papers, 'fetch_arxiv', return_value=rows('arXiv', 1)):
            candidates = fetch_papers.search_papers('routing')
        self.assertEqual(len(candidates), 1)
        self.assertIn('Partial paper search: openalex', stderr.getvalue())

    @unittest.skipUnless(HAS_MPL and HAS_PIL, 'Optional rendering dependencies are not installed')
    def test_skip_corridor_recovery_at_fixed_width_preserves_all_edges(self):
        method = {'title': 'Routing control', 'direction': 'vertical', 'canvas': {'width_pt': 400},
                  'nodes': [{'id': key, 'label': label} for key, label in (
                      ('a', 'Shortcut input'), ('b', 'Long path input'), ('c', 'Process'), ('d', 'Merge'))],
                  'edges': [{'id': a + b, 'from': a, 'to': b} for a, b in [('a', 'd'), ('b', 'c'), ('c', 'd')]]}
        original = copy.deepcopy(method)
        selected = plan_diagram.choose_layout(method, fixed_width=True)
        self.assertEqual(method, original)
        self.assertEqual(selected['canvas']['width_pt'], 400)
        self.assertFalse(selected['layout_plan']['attempts'][0]['passed'])
        self.assertEqual(selected['layout_plan']['selected_strategy'], 'left-skip-corridor')
        self.assertEqual({(e['from'], e['to']) for e in selected['edges']},
                         {(e['from'], e['to']) for e in method['edges']})
        with tempfile.TemporaryDirectory() as out:
            report = render_diagram.render(selected, out, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])


@unittest.skipUnless(HAS_PDF and HAS_PIL, 'Optional PDF and image dependencies are not installed')
class VectorPaperTest(unittest.TestCase):
    def test_vector_figure_page_and_candidate_caption_are_indexed(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'vector.pdf'
            with pymupdf.open() as doc:
                page = doc.new_page()
                page.draw_rect((20, 20, 200, 80), color=(0, 0, 0))
                page.insert_text((20, 120), 'Figure 2. Vector diagram caption')
                doc.save(path)
            dest = root / 'pages'
            subprocess.run([sys.executable, str(ROOT / 'scripts' / 'extract_pdf_figures.py'),
                            str(path), '--output-dir', str(dest), '--pages-only'],
                           capture_output=True, check=True)
            data = json.loads((dest / 'vector_figure_candidates.json').read_text('utf-8'))
            self.assertEqual(data['pages'][0]['caption_candidates'][0]['figure_label'], '2')
            self.assertTrue((dest / 'vector_page_001.png').is_file())
            sheet = root / 'contact.png'
            subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build_contact_sheet.py'),
                            str(dest), '--output', str(sheet), '--pages-only'],
                           capture_output=True, check=True)
            self.assertTrue(sheet.is_file())
