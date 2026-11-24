import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.plan_diagram import graph_rows, plan
from scripts.render_diagram import render


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT/'templates'/'review-selection-method.json'


class GraphTests(unittest.TestCase):
    def test_preserves_order_and_rejects_cycle(self):
        nodes = dict.fromkeys(['a','b','c','d'])
        edges = [{'from':'a','to':'b'},{'from':'a','to':'c'},{'from':'c','to':'d'},{'from':'b','to':'d'}]
        rows, rank, _, _ = graph_rows(nodes, edges)
        self.assertEqual(rows, [['a'], ['b','c'], ['d']])
        with self.assertRaisesRegex(ValueError, 'acyclic'):
            graph_rows(nodes, edges + [{'from':'d','to':'a'}])


try:
    import matplotlib
    from PIL import Image
    RENDER = True
except ImportError:
    RENDER = False


@unittest.skipUnless(RENDER, 'Optional render dependencies are unavailable')
class PlannerTests(unittest.TestCase):
    def test_public_example_preserves_method_and_emits_readable_branches(self):
        original = json.loads(EXAMPLE.read_text(encoding='utf-8'))
        untouched = copy.deepcopy(original)
        made = plan(original, EXAMPLE.parent)
        self.assertEqual(original, untouched)
        self.assertEqual([(e['from'], e['to'], e['source_refs']) for e in made['edges']],
                         [(e['from'], e['to'], e['source_refs']) for e in original['edges']])
        self.assertEqual(set(x['label'] for x in made['annotations']), {'Yes','No'})
        self.assertEqual(made['canvas']['width_pt'], original['canvas']['width_pt'])
        with tempfile.TemporaryDirectory() as folder:
            report = render(made, folder, dpi=150, require_sources=True, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        self.assertEqual(report['connector_crossings'], [])

    def test_parallel_branches_rejoin_at_shared_evaluation(self):
        source = {
            'title': 'Algorithm comparison', 'canvas': {'width_pt': 410},
            'nodes': [{'id':identifier,'label':label,'detail':detail} for identifier,label,detail in [
                ('source','Benchmark sources','Curated records'),
                ('first','First method','Evaluate the same inputs'),
                ('second','Second method','Evaluate the same inputs'),
                ('shared','Shared evaluation','Compare common measures'),
            ]],
            'edges': [{'from':a,'to':b} for a,b in [
                ('source','first'), ('source','second'), ('first','shared'), ('second','shared')]],
        }
        made = plan(source)
        self.assertEqual(made['layout_plan']['reading_direction'], 'horizontal')
        with tempfile.TemporaryDirectory() as folder:
            report = render(made,folder,dpi=150,preview_only=True)
        self.assertTrue(report['passed_geometry_checks'],report['errors'])

    def test_icon_comparison_uses_rendered_option_and_preserves_detail(self):
        root = ROOT/'templates'/'icon-workflow'
        method = {
            'title':'Records',
            'canvas':{'width_pt':250},
            'nodes':[{'id':'start','label':'Records','detail':'Obtain verified source extracts'}],
            'icons':[{'id':'doc','node':'start','path':'assets/records.png','alt':'Source records'}],
        }
        spec = plan(method, root)
        with tempfile.TemporaryDirectory() as folder:
            report = render(spec, folder, dpi=150, asset_dir=root, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        self.assertEqual(report['icons'][0]['placement'], report['layout_plan']['icon_choices'][0]['choice'])
        candidates = report['layout_plan']['icon_choices'][0]['candidates']
        self.assertEqual({item['placement'] for item in candidates}, {'title','left','top'})
        detail = next(item for item in report['text'] if item['id']=='start:detail')
        self.assertEqual(' '.join(detail['text'].split()), method['nodes'][0]['detail'])

    def test_planner_early_rejects_empty_whitespace_detail(self):
        method = {
            'title': 'Test',
            'canvas': {'width_pt': 250},
            'nodes': [{'id': 'a', 'label': 'A', 'detail': '   '}],
        }
        with self.assertRaisesRegex(ValueError, 'detail must be text'):
            plan(method)

    def test_planner_removes_label_when_creating_branch_note(self):
        method = {
            'title': 'Branch Test',
            'canvas': {'width_pt': 250},
            'nodes': [{'id': 'a', 'label': 'Start'}, {'id': 'b', 'label': 'End'}],
            'edges': [{'from': 'a', 'to': 'b', 'label': 'Condition'}],
        }
        spec = plan(method)
        self.assertNotIn('label', spec['edges'][0])
        self.assertEqual(len(spec.get('annotations', [])), 1)
        self.assertEqual(spec['annotations'][0]['label'], 'Condition')
        with tempfile.TemporaryDirectory() as folder:
            report = render(spec, folder, dpi=150, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])

    def test_planner_horizontal_clamping_avoids_vertical_segments(self):
        method = {
            'title': 'Clamp Test',
            'canvas': {'width_pt': 250},
            'nodes': [{'id': 'a', 'label': 'Node A'}, {'id': 'b', 'label': 'Node B'}],
            'edges': [{'from': 'a', 'to': 'b', 'label': 'Option A (Approved)'}],
        }
        spec = plan(method)
        note = spec['annotations'][0]
        nx, ny, nw, nh = note['box']
        edge = spec['edges'][0]
        sx = edge['points'][0][0]
        self.assertTrue(nx + nw <= sx or nx >= sx, f'Note [{nx}, {nx+nw}] overlaps vertical connector sx={sx}')
