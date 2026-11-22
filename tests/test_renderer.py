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

if __name__=='__main__':unittest.main()
