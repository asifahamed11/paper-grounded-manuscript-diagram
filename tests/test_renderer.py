import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

R=load('render_diagram')
def minimal():
    return {'title':'Test method','canvas':{'width_pt':252,'height_pt':160},
            'nodes':[{'id':'a','box':[20,10,210,42],'label':'Audited input'},
                     {'id':'b','box':[20,100,210,42],'label':'Evaluation'}],
            'edges':[{'from':'a','to':'b','points':[[125,52],[125,100]]}]}

class SpecTests(unittest.TestCase):
    def test_check_only_with_standard_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'in.json';p.write_text(json.dumps(minimal()))
            process=subprocess.run([sys.executable,'-S',str(ROOT/'scripts/render_diagram.py'),str(p),'--check-only'],capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr)

    def test_missing_id_and_duplicate_id(self):
        for transform in [lambda s:s['nodes'][0].pop('id'),lambda s:s['nodes'][1].update(id='a')]:
            spec=minimal();transform(spec)
            with self.assertRaises(ValueError):R.validate_spec(spec)

    def test_nonfinite_and_out_of_canvas(self):
        for value in [float('nan'),float('inf'),-1,300]:
            spec=minimal();spec['nodes'][0]['box'][0]=value
            with self.assertRaises(ValueError):R.validate_spec(spec)

    def test_unknown_endpoint_diagonal_and_unexplained_dashes(self):
        mutations=[{'to':'missing'},{'points':[[125,52],[140,100]]},{'style':'dashed'}]
        for change in mutations:
            spec=minimal();spec['edges'][0].update(change)
            with self.assertRaises(ValueError):R.validate_spec(spec)

    def test_rounded_routes_preserve_endpoints_and_limit_radius(self):
        commands,samples=R.rounded_route([[0,0],[10,0],[10,20]],100)
        self.assertEqual(samples[0],(0,0));self.assertEqual(samples[-1],(10,20))
        self.assertIn('Q',[c for c,p in commands])
        self.assertTrue(all(0<=x<=10 and 0<=y<=20 for x,y in samples))

    def test_bad_visual_style_is_rejected(self):
        for style in [{'connector_style':'unknown'},{'connector_radius_pt':-1},{'line_width_pt':0}]:
            spec=minimal();spec['style']=style
            with self.assertRaises(ValueError):R.validate_spec(spec)

try:
    import matplotlib
    HAS_MPL=True
except ImportError:HAS_MPL=False

