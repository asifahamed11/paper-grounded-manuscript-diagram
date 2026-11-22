import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('layout_renderer',ROOT/'scripts/render_diagram.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)


def diagram():
    return {'title':'Layout diagnostic fixture', 'canvas':{'width_pt':300,'height_pt':220},
            'nodes':[{'id':'a','box':[20,20,120,60],'label':'Source records','detail':'Dates and definitions'},
                     {'id':'b','box':[20,160,120,40],'label':'Evaluation'}],
            'edges':[{'from':'a','to':'b','points':[[80,80],[80,160]]}]}


class MetricTests(unittest.TestCase):
    def test_rectangle_union_counts_overlap_once(self):
        self.assertEqual(R.rectangle_union_area([(0,0,10,10),(5,5,15,15)]),175)
        self.assertEqual(R.rectangle_union_area([]),0)

    def test_headers_and_containers_cannot_inflate_main_fill(self):
        data=diagram();before=R.layout_metrics(data)
        data['nodes'] += [{'id':'header','shape':'header','box':[0,0,300,12],'label':'Heading'},
                          {'id':'group','shape':'group','box':[5,15,280,200],'label':'Container'}]
        after=R.layout_metrics(data)
        for key in ['main_box_canvas_fraction','main_box_envelope_fraction','median_nearest_node_gap_pt']:
            self.assertEqual(before[key],after[key])

    def test_tighter_spacing_improves_occupancy_without_changing_boxes(self):
        data=diagram();before=R.layout_metrics(data)
        data['nodes'][1]['box'][1]=94
        data['edges'][0]['points'][-1]=[80,94]
        after=R.layout_metrics(data)
        self.assertGreater(after['main_box_envelope_fraction'],before['main_box_envelope_fraction'])
        self.assertEqual(after['main_box_canvas_fraction'],before['main_box_canvas_fraction'])
        self.assertLess(after['median_nearest_node_gap_pt'],before['median_nearest_node_gap_pt'])

    def test_loop_bounds_and_close_pairs_are_reported(self):
        data=diagram();data['nodes'][1]['box'][1]=84
        data['edges'][0]['points']=[[20,50],[8,50],[8,104],[20,104]]
        report=R.layout_metrics(data)
        self.assertEqual(report['outside_margins_pt']['left'],8)
        self.assertEqual(report['crowded_pairs'][0]['gap_pt'],4)

    def test_layout_only_works_without_optional_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.json';path.write_text(json.dumps(diagram()))
            result=subprocess.run([sys.executable,'-S',str(ROOT/'scripts/render_diagram.py'),str(path),'--layout-only'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report['node_content'],[])
            self.assertIn('not ink coverage',report['definition'])

    def test_invalid_text_gap_or_layout_rejected(self):
        for gap in [-1,True,float('nan')]:
            data=diagram();data['style']={'title_detail_gap_pt':gap}
            with self.assertRaises(ValueError):R.validate_spec(data)
        data=diagram();data['nodes'][0]['text_layout']='unknown'
        with self.assertRaises(ValueError):R.validate_spec(data)


try:
    import matplotlib
    HAS_MPL=True
except ImportError:HAS_MPL=False


@unittest.skipUnless(HAS_MPL,'Optional Matplotlib is not installed')
class TextStackTests(unittest.TestCase):
    def draw(self,data):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name);return R.render(data,self.out,dpi=150)

    def test_tall_node_keeps_compact_title_detail_gap(self):
        data=diagram();original=copy.deepcopy(data)
        report=self.draw(data)
        self.assertTrue(report['passed_geometry_checks'],report['errors'])
        title,detail=report['text'][:2]
        self.assertAlmostEqual(detail['bounds_pt'][1]-title['bounds_pt'][3],3.5,places=2)
        self.assertEqual(data,original)  # No silent graph/canvas rewrite.
        self.assertTrue(all(t['font_pt']>=8.5 for t in report['text']))

    def test_legacy_band_override_remains_and_stacked_can_override_it(self):
        data=diagram();data['nodes'][0]['title_height_pt']=20
        legacy=self.draw(data)
        gap=legacy['text'][1]['bounds_pt'][1]-legacy['text'][0]['bounds_pt'][3]
        data['nodes'][0]['text_layout']='stacked'
        compact=self.draw(data)
        compact_gap=compact['text'][1]['bounds_pt'][1]-compact['text'][0]['bounds_pt'][3]
        self.assertGreater(gap,compact_gap)
        self.assertAlmostEqual(compact_gap,3.5,places=2)

    def test_combined_stack_overflow_does_not_export_success(self):
        data=diagram();data['nodes'][0].update(box=[20,20,120,42],label='Line 1\nLine 2\nLine 3',detail='Line 4\nLine 5\nLine 6')
        data['edges'][0]['points'][0]=[80,62]
        report=self.draw(data)
        self.assertFalse(report['passed_geometry_checks'])
        self.assertTrue(any('Combined title/detail' in e for e in report['errors']))
        self.assertEqual(report['exports'],[])

    def test_density_advisory_does_not_fail_valid_geometry(self):
        report=self.draw(diagram())
        self.assertTrue(report['passed_geometry_checks'])
        self.assertTrue(any('nearest-node gap' in a for a in report['layout']['advisories']))
        self.assertEqual(len(report['layout']['node_content']),2)

    def test_readable_decision_is_not_called_oversized_for_its_semantic_wings(self):
        data={'title':'Decision fixture','canvas':{'width_pt':140,'height_pt':90},
              'nodes':[{'id':'choice','shape':'decision','box':[15,10,110,64],'label':'Eligible?','bold':True}]}
        report=self.draw(data)
        self.assertTrue(report['passed_geometry_checks'],report['errors'])
        self.assertLess(report['layout']['node_content'][0]['content_envelope_fraction'],.12)
        self.assertFalse(any('oversized' in a for a in report['layout']['advisories']))


if __name__=='__main__':unittest.main()
