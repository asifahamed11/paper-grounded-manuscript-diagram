import copy
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts import render_diagram as renderer
from scripts.score_papers import calculate_scores, reviewed_figures


ROOT = Path(__file__).resolve().parents[1]


def method():
    return {
        'title': 'Review',
        'canvas': {'width_pt': 264, 'height_pt': 170},
        'nodes': [
            {'id': 'a', 'label': 'Records', 'box': [40, 15, 180, 37]},
            {'id': 'b', 'label': 'Review', 'box': [40, 115, 180, 37]},
        ],
        'edges': [{'id': 'records-to-review', 'from': 'a', 'to': 'b', 'points': [[130, 52], [130, 115]]}],
    }


class ValidationTests(unittest.TestCase):
    def test_early_rejection_of_invalid_label_fields(self):
        for field, value in [('padding_pt','4'), ('detail_font_pt', None), ('align', []), ('fill', [])]:
            spec = method()
            spec['annotations'] = [{'label':'Review note', 'box':[20, 80, 200, 24], field:value}]
            with self.assertRaises(ValueError):
                renderer.validate_spec(spec)

    def test_source_ref_must_resolve(self):
        spec = method()
        spec['nodes'][0]['source_refs'] = ['source-not-present']
        with self.assertRaisesRegex(ValueError, 'source_refs'):
            renderer.validate_spec(spec)

    def test_invalid_connector_overrides_fail_validation(self):
        spec = method()
        spec['style'] = {'connector_width_pt': 0}
        with self.assertRaisesRegex(ValueError, 'connector_width_pt'):
            renderer.validate_spec(spec)
        spec['style']['connector_width_pt'] = 1.2
        spec['edges'][0]['color'] = 'not-a-palette-name'
        with self.assertRaisesRegex(ValueError, 'palette name'):
            renderer.validate_spec(spec)

    def test_reviewed_figures_prioritise_inspected_relevant_evidence(self):
        candidates = calculate_scores([
            {'title':'Cited', 'citations':4000, 'relevance':90, 'figure_relevance':95, 'year':2026},
            {'title':'Inspected', 'figure_inspected':True, 'figure_locator':'Fig. 2',
             'citations':1, 'relevance':80, 'figure_relevance':85, 'year':2023},
            {'title':'No locator', 'figure_inspected':'yes', 'figure_relevance':95},
            {'title':'Less close', 'figure_inspected':'yes', 'figure_locator':'Fig. 1',
             'figure_relevance':70, 'relevance':99, 'citations':2000},
        ], current_year=2026)
        self.assertEqual([item['title'] for item in reviewed_figures(candidates)], ['Inspected','Less close'])


try:
    import matplotlib
    from PIL import Image
    RENDER = True
except ImportError:
    RENDER = False


