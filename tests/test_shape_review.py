import base64
from importlib.util import find_spec
import json
from math import hypot
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import unquote
from xml.etree import ElementTree as ET
import zlib

from scripts import plan_diagram, render_diagram
from scripts.node_shapes import SHAPES


ROOT = Path(__file__).resolve().parents[1]
HAS_RENDER = find_spec('matplotlib') is not None and find_spec('PIL') is not None


def template(name):
    return json.loads((ROOT / 'templates' / f'{name}.json').read_text(encoding='utf-8'))


def decode_stencil(cell):
    encoded = re.search(r'shape=stencil\(([^)]+)\);', cell.get('style'))[1]
    xml = unquote(zlib.decompress(base64.b64decode(encoded), -zlib.MAX_WBITS).decode('ascii'))
    return ET.fromstring(xml)


class ShapeReviewTests(unittest.TestCase):
    def test_commands_list_roles_without_render_packages(self):
        for script, count in [('render_diagram', 14), ('plan_diagram', 12)]:
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, '-S', str(ROOT / 'scripts' / f'{script}.py'), '--list-shapes'],
                    capture_output=True, text=True, check=True, cwd=ROOT,
                )
                names = {line.partition(':')[0] for line in result.stdout.splitlines()}
                self.assertEqual(len(names), count)
                self.assertTrue(set(SHAPES).issubset(names))
                self.assertIn('process', names)

    def test_five_actual_papers_have_inventories_and_mapped_choices(self):
        spec = template('multiscale-architecture')
        report = render_diagram.provenance(spec)
        render_diagram.enforce_review(report, require_sources=True, require_paper_figures=True,
                                     require_shape_review=True)
        review = report['design_review']
        self.assertEqual(review['reported_published_papers'], 5)
        self.assertEqual(review['shape_review']['inventoried_figures'], 5)
        self.assertGreater(review['shape_review']['shape_observations'], 20)
        self.assertEqual(review['shape_review']['mapped_nodes'], 17)
        self.assertEqual(review['shape_review']['nodes_using_paper_conventions'], 15)

    def test_strict_review_requires_each_inspected_figure_inventory(self):
        spec = template('multiscale-architecture')
        row = spec['design_review']['precedents'][0]
        row.pop('shapes')
        for choice in spec['design_review']['shape_choices']:
            choice['from_shapes'] = [ref for ref in choice['from_shapes'] if ref['source'] != row['source']]
        report = render_diagram.provenance(spec)
        with self.assertRaisesRegex(ValueError, 'inventory for each reviewed figure: changeformer'):
            render_diagram.enforce_review(report, require_shape_review=True)

    def test_strict_review_requires_a_reason_for_each_actual_shape(self):
        spec = template('scientific-shapes')
        spec['design_review']['shape_choices'].pop()
        report = render_diagram.provenance(spec)
        with self.assertRaisesRegex(ValueError, 'shape choice for each method node: state'):
            render_diagram.enforce_review(report, require_shape_review=True)

    def test_shape_choices_check_the_observation_id_and_rendered_shape(self):
        spec = template('multiscale-architecture')
        choice = spec['design_review']['shape_choices'][2]
        choice['from_shapes'][0]['shape'] = 'made-up'
        with self.assertRaisesRegex(ValueError, 'unrecorded observation'):
            render_diagram.provenance(spec)
        choice['from_shapes'].pop(0)
        choice['shape'] = 'process'
        with self.assertRaisesRegex(ValueError, 'must match its rendered shape: tensor'):
            render_diagram.provenance(spec)

    def test_an_empty_inventory_requires_a_note_and_allows_a_local_choice(self):
        spec = template('multiscale-architecture')
        row = spec['design_review']['precedents'][0]
        row['shapes'] = []
        with self.assertRaisesRegex(ValueError, 'empty-inventory note'):
            render_diagram.provenance(spec)
        row['shape_inventory_note'] = 'Hypothetical source represented by annotated edges.'
        for choice in spec['design_review']['shape_choices']:
            choice['from_shapes'] = [ref for ref in choice['from_shapes'] if ref['source'] != row['source']]
        render_diagram.enforce_review(render_diagram.provenance(spec), require_shape_review=True)


