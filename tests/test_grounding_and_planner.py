"""Comprehensive test suite for literature grounding, layout planner, and diagram exports."""
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from matplotlib.path import Path as MplPath

from scripts import render_diagram as renderer
from scripts import themes
from scripts import vector_icons
from scripts import plan_diagram
from scripts import export_drawio
from scripts import fetch_papers
from scripts import score_papers

ROOT = Path(__file__).resolve().parents[1]


def minimal_spec():
    return {
        'title': 'Test Schematic',
        'canvas': {'width_pt': 320, 'height_pt': 220, 'font_pt': 9, 'min_font_pt': 8.0},
        'nodes': [
            {'id': 'a', 'label': 'Start Process', 'box': [20, 30, 100, 40]},
            {'id': 'b', 'label': 'End Outcome', 'box': [180, 30, 100, 40]},
        ],
        'edges': [
            {'id': 'e1', 'from': 'a', 'to': 'b', 'points': [[120, 50], [180, 50]]}
        ]
    }


class RendererHardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def draw(self, spec, **kwargs):
        return renderer.render(spec, self.out, stem='test-hardening', dpi=150, **kwargs)

    def test_plos_one_profile_with_legend_does_not_raise_keyerror(self):
        spec = minimal_spec()
        spec['canvas']['font_family'] = 'Arial'
        spec['canvas']['font_pt'] = 9.0
        spec['canvas']['min_font_pt'] = 8.0
        spec['legend'] = {
            'box': [20, 160, 260, 40],
            'frame': False,
            'items': [
                {'label': 'Dense Retrieval', 'kind': 'node', 'color': '#D0E2FF'},
                {'label': 'Benchmark Path', 'kind': 'edge', 'color': '#0F62FE', 'stroke_color': '#0F62FE', 'dashes': [3, 2]}
            ]
        }
        try:
            report = renderer.render(spec, self.out, stem='plos-legend-test', profile='plos-one', dpi=300)
            self.assertTrue(report['passed_geometry_checks'], report.get('errors'))
        except KeyError as e:
            self.fail(f"render() raised KeyError: {e}")

    def test_legend_item_stroke_color_validation(self):
        spec = minimal_spec()
        spec['legend'] = {
            'box': [20, 160, 200, 30],
            'items': [{'label': 'Item 1', 'stroke_color': 'invalid-hex-color'}]
        }
        with self.assertRaises(ValueError):
            renderer.validate_spec(spec)

    def test_single_label_badge_and_accent_padding(self):
        spec = minimal_spec()
        spec['nodes'][0]['accent'] = 'left'
        spec['nodes'][0]['badge'] = 'Step 1'
        # Renders single-label node without detail cleanly with insets applied
        report = self.draw(spec, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(len(report['errors']), 0)

    def test_single_label_title_icon_with_badge_and_accent_no_double_inset(self):
        spec = minimal_spec()
        spec['nodes'][0]['accent'] = 'left'
        spec['nodes'][0]['badge'] = 'STEP 1'
        spec['icons'] = [
            {'id': 'ic1', 'node': 'a', 'vector_icon': 'database', 'placement': 'title', 'size_pt': [16, 16], 'alt': 'Database icon'}
        ]
        report = self.draw(spec, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(len(report['errors']), 0)

    def test_single_label_badge_collision_detection(self):
        spec = minimal_spec()
        spec['canvas']['font_pt'] = 14
        spec['canvas']['min_font_pt'] = 14
        # Place a tiny node where badge and large label would collide
        spec['nodes'][0]['box'] = [20, 30, 60, 18]
        spec['nodes'][0]['badge'] = 'Very Long Badge Label'
        spec['nodes'][0]['label'] = 'Multi Line Very Tall Text Block'
        report = self.draw(spec, preview_only=True)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('badge' in err.lower() for err in report['errors']))

    def test_badge_corner_clearance_input_terminator(self):
        spec = minimal_spec()
        spec['nodes'][0]['shape'] = 'input'
        spec['nodes'][0]['badge'] = 'Step 1'
        spec['nodes'][1]['shape'] = 'terminator'
        spec['nodes'][1]['badge'] = 'End'
        report = self.draw(spec, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])

    def test_default_group_border_style_is_dashed(self):
        spec = minimal_spec()
        spec['nodes'][0]['box'] = [20, 60, 100, 40]
        spec['nodes'][0]['group'] = 'g1'
        spec['nodes'][1]['box'] = [180, 60, 100, 40]
        spec['nodes'][1]['group'] = 'g1'
        spec['edges'][0]['points'] = [[120, 80], [180, 80]]
        spec['nodes'].append({
            'id': 'g1',
            'shape': 'group',
            'label': 'Group Container',
            'box': [10, 10, 290, 180]
        })
        res = self.draw(spec)
        self.assertTrue(res['passed_geometry_checks'])
        svg_content = (self.out / 'test-hardening.svg').read_text(encoding='utf-8')
        self.assertIn('stroke-dasharray', svg_content)

    def test_apply_theme_type_safety(self):
        self.assertIsNone(themes.apply_theme(None))
        self.assertEqual(themes.apply_theme("not-a-dict"), "not-a-dict")
        malformed = {'style': 'not-a-dict', 'nodes': 'not-a-list'}
        res = themes.apply_theme(malformed)
        self.assertEqual(res, malformed)

    def test_crossing_jump_named_and_indexed_edges(self):
        spec = {
            'title': 'Crossing Jump Test',
            'canvas': {'width_pt': 200, 'height_pt': 200, 'font_pt': 9, 'min_font_pt': 8.0},
            'nodes': [
                {'id': 'n1', 'label': 'N1', 'box': [20, 70, 40, 30]},
                {'id': 'n2', 'label': 'N2', 'box': [140, 70, 40, 30]},
                {'id': 'n3', 'label': 'N3', 'box': [80, 20, 40, 30]},
                {'id': 'n4', 'label': 'N4', 'box': [80, 140, 40, 30]},
            ],
            'edges': [
                {'id': 'edge-h', 'from': 'n1', 'to': 'n2', 'points': [[60, 85], [140, 85]]},
                {'from': 'n3', 'to': 'n4', 'points': [[100, 50], [100, 140]]}
            ],
            'allowed_crossings': [{'edges': ['edge-h', '1'], 'kind': 'crossing_jump', 'reason': 'Orthogonal bus line crossing'}]
        }
        report = self.draw(spec, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])

    def test_legend_edge_line_swatches(self):
        spec = minimal_spec()
        spec['legend'] = {
            'box': [20, 150, 260, 50],
            'title': 'Legend',
            'items': [
                {'label': 'Direct flow', 'kind': 'edge', 'stroke_color': '#334E68', 'line_width_pt': 1.5, 'arrow': True},
                {'label': 'Optional flow', 'shape': 'line', 'stroke_color': '#B00020', 'border_style': 'dashed'}
            ]
        }
        res = self.draw(spec)
        self.assertTrue(res['passed_geometry_checks'])
        svg_content = (self.out / 'test-hardening.svg').read_text(encoding='utf-8')
        self.assertIn('Direct flow', svg_content)
        self.assertIn('Optional flow', svg_content)

    def test_legend_edge_collision_and_slot_overflow(self):
        # 1. Edge crossing legend box
        spec = minimal_spec()
        spec['legend'] = {
            'box': [100, 40, 100, 40],
            'items': [{'label': 'Key', 'color': '#1B4965'}]
        }
        report = self.draw(spec, preview_only=True)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('legend' in err.lower() for err in report['errors']))

        # 2. Text slot width overflow
        spec2 = minimal_spec()
        spec2['legend'] = {
            'box': [20, 150, 80, 40],
            'columns': 4,
            'items': [{'label': 'Exceedingly Long Unbroken Label That Cannot Fit Slot', 'color': '#1B4965'}]
        }
        report2 = self.draw(spec2, preview_only=True)
        self.assertTrue(any('overflows allocated slot' in err for err in report2['errors']))

    def test_export_drawio_vector_icon_and_escaped_legend(self):
        spec = minimal_spec()
        spec['nodes'][0]['icon_space_pt'] = 24
        spec['icons'] = [
            {'id': 'ic1', 'node': 'a', 'vector_icon': 'database', 'box': [24, 42, 16, 16], 'alt': 'Database icon'}
        ]
        spec['legend'] = {
            'box': [20, 150, 260, 50],
            'title': 'Symbols & Notes',
            'items': [
                {'label': 'A < B & C > D', 'kind': 'edge', 'stroke_color': '#334E68'}
            ]
        }
        res = self.draw(spec, drawio=True)
        drawio_path = self.out / 'test-hardening.drawio'
        self.assertTrue(drawio_path.exists())
        content = drawio_path.read_text(encoding='utf-8')
        # Check XML escaping of legend text in drawio
        self.assertIn('&amp;lt;', content)
        self.assertIn('&amp;amp;', content)
        # Check vector icon data uri
        self.assertIn('data:image/svg+xml;base64,', content)

    def test_plan_supports_vector_icons(self):
        method = {
            'title': 'Icon Pipeline',
            'canvas': {'width_pt': 300},
            'nodes': [
                {'id': 'n1', 'label': 'Raw Data', 'vector_icon': 'database'},
                {'id': 'n2', 'label': 'Model AI', 'vector_icon': 'brain'}
            ],
            'edges': [
                {'from': 'n1', 'to': 'n2'}
            ]
        }
        planned = plan_diagram.plan(method)
        self.assertIn('icons', planned)
        self.assertEqual(len(planned['icons']), 2)
        self.assertEqual(planned['icons'][0]['vector_icon'], 'database')


class CustomSvgIconsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_local_svg_security_rejections(self):
        # 1. ENTITY
        p = self.dir / 'entity.svg'
        p.write_text('<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><svg>&xxe;</svg>', encoding='utf-8')
        with self.assertRaises(ValueError):
            vector_icons.load_local_svg(p)

        # 2. xml-stylesheet
        p = self.dir / 'stylesheet.svg'
        p.write_text('<?xml-stylesheet type="text/css" href="http://evil.com/style.css"?><svg></svg>', encoding='utf-8')
        with self.assertRaises(ValueError):
            vector_icons.load_local_svg(p)

        # 3. script tag
        p = self.dir / 'script.svg'
        p.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', encoding='utf-8')
        with self.assertRaises(ValueError):
            vector_icons.load_local_svg(p)

        # 4. foreignObject
        p = self.dir / 'foreign.svg'
        p.write_text('<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><body>iframe</body></foreignObject></svg>', encoding='utf-8')
        with self.assertRaises(ValueError):
            vector_icons.load_local_svg(p)

        # 5. onclick event handler
        p = self.dir / 'onclick.svg'
        p.write_text('<svg xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="5" onclick="run()"/></svg>', encoding='utf-8')
        with self.assertRaises(ValueError):
            vector_icons.load_local_svg(p)

        # 6. external href
        p = self.dir / 'href.svg'
        p.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="http://evil.com/pic.png"/></svg>', encoding='utf-8')
        with self.assertRaises(ValueError):
            vector_icons.load_local_svg(p)

    def test_parse_svg_path_curves(self):
        d = "M 10 10 Q 20 20 30 30 T 40 40 S 50 50 60 60 s 10 10 20 20 Z"
        path_obj = vector_icons.parse_svg_path(d)
        self.assertIsInstance(path_obj, MplPath)
        self.assertIn(MplPath.CURVE3, path_obj.codes)
        self.assertIn(MplPath.CURVE4, path_obj.codes)

    def test_render_diagram_pure_vector_with_svg_icon(self):
        svg_icon = self.dir / 'custom_icon.svg'
        svg_icon.write_text(
            '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="12" cy="12" r="10" fill="none" stroke="#000000" stroke-width="2"/>'
            '</svg>',
            encoding='utf-8'
        )
        spec = minimal_spec()
        spec['nodes'][0]['icon_space_pt'] = 24
        spec['icons'] = [
            {'id': 'ic1', 'node': 'a', 'path': 'custom_icon.svg', 'box': [24, 42, 16, 16], 'alt': 'Custom icon'}
        ]
        res = renderer.render(spec, self.dir / 'out', stem='pure-vector', asset_dir=self.dir, drawio=True)
        # Check pure vector: no <image> tag in output SVG
        svg_content = (self.dir / 'out' / 'pure-vector.svg').read_text(encoding='utf-8')
        self.assertNotIn('<image', svg_content)
        # Check warnings: no raster icon warning
        self.assertFalse(any('raster icon' in w.lower() for w in res['warnings']))

        # Check Draw.io embed
        drawio_content = (self.dir / 'out' / 'pure-vector.drawio').read_text(encoding='utf-8')
        self.assertIn('data:image/svg+xml;base64,', drawio_content)

        # Check asset directory copying
        assets_dir = self.dir / 'out' / 'pure-vector-assets'
        self.assertTrue(assets_dir.exists())
        self.assertTrue((assets_dir / 'ic1.svg').exists())


class LayeredPlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_skip_rank_dag_routing(self):
        method = {
            'title': 'Skip Rank DAG',
            'canvas': {'width_pt': 320},
            'nodes': [
                {'id': 'step1', 'label': 'Stage 1 Input'},
                {'id': 'step2', 'label': 'Stage 2 Intermediate'},
                {'id': 'step3', 'label': 'Stage 3 Outcome'}
            ],
            'edges': [
                {'from': 'step1', 'to': 'step2'},
                {'from': 'step2', 'to': 'step3'},
                {'from': 'step1', 'to': 'step3'}  # Skips step2
            ]
        }
        planned = plan_diagram.plan(method)
        report = renderer.render(planned, self.out, stem='skip-dag', preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(len(report['errors']), 0)

    def test_cyclic_feedback_loop_routing(self):
        method = {
            'title': 'Feedback Loop Method',
            'canvas': {'width_pt': 320},
            'nodes': [
                {'id': 'init', 'label': 'Initialize Model'},
                {'id': 'train', 'label': 'Train Epoch'},
                {'id': 'eval', 'label': 'Evaluate Metric', 'shape': 'decision'}
            ],
            'edges': [
                {'from': 'init', 'to': 'train'},
                {'from': 'train', 'to': 'eval'},
                {'from': 'eval', 'to': 'train', 'label': 'Repeat'}  # Cyclic back-edge
            ]
        }
        planned = plan_diagram.plan(method)
        self.assertIn('layout_plan', planned)
        self.assertEqual(len(planned['layout_plan']['feedback_edges']), 1)
        report = renderer.render(planned, self.out, stem='cycle', preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(len(report['errors']), 0)

    def test_horizontal_lr_layout_with_icons_and_labels(self):
        method = {
            'title': 'Horizontal Workflow',
            'canvas': {'width_pt': 400},
            'direction': 'horizontal',
            'nodes': [
                {'id': 'src', 'label': 'Data Source', 'vector_icon': 'database'},
                {'id': 'proc', 'label': 'Processing Unit', 'vector_icon': 'cpu'},
                {'id': 'out', 'label': 'Final Storage', 'vector_icon': 'cloud'}
            ],
            'edges': [
                {'from': 'src', 'to': 'proc', 'label': 'Stream'},
                {'from': 'proc', 'to': 'out', 'label': 'Upload'}
            ]
        }
        planned = plan_diagram.plan(method)
        self.assertEqual(planned['layout_plan']['reading_direction'], 'horizontal')
        report = renderer.render(planned, self.out, stem='horizontal-pipe', preview_only=True)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(len(report['errors']), 0)


class FetchPapersTests(unittest.TestCase):
    def test_normalize_doi_and_title(self):
        self.assertEqual(fetch_papers.normalize_doi('https://doi.org/10.1038/s41586-020-2649-2'), '10.1038/s41586-020-2649-2')
        self.assertEqual(fetch_papers.normalize_doi('  DOI: 10.1145/12345.67890 '), '10.1145/12345.67890')
        self.assertEqual(fetch_papers.normalize_doi(None), '')

        t1 = 'A Framework for Multi-Panel Diagram Generation!'
        t2 = 'a framework for multi panel diagram generation'
        self.assertEqual(fetch_papers.normalize_title(t1), fetch_papers.normalize_title(t2))

    @patch('urllib.request.urlopen')
    def test_fetch_openalex_offline_mock(self, mock_urlopen):
        mock_response = MagicMock()
        mock_data = {
            'results': [
                {
                    'id': 'https://openalex.org/W12345',
                    'doi': 'https://doi.org/10.1000/182',
                    'title': 'Single-Cell Analysis Methods',
                    'publication_year': 2023,
                    'cited_by_count': 42,
                    'authorships': [
                        {'author': {'display_name': 'Jane Doe'}},
                        {'author': {'display_name': 'John Smith'}}
                    ],
                    'primary_location': {
                        'source': {'display_name': 'Nature Methods'},
                        'is_oa': True,
                        'pdf_url': 'https://nature.com/example.pdf',
                        'landing_page_url': 'https://nature.com/example'
                    },
                    'open_access': {'is_oa': True, 'oa_status': 'gold', 'oa_url': 'https://nature.com/example.pdf'}
                }
            ]
        }
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        records = fetch_papers.fetch_openalex('single cell', limit=5)
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec['title'], 'Single-Cell Analysis Methods')
        self.assertEqual(rec['year'], '2023')
        self.assertEqual(rec['citations'], '42')
        self.assertEqual(rec['doi'], '10.1000/182')
        self.assertIn('Jane Doe', rec['authors'])
        self.assertEqual(rec['venue'], 'Nature Methods')
        self.assertEqual(rec['oa_status'], 'gold')

    @patch('urllib.request.urlopen')
    def test_fetch_arxiv_offline_mock(self, mock_urlopen):
        mock_response = MagicMock()
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/2301.00001v1</id>
            <title>Neural Flow: Scalable Deep Learning</title>
            <summary>We present a scalable architecture for deep learning workflows.</summary>
            <published>2023-01-01T00:00:00Z</published>
            <author><name>Alan Turing</name></author>
            <link title="pdf" href="http://arxiv.org/pdf/2301.00001v1" type="application/pdf"/>
          </entry>
        </feed>"""
        mock_response.read.return_value = mock_xml.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        records = fetch_papers.fetch_arxiv('neural flow', limit=5)
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec['title'], 'Neural Flow: Scalable Deep Learning')
        self.assertEqual(rec['year'], '2023')
        self.assertEqual(rec['doi'], '')
        self.assertIn('Alan Turing', rec['authors'])
        self.assertEqual(rec['oa_status'], 'green-preprint')

    def test_deduplicate_papers(self):
        p1 = {'doi': '10.1000/182', 'title': 'Exact Same Title', 'venue': 'Bioinformatics'}
        p2 = {'doi': '10.1000/182', 'title': 'Exact Same Title (arXiv)', 'venue': 'arXiv'}
        p3 = {'doi': '', 'title': 'Exact Same Title', 'venue': 'arXiv'}
        p4 = {'doi': '', 'title': 'Completely Unique Title', 'venue': 'Bioinformatics'}

        deduped = fetch_papers.deduplicate_papers([p1, p2, p3, p4])
        self.assertEqual(len(deduped), 2)
        titles = [p['title'] for p in deduped]
        self.assertIn('Exact Same Title', titles)
        self.assertIn('Completely Unique Title', titles)

    @patch('scripts.fetch_papers.fetch_openalex')
    @patch('scripts.fetch_papers.fetch_arxiv')
    def test_search_papers_and_matrix_csv_compatibility(self, mock_arxiv, mock_oa):
        mock_oa.return_value = [
            {
                'title': 'High-Throughput Deep Learning Screening',
                'authors': 'Alice Watson, Bob Ross',
                'year': '2022',
                'venue': 'Bioinformatics',
                'doi': '10.1093/bioinf/12345',
                'url': 'https://example.com/paper',
                'citations': '85',
                'citation_source': 'OpenAlex',
                'citation_checked_on': '2026-01-01',
                'relevance': '90.0',
                'figure_relevance': '85.0',
                'oa_status': 'gold',
                'pdf_url': 'https://example.com/paper.pdf',
                'downloaded_full_text': 'no',
                'figure_inspected': 'no',
                'figure_locator': '',
                'notes': ''
            }
        ]
        mock_arxiv.return_value = []

        results = fetch_papers.search_papers('deep learning', limit=5, oa_only=True)
        self.assertEqual(len(results), 1)

        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.csv') as tf:
            writer = csv.DictWriter(tf, fieldnames=fetch_papers.FIELDNAMES)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
            tf_path = Path(tf.name)

        try:
            records = score_papers.load_records(tf_path)
            self.assertEqual(len(records), 1)
            scored = score_papers.calculate_scores(records)
            self.assertEqual(len(scored), 1)
            self.assertIn('weighted_score', scored[0])
            self.assertGreater(scored[0]['weighted_score'], 0)
        finally:
            if tf_path.exists():
                tf_path.unlink()


class PaperFigureGroundingEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def draw(self, spec, **kwargs):
        return renderer.render(spec, self.out, stem='test-grounding', dpi=150, **kwargs)

    def test_require_paper_figures_rejects_missing_or_insufficient_figure_sources(self):
        spec = minimal_spec()
        # 1. Zero sources
        with self.assertRaises(ValueError) as cm:
            self.draw(spec, require_paper_figures=True)
        self.assertIn("Paper-grounded mode requires at least 2 inspected published figure sources", str(cm.exception))

        # 2. Only 1 figure source
        spec['sources'] = [
            {'id': 'fig1', 'kind': 'figure', 'title': 'Paper A Architecture', 'locator': 'Fig. 2, p. 4', 'doi': '10.1234/example1'}
        ]
        with self.assertRaises(ValueError) as cm:
            self.draw(spec, require_paper_figures=True)
        self.assertIn("Paper-grounded mode requires at least 2 inspected published figure sources", str(cm.exception))

        # 3. Two figure sources, but one lacks doi/url/pdf_url
        spec['sources'].append(
            {'id': 'fig2', 'kind': 'figure', 'title': 'Paper B Flowchart', 'locator': 'Fig. 3, p. 5'}
        )
        with self.assertRaises(ValueError) as cm:
            self.draw(spec, require_paper_figures=True)
        self.assertIn("Paper-grounded mode requires at least 2 inspected published figure sources", str(cm.exception))

    def test_require_paper_figures_accepts_two_verified_figures_and_reports_count(self):
        spec = minimal_spec()
        spec['sources'] = [
            {'id': 'fig1', 'kind': 'figure', 'title': 'Paper A Architecture', 'locator': 'Fig. 2, p. 4', 'doi': '10.1234/example1'},
            {'id': 'fig2', 'kind': 'figure', 'title': 'Paper B Flowchart', 'locator': 'Fig. 3, p. 5', 'url': 'https://arxiv.org/abs/2301.00000'}
        ]
        report = self.draw(spec, require_paper_figures=True, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        self.assertEqual(report['provenance']['paper_figures_inspected'], 2)
        self.assertEqual(report['provenance']['paper_figure_ids'], ['fig1', 'fig2'])

    def test_require_paper_figures_cli_check_only(self):
        import subprocess
        import sys
        spec_bad = minimal_spec()
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(spec_bad, f)
            p_bad = Path(f.name)
        try:
            res_bad = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'render_diagram.py'), str(p_bad), '--check-only', '--require-paper-figures'],
                capture_output=True, text=True
            )
            self.assertEqual(res_bad.returncode, 2)
            self.assertIn("Paper-grounded mode requires at least 2 inspected published figure sources", res_bad.stderr)
        finally:
            if p_bad.exists():
                p_bad.unlink()

        spec_good = minimal_spec()
        spec_good['sources'] = [
            {'id': 'fig1', 'kind': 'figure', 'title': 'Paper A Architecture', 'locator': 'Fig. 2, p. 4', 'doi': '10.1234/example1'},
            {'id': 'fig2', 'kind': 'figure', 'title': 'Paper B Flowchart', 'locator': 'Fig. 3, p. 5', 'url': 'https://arxiv.org/abs/2301.00000'}
        ]
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(spec_good, f)
            p_good = Path(f.name)
        try:
            res_good = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'render_diagram.py'), str(p_good), '--check-only', '--require-paper-figures'],
                capture_output=True, text=True
            )
            self.assertEqual(res_good.returncode, 0, res_good.stderr)
        finally:
            if p_good.exists():
                p_good.unlink()

    def test_borderless_legend_and_elongated_swatches(self):
        spec = minimal_spec()
        spec['legend'] = {
            'box': [20, 140, 260, 30],
            'items': [
                {'label': 'Category A', 'kind': 'node', 'color': '#0072B2'},
                {'label': 'Dashed path', 'kind': 'edge', 'style': 'dashed', 'color': '#334E68', 'arrow': 'end'}
            ]
        }
        # Default frame is False -> borderless
        res = self.draw(spec, drawio=True)
        self.assertTrue(res['passed_geometry_checks'], res['errors'])
        drawio_text = (self.out / 'test-grounding.drawio').read_text(encoding='utf-8')
        self.assertIn('fillColor=none;strokeColor=none;', drawio_text)

        # Test explicit frame=True
        spec['legend']['frame'] = True
        res_framed = self.draw(spec, drawio=True)
        self.assertTrue(res_framed['passed_geometry_checks'], res_framed['errors'])
        drawio_framed = (self.out / 'test-grounding.drawio').read_text(encoding='utf-8')
        self.assertNotIn('fillColor=none;strokeColor=none;', drawio_framed)


if __name__ == '__main__':
    unittest.main()