@unittest.skipUnless(HAS_MPL,'Optional Matplotlib is not installed')
class RenderTests(unittest.TestCase):
    def draw(self,spec):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name);return R.render(spec,self.out,dpi=150)

    def test_real_exports_and_no_false_review_claim(self):
        report=self.draw(minimal());self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['visual_review'],'pending human inspection')
        self.assertIn('not performed',report['scientific_review'])
        svg=self.out/'figure-01.svg';root=ET.parse(svg).getroot()
        self.assertGreater(len(list(root.iter('{http://www.w3.org/2000/svg}text'))),0)
        self.assertEqual(root.attrib['aria-labelledby'],'diagram-title diagram-description')
        self.assertTrue(load('validate_svg').validate(svg)['passed_basic_structural_checks'])
        self.assertIn('sans-serif',svg.read_text(encoding='utf-8'))
        outlined=ET.parse(self.out/'figure-01-outlined.svg').getroot()
        self.assertEqual(len(list(outlined.iter('{http://www.w3.org/2000/svg}text'))),0)
        self.assertFalse(report['outlined_svg_label_text_editable'])
        from PIL import Image
        with Image.open(self.out/'figure-01.png') as image:
            self.assertEqual(image.size,(525,333))
        self.assertTrue((self.out/'figure-01.pdf').read_bytes().startswith(b'%PDF'))

    def test_long_text_fails_without_fake_final_exports(self):
        spec=minimal();spec['nodes'][0]['label']='UnbreakableIdentifier'*30
        report=self.draw(spec);self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('overflows' in e for e in report['errors']))
        self.assertEqual(report['exports'],[]);self.assertFalse((self.out/'figure-01.svg').exists())
        self.assertTrue((self.out/'figure-01-diagnostic.png').exists())

    def test_overlap_and_wrong_edge_anchor(self):
        spec=minimal();spec['nodes'][1]['box']=[30,20,210,42]
        report=self.draw(spec)
        self.assertTrue(any('Nodes overlap' in e for e in report['errors']))
        self.assertTrue(any('boundaries' in e for e in report['errors']))

    def test_unrelated_node_obstacle(self):
        spec=minimal();spec['nodes'].append({'id':'obstacle','box':[100,62,50,28],'label':'X'})
        report=self.draw(spec)
        self.assertTrue(any('crosses unrelated node' in e for e in report['errors']))

    def test_contrast_and_minimum_font(self):
        for change in [{'text_color':'yellow'},{'font_pt':7}]:
            spec=minimal();spec['nodes'][0].update(change);report=self.draw(spec)
            self.assertFalse(report['passed_geometry_checks'])

    def test_title_and_detail_remain_separate_editable_labels(self):
        spec=minimal();spec['nodes'][0].update(detail='Exact source dates',title_height_pt=18)
        report=self.draw(spec);self.assertTrue(report['passed_geometry_checks'],report['errors'])
        self.assertEqual([x['id'] for x in report['text']][:2],['a:title','a:detail'])

    def test_cylinder_heading_clears_the_top_cap(self):
        spec=minimal();spec['nodes'][0].update(shape='data',detail='Dated observations',box=[20,10,210,50])
        spec['edges'][0]['points'][0]=[125,60]
        report=self.draw(spec);self.assertTrue(report['passed_geometry_checks'],report['errors'])
        title=next(t for t in report['text'] if t['id']=='a:title')
        self.assertGreaterEqual(title['bounds_pt'][1],18)

    def test_missing_glyphs_are_not_a_success(self):
        spec=minimal();spec['nodes'][0]['label']='Unsupported '+chr(0x10ffff)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');report=self.draw(spec)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('missing glyphs' in e for e in report['errors']))

    def test_literal_dollar_labels_are_preserved(self):
        spec=minimal();spec['nodes'][0]['label']='Cost $100 and $200'
        report=self.draw(spec);self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['text'][0]['text'],'Cost $100 and $200')

    def test_bundled_templates_really_render(self):
        for name in ['linear-workflow.json','parallel-study.json','decision-workflow.json','conceptual-framework.json']:
            with self.subTest(name=name):
                report=self.draw(json.loads((ROOT/'templates'/name).read_text(encoding='utf-8')))
                self.assertTrue(report['passed_geometry_checks'],report['errors'])

    def test_all_polygon_shapes_and_elbows_are_rounded_by_default(self):
        spec=json.loads((ROOT/'templates/decision-workflow.json').read_text(encoding='utf-8'))
        report=self.draw(spec);self.assertTrue(report['passed_geometry_checks'],report['errors'])
        root=ET.parse(self.out/'figure-01.svg').getroot()
        paths=[e.get('d','') for e in root.iter('{http://www.w3.org/2000/svg}path')]
        self.assertGreaterEqual(sum('Q' in p for p in paths),5)
        self.assertEqual(report['style']['connector_radius_pt'],5)

    def test_curve_corner_obstacle_checks_follow_actual_route(self):
        commands,samples=R.rounded_route([[0,0],[10,0],[10,10]],5)
        obstacle=(8.5,1,9,1.5)
        self.assertTrue(any(R.segment_hits(a,b,obstacle) for a,b in zip(samples,samples[1:])))
        self.assertFalse(R.segment_hits((0,0),(10,0),obstacle))

    def test_explicit_square_connector_override_remains_available(self):
        spec=minimal();spec['style']={'connector_style':'orthogonal','corner_radius_pt':0}
        report=self.draw(spec);self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['style']['connector_radius_pt'],0)

    def test_connectors_touch_sloped_input_outline(self):
        spec=json.loads((ROOT/'templates/conceptual-framework.json').read_text(encoding='utf-8'))
        report=self.draw(spec);self.assertTrue(report['passed_geometry_checks'],report['errors'])
        port=report['resolved_ports'][0]['start']
        x,y,w,h=next(n['box'] for n in spec['nodes'] if n['id']=='exposure')
        self.assertAlmostEqual(port[0],x+w-3.5,places=3)
        self.assertAlmostEqual(port[1],y+h/2,places=3)

    def test_edge_label_rendering_and_drawio_export(self):
        spec = minimal()
        spec['edges'][0]['label'] = 'Proceed'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = R.render(spec, out, dpi=150, drawio=True)
            self.assertTrue(report['passed_geometry_checks'], report['errors'])
            edge_label_records = [t for t in report['text'] if t['id'] == 'edge:0:label']
            self.assertEqual(len(edge_label_records), 1)
            self.assertEqual(edge_label_records[0]['text'], 'Proceed')
            drawio_path = out / 'figure-01.drawio'
            self.assertTrue(drawio_path.exists())
            root = ET.parse(drawio_path).getroot()
            edge_cells = [c for c in root.iter('mxCell') if c.get('id') == 'edge-0']
            self.assertEqual(len(edge_cells), 1)
            self.assertIn('Proceed', edge_cells[0].get('value', ''))

    def test_collision_annotation_overlaps_node_and_group_title(self):
        spec = minimal()
        spec['annotations'] = [{'label': 'Overlapping Note', 'box': [30, 20, 100, 20]}]
        report = self.draw(spec)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('Annotation annotation-0 overlaps node a' in e for e in report['errors']))

        spec2 = minimal()
        spec2['nodes'].append({'id': 'grp', 'label': 'Group Header', 'shape': 'group', 'box': [10, 5, 230, 140], 'title_height_pt': 25})
        spec2['nodes'][0]['box'] = [20, 8, 100, 20]
        report2 = self.draw(spec2)
        self.assertFalse(report2['passed_geometry_checks'])
        self.assertTrue(any('Group label grp overlaps child node a' in e for e in report2['errors']))

    def test_obstacle_diamond_empty_corner_does_not_false_fail(self):
        spec = {
            'title': 'Diamond Test',
            'canvas': {'width_pt': 300, 'height_pt': 200},
            'nodes': [
                {'id': 'src', 'box': [10, 10, 40, 30], 'label': 'Src'},
                {'id': 'dst', 'box': [240, 10, 40, 30], 'label': 'Dst'},
                {'id': 'dec', 'shape': 'decision', 'box': [100, 50, 80, 80], 'label': 'Decision'},
            ],
            'edges': [
                {'from': 'src', 'to': 'dst', 'points': [[30, 40], [30, 55], [115, 55], [115, 25], [240, 25]]}
            ]
        }
        report = self.draw(spec)
        self.assertFalse(any('crosses unrelated node dec' in e for e in report['errors']))

    def test_silent_font_shrink_warning(self):
        spec = minimal()
        spec['nodes'][0]['box'] = [20, 10, 110, 30]
        spec['nodes'][0]['font_pt'] = 12
        spec['nodes'][0]['label'] = 'Medium Length Title Box'
        report = self.draw(spec)
        self.assertTrue(any('font shrunk from 12 pt to' in w for w in report['warnings']))

    def test_opt_in_math_rendering(self):
        spec = minimal()
        spec['nodes'][0]['label'] = r'Value \( \alpha + \beta \)'
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        text_entry = next(t for t in report['text'] if t['id'] == 'a')
        self.assertIn(r'\alpha', text_entry['text'])

        spec2 = minimal()
        spec2['nodes'][0]['label'] = r'\sum_{i=1}^n x_i'
        spec2['nodes'][0]['math'] = True
        report2 = self.draw(spec2)
        self.assertTrue(report2['passed_geometry_checks'], report2['errors'])

        spec3 = minimal()
        spec3['nodes'][0]['label'] = 'Budget $100 and $200'
        report3 = self.draw(spec3)
        self.assertTrue(report3['passed_geometry_checks'], report3['errors'])
        self.assertEqual(report3['text'][0]['text'], 'Budget $100 and $200')

    def test_journal_profiles_and_eps_export(self):
        spec = minimal()
        spec['canvas']['width_pt'] = 240
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = R.render(spec, out, dpi=300, profile='ieee-single', eps=True)
            self.assertTrue(report['passed_geometry_checks'], report['errors'])
            self.assertIn('figure-01.eps', report['exports'])
            self.assertTrue((out / 'figure-01.eps').exists())
            self.assertIn('figure-01.eps', R.artifact_names('figure-01'))

            spec_over = minimal()
            spec_over['canvas']['width_pt'] = 300
            report_over = R.render(spec_over, out, dpi=300, profile='ieee-single')
            self.assertFalse(report_over['passed_geometry_checks'])
            self.assertTrue(any('ieee-single profile expects width at most 252.00 pt' in e for e in report_over['errors']))

            report_springer = R.render(spec, out, dpi=300, profile='springer-lncs')
            self.assertTrue(report_springer['passed_geometry_checks'], report_springer['errors'])

    def test_math_bug_regression_plain_text_not_wrapped(self):
        # Regression test: verify that when canvas.math: true or node.math: true is set,
        # plain English labels like "Multi-Source Corpus" and "Raw text & metadata"
        # have parse_math=False (are not wrapped in $...$), while inline \( ... \) and
        # pure LaTeX commands like r'\sum_{i=1}^n x_i' render math cleanly.
        spec = minimal()
        spec['canvas']['math'] = True
        spec['canvas']['height_pt'] = 200
        spec['nodes'][0]['label'] = 'Multi-Source Corpus'
        spec['nodes'][0]['detail'] = 'Raw text & metadata'
        spec['nodes'][0]['math'] = True

        spec['nodes'][1]['box'] = [20, 90, 210, 60]
        spec['nodes'][1]['label'] = r'Dense embeddings \( \mathbf{h} \in \mathbb{R}^d \)'
        spec['nodes'][1]['detail'] = r'\sum_{i=1}^n x_i'
        spec['nodes'][1]['math'] = True
        spec['edges'][0]['points'] = [[125, 52], [125, 90]]
        spec['edges'][0]['label'] = 'Yes'

        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])

        # Verify _resolve_math behavior directly
        text_a, math_a = R._resolve_math('Multi-Source Corpus', record_or_math={'math': True}, canvas_math=True)
        self.assertEqual(text_a, 'Multi-Source Corpus')
        self.assertFalse(math_a)

        text_detail, math_detail = R._resolve_math('Raw text & metadata', record_or_math={'math': True}, canvas_math=True)
        self.assertEqual(text_detail, 'Raw text & metadata')
        self.assertFalse(math_detail)

        text_b, math_b = R._resolve_math(r'Dense embeddings \( \mathbf{h} \in \mathbb{R}^d \)', record_or_math={'math': True}, canvas_math=True)
        self.assertTrue(math_b)
        self.assertIn(r'$\mathbf{h} \in \mathbb{R}^d$', text_b)
        self.assertTrue(text_b.startswith('Dense embeddings '))

        text_sum, math_sum = R._resolve_math(r'\sum_{i=1}^n x_i', record_or_math={'math': True}, canvas_math=True)
        self.assertTrue(math_sum)
        self.assertEqual(text_sum, r'$\sum_{i=1}^n x_i$')

    def test_unambiguous_math_and_punctuated_formula_wrapping(self):
        # 1. Verify smart auto-detection for unambiguous LaTeX in $...$
        text_math = "Tokenize text; BM25 score ($k_1=1.2, b=0.75$)"
        resolved_math, is_math = R._resolve_math(text_math)
        self.assertTrue(is_math)
        self.assertEqual(resolved_math, text_math)

        # 2. Verify literal currency strings remain untouched
        text_currency = "Cost $100 and $200"
        resolved_curr, is_curr = R._resolve_math(text_currency)
        self.assertFalse(is_curr)
        self.assertEqual(resolved_curr, text_currency)

        text_budget = "Budget $100 and $200"
        resolved_bgt, is_bgt = R._resolve_math(text_budget)
        self.assertFalse(is_bgt)
        self.assertEqual(resolved_bgt, text_budget)

        # 3. Verify wrap_label does not break punctuated math spans across lines
        wrapped = R.wrap_label(text_math, 120, lambda s: len(s) * 6, math=is_math)
        lines = wrapped.split('\n')
        self.assertTrue(any("($k_1=1.2, b=0.75$)" in line for line in lines))
        for line in lines:
            self.assertFalse(line.startswith("b=0.75"))

        # 4. End-to-end rendering test with minimal()
        spec = minimal()
        spec['nodes'][0]['box'] = [20, 10, 210, 48]
        spec['nodes'][0]['label'] = "Preprocessing"
        spec['nodes'][0]['detail'] = text_math
        spec['edges'][0]['points'] = [[125, 58], [125, 100]]
        # canvas.math and node.math are both False by default in minimal()
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        text_node = next(t for t in report['text'] if t['id'] == 'a:detail')
        self.assertTrue(any("($k_1=1.2, b=0.75$)" in line for line in text_node['text'].split('\n')))

if __name__=='__main__':unittest.main()