@unittest.skipUnless(RENDER, 'Optional render dependencies are unavailable')
class RendererReliabilityTests(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.out = Path(fixture.name)

    def render(self, spec, **kwargs):
        return renderer.render(spec, self.out, dpi=300, **kwargs)

    def test_transparent_group_checks_effective_background(self):
        spec = method()
        spec['nodes'].append({'id':'group', 'shape':'group', 'box':[12, 53, 95, 57],
                              'label':'Review group', 'fill':'blue', 'text_color':'white'})
        report = self.render(spec)
        self.assertFalse(report['passed_geometry_checks'])
        group = next(item for item in report['text'] if item['id']=='group')
        self.assertEqual(group['contrast'], 1)

    def test_no_port_flip_when_route_heads_inward(self):
        spec = method()
        spec['edges'][0]['points'] = [[220, 30], [75, 30], [75, 115]]
        report = self.render(spec)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('points inward' in error for error in report['errors']))
        self.assertEqual(report['resolved_ports'][0]['start'], [220,30])

    def test_crossing_flags_independent_routes_and_records_review_exception(self):
        spec = {'title':'Separate paths', 'canvas':{'width_pt':300,'height_pt':240},
                'nodes':[{'id':i, 'label':i.upper(), 'box':bounds} for i,bounds in [
                    ('a',[18,105,92,30]), ('b',[190,105,92,30]),
                    ('c',[104,18,92,34]), ('d',[104,188,92,34])]],
                'edges': [
                    {'id':'ab','from':'a','to':'b','points':[[110,120],[190,120]]},
                    {'id':'cd','from':'c','to':'d','points':[[150,52],[150,188]]},
                ]}
        report = self.render(spec)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertEqual(report['connector_crossings'][0]['point_pt'], [150,120])
        self.assertEqual(report['connector_crossings'][0]['kind'], 'crossing')
        spec['allowed_crossings'] = [{'edges': ['ab','cd'], 'reason': 'Two separate paths in the comparison'}]
        report = self.render(spec)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        self.assertEqual(report['connector_crossings'][0]['review_reason'], spec['allowed_crossings'][0]['reason'])

    def test_shared_join_is_not_reported_as_a_crossing(self):
        a = {'from':'a','to':'c'}
        b = {'from':'b','to':'c'}
        paths = [(a, [(1,0),(1,2),(4,2),(4,8)]), (b, [(7,0),(7,2),(4,2),(4,8)])]
        self.assertEqual(list(renderer.connector_crossings(paths)), [])

    def test_failed_revision_archives_previous_outputs_and_keeps_unrelated_file(self):
        initial = self.render(method())
        stamp = initial['spec_sha256']
        original = self.out/'figure-01.svg'
        (self.out/'notes.txt').write_text('Human notes', encoding='utf-8')
        bad = method()
        bad['nodes'][0]['label'] = 'LongUnbrokenTerm' * 20
        report = self.render(bad)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertFalse(original.exists())
        rev, = (self.out/'.history').iterdir()
        self.assertTrue((rev/original.name).is_file())
        self.assertEqual(json.loads((rev/'figure-01-qa.json').read_text())['spec_sha256'], stamp)
        self.assertEqual((self.out/'notes.txt').read_text(), 'Human notes')
        self.assertEqual(json.loads((self.out/'figure-01-qa.json').read_text())['exports'], [])

    def test_refuse_to_move_user_edited_export(self):
        self.render(method())
        edited = self.out/'figure-01-source.json'
        edited.write_text('User draft')
        with self.assertRaisesRegex(ValueError, 'edited'):
            self.render(method())
        self.assertEqual(edited.read_text(), 'User draft')

    def test_invalid_json_in_cli_has_a_current_failure_receipt(self):
        self.render(method())
        bad = self.out/'invalid.json'
        bad.write_text('{')
        run = subprocess.run([sys.executable, str(ROOT/'scripts/render_diagram.py'), str(bad),
                              '--output-dir', str(self.out)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertFalse((self.out/'figure-01.svg').exists())
        self.assertEqual(json.loads((self.out/'figure-01-qa.json').read_text())['status'], 'input-or-export-error')

    def test_tiff_and_native_diagram_have_expected_structure(self):
        report = self.render(method(), drawio=True, tiff=True)
        self.assertEqual(report['status'], 'complete')
        with Image.open(self.out/'figure-01.tiff') as image:
            self.assertEqual(image.mode, 'RGB')
            self.assertEqual(image.info['dpi'], (300.0, 300.0))
            self.assertEqual(image.info['compression'], 'tiff_lzw')
        root = ET.parse(self.out/'figure-01.drawio')
        cells = {cell.get('id'):cell for cell in root.findall('.//mxCell')}
        edge = cells['edge-0']
        self.assertEqual((edge.get('source'), edge.get('target')), ('node-0', 'node-1'))
        self.assertEqual(edge.find('mxGeometry').get('relative'),'1')
        self.assertIn('Records', cells['node-0'].get('value'))

    def test_connector_overrides_preserve_color_and_weight_in_exports(self):
        spec = method()
        spec['canvas']['height_pt'] = 230
        spec['style'] = {'line_width_pt': .75, 'connector_width_pt': 1.2, 'connector_color': 'blue'}
        spec['nodes'].append({'id': 'c', 'label': 'Summary', 'box': [40, 178, 180, 37]})
        spec['edges'][0]['color'] = 'vermillion'
        spec['edges'].append({'from': 'b', 'to': 'c', 'points': [[130, 152], [130, 178]]})
        report = self.render(spec, drawio=True)
        self.assertEqual(report['status'], 'complete', report.get('errors'))

        svg = ET.parse(self.out/'figure-01.svg')
        path_styles = [path.get('style', '') for path in svg.iter('{http://www.w3.org/2000/svg}path')]
        for stroke in ('#d55e00', '#0072b2'):
            self.assertTrue(any(f'stroke: {stroke};' in style and 'stroke-width: 1.2;' in style
                                for style in path_styles))
        with Image.open(self.out/'figure-01.png') as image:
            self.assertEqual(image.getpixel((542, 333))[:3], (213, 94, 0))
            self.assertEqual(image.getpixel((542, 687))[:3], (0, 114, 178))

        native = ET.parse(self.out/'figure-01.drawio')
        styles = {cell.get('id'): cell.get('style') for cell in native.iter('mxCell')}
        self.assertIn('strokeWidth=1.00000;', styles['node-0'])
        self.assertIn('strokeColor=#D55E00;strokeWidth=1.60000;', styles['edge-0'])
        self.assertIn('strokeColor=#0072B2;strokeWidth=1.60000;', styles['edge-1'])

    def test_checked_references_and_preview_mode(self):
        data = method()
        with self.assertRaisesRegex(ValueError, 'Missing source references'):
            self.render(data, require_sources=True)
        data['sources'] = [{'id':'method','title':'Illustrative method','locator':'Steps 1–2'}]
        for item in data['edges'] + data['nodes']:
            item['source_refs'] = ['method']
        report = self.render(data, require_sources=True, preview_only=True)
        self.assertEqual(report['status'], 'preview')
        self.assertFalse((self.out/'figure-01.pdf').exists())
        self.assertEqual(report['provenance']['unlinked_method_elements'], [])


class PdfExtractionTests(unittest.TestCase):
    def test_successful_vector_and_raster_extraction(self):
        try:
            import pymupdf
            from PIL import Image
        except ImportError:
            self.skipTest('Optional PDF and image dependencies are unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            for name in ('vector','raster'):
                with self.subTest(name=name):
                    pdf = destination/f'{name}.pdf'
                    with pymupdf.open() as document:
                        page = document.new_page()
                        if name == 'raster':
                            data = BytesIO()
                            Image.new('RGB', (16,16), 'blue').save(data, format='PNG')
                            page.insert_image((24,24,48,48), stream=data.getvalue())
                        else:
                            page.draw_rect((24,24,48,48))
                        document.save(pdf)
                    run = subprocess.run([sys.executable,str(ROOT/'scripts/extract_pdf_figures.py'),str(pdf),
                                          '--output-dir',tmp,'--end-page','1'],capture_output=True,text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertTrue((destination/f'{name}_page_001.png').is_file())
                    self.assertEqual(len(list(destination.glob(f'{name}_page_*_image_*'))), int(name=='raster'))