@unittest.skipUnless(HAS_RENDER, 'Local rendering dependencies unavailable')
class ScientificShapeRenderTests(unittest.TestCase):
    def test_all_seven_render_as_editable_native_shapes_and_native_legend_swatches(self):
        spec = template('scientific-shapes')
        spec['canvas']['height_pt'] = 272
        spec['legend'] = {
            'box': [8, 246, 441, 18],
            'items': [
                {'shape': 'tensor', 'label': 'Feature pair', 'color': '#E8F3FB', 'stroke_color': '#0072B2'},
                {'shape': 'event', 'label': 'Review trigger', 'color': '#E5F3EF', 'stroke_color': '#009E73'},
            ],
        }
        with TemporaryDirectory() as output:
            report = render_diagram.render(spec, output, 'shapes', drawio=True, profile='ieee-double',
                                           require_sources=True, require_shape_review=True)
            self.assertTrue(report['passed_geometry_checks'], report['errors'])
            self.assertTrue(set(SHAPES) <= report['node_shape_counts'].keys())
            root = ET.parse(Path(output) / 'shapes.drawio').getroot()
        cells = {cell.get('id'): cell for cell in root.iter('mxCell')}
        for index, node in enumerate(spec['nodes']):
            shape = node['shape']
            if shape not in SHAPES:
                continue
            cell_id = f'node-{index}'
            stencil = decode_stencil(cells[cell_id])
            self.assertEqual(stencil.get('name'), shape)
            self.assertIsNotNone(stencil.find('background'))
            text_cell = cells[f'{cell_id}-text-0']
            self.assertEqual(text_cell.get('parent'), cell_id)
            self.assertIn('font-weight:bold', text_cell.get('value'))
        for i, shape in enumerate(('tensor', 'event')):
            self.assertEqual(decode_stencil(cells[f'legend-swatch-{i}']).get('name'), shape)
        for cell in cells.values():
            if cell.get('id', '').startswith('edge-'):
                self.assertIn('exitPerimeter=0;', cell.get('style'))
                self.assertIn(cell.get('source'), cells)
                self.assertIn(cell.get('target'), cells)

    def test_the_planner_sizes_new_shapes_in_two_lanes(self):
        method = template('scientific-shapes')
        method['nodes'] = [node for node in method['nodes'] if node['shape'] != 'group']
        method.pop('annotations')
        method['design_review']['checks'][2]['elements'].remove('nodes:review-boundary')
        method.update(direction='vertical', lanes=['comparison-lane', 'review-lane'])
        for index, node in enumerate(method['nodes']):
            node.pop('box')
            node['lane'] = method['lanes'][index // 4]
        for edge in method['edges']:
            edge.pop('points')
        spec = plan_diagram.plan(method)
        operator = next(node for node in spec['nodes'] if node['shape'] == 'operator')
        self.assertEqual(operator['box'][2], operator['box'][3])
        with TemporaryDirectory() as output:
            report = render_diagram.render(spec, output, preview_only=True,
                                           require_sources=True, require_shape_review=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])

    def test_off_center_port_touches_the_circle_instead_of_its_box(self):
        spec = {
            'title': 'Off-center comparison input',
            'canvas': {'width_pt': 160, 'height_pt': 84},
            'nodes': [
                {'id': 'source', 'shape': 'process', 'label': 'Input', 'box': [10, 18, 50, 26]},
                {'id': 'op', 'shape': 'operator', 'label': 'Sub', 'box': [80, 24, 42, 42]},
            ],
            'edges': [{'id': 'route', 'from': 'source', 'to': 'op', 'points': [[60, 33], [80, 33]]}],
        }
        with TemporaryDirectory() as output:
            report = render_diagram.render(spec, output, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])
        x, y = report['resolved_ports'][0]['end']
        self.assertEqual(y, 33)
        self.assertGreater(x, 82)
        self.assertAlmostEqual(hypot(x - 101, y - 45), 21, delta=.12)

    def test_horizontal_planner_keeps_the_operator_compact(self):
        spec = plan_diagram.plan({
            'title': 'Horizontal merge',
            'direction': 'horizontal',
            'canvas': {'width_pt': 360},
            'nodes': [
                {'id': 'input', 'shape': 'grid', 'label': 'Pair'},
                {'id': 'op', 'shape': 'operator', 'label': '+'},
                {'id': 'output', 'shape': 'tensor', 'label': 'Merged'},
            ],
            'edges': [{'from': 'input', 'to': 'op'}, {'from': 'op', 'to': 'output'}],
        })
        first, operator, last = spec['nodes']
        self.assertLess(operator['box'][2], first['box'][2])
        self.assertEqual(operator['box'][2], operator['box'][3])
        self.assertLess(first['box'][0], operator['box'][0])
        self.assertLess(operator['box'][0], last['box'][0])
        with TemporaryDirectory() as output:
            report = render_diagram.render(spec, output, preview_only=True)
        self.assertTrue(report['passed_geometry_checks'], report['errors'])


if __name__ == '__main__':
    unittest.main()
