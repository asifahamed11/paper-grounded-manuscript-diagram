"""Comprehensive test suite for visual engine styling, themes, and vector icons."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts import render_diagram as renderer
from scripts import themes
from scripts import vector_icons

ROOT = Path(__file__).resolve().parents[1]

try:
    import matplotlib
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def minimal_spec():
    return {
        'title': 'Test Schematic',
        'canvas': {'width_pt': 300, 'height_pt': 200, 'font_pt': 9, 'min_font_pt': 8.0},
        'nodes': [
            {'id': 'a', 'label': 'Start Process', 'box': [20, 30, 100, 40]},
            {'id': 'b', 'label': 'End Outcome', 'box': [180, 30, 100, 40]},
        ],
        'edges': [
            {'id': 'e1', 'from': 'a', 'to': 'b', 'points': [[120, 50], [180, 50]]}
        ]
    }


class VisualEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def draw(self, spec, **kwargs):
        return renderer.render(spec, self.out, stem='test-fig', dpi=150, **kwargs)

    # 1. Themes
    def test_themes_definitions_and_application(self):
        self.assertEqual(len(themes.THEMES), 5)
        for theme_name in ['nature-clean', 'ieee-crisp', 'neurips-soft', 'biomed-prisma', 'print-mono']:
            spec = minimal_spec()
            spec['style'] = {'theme': theme_name}
            resolved = themes.apply_theme(spec)
            # Original untouched
            self.assertNotIn('connector_color', spec['style'])
            # Resolved populated
            self.assertIn('connector_color', resolved['style'])
            self.assertIn('fill', resolved['nodes'][0])
            self.assertIn('stroke_color', resolved['nodes'][0])

    def test_theme_preserves_explicit_user_overrides(self):
        spec = minimal_spec()
        spec['style'] = {'theme': 'nature-clean', 'connector_color': '#FF0000'}
        spec['nodes'][0]['fill'] = '#123456'
        spec['nodes'][0]['stroke_color'] = '#654321'
        resolved = themes.apply_theme(spec)
        self.assertEqual(resolved['style']['connector_color'], '#FF0000')
        self.assertEqual(resolved['nodes'][0]['fill'], '#123456')
        self.assertEqual(resolved['nodes'][0]['stroke_color'], '#654321')

    def test_unknown_theme_rejected(self):
        spec = minimal_spec()
        spec['style'] = {'theme': 'non-existent-theme'}
        with self.assertRaises(ValueError):
            renderer.validate_spec(spec)

    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_theme_recorded_in_report(self):
        spec = minimal_spec()
        spec['style'] = {'theme': 'neurips-soft'}
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['style']['theme'], 'neurips-soft')
        self.assertFalse(report['style']['shadow'])

        # Explicit shadow=True
        spec_shadow = minimal_spec()
        spec_shadow['style'] = {'theme': 'neurips-soft', 'shadow': True}
        report_shadow = self.draw(spec_shadow)
        self.assertTrue(report_shadow['style']['shadow'])

    # 2. Font Auto
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_font_family_auto_resolves_and_renders(self):
        name, path = themes.resolve_font('auto')
        self.assertIsInstance(name, str)
        self.assertTrue(Path(path).exists())

        spec = minimal_spec()
        spec['canvas']['font_family'] = 'auto'
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['font_requested'], 'auto')
        self.assertEqual(report['font_used'], name)

    # 3. Vector Card Elevation (Shadow)
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_card_shadow_elevation(self):
        spec = minimal_spec()
        spec['style'] = {'shadow': True}
        spec['nodes'][0]['shadow'] = True
        report = self.draw(spec, eps=True)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertIn('test-fig.eps', report['exports'])

    # 4. Accent Stripes
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_accent_stripe_padding_and_validation(self):
        spec = minimal_spec()
        spec['nodes'][0]['accent'] = 'left'
        spec['nodes'][0]['accent_color'] = '#0072B2'
        spec['nodes'][1]['accent'] = 'top'
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])

        # Bad accent direction
        bad_spec = minimal_spec()
        bad_spec['nodes'][0]['accent'] = 'bottom'
        with self.assertRaises(ValueError):
            renderer.validate_spec(bad_spec)

        # Accent on group shape rejected
        bad_grp = minimal_spec()
        bad_grp['nodes'][0]['shape'] = 'group'
        bad_grp['nodes'][0]['accent'] = 'left'
        with self.assertRaises(ValueError):
            renderer.validate_spec(bad_grp)

    # 5. Group Containers
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_group_container_fill_and_border_style(self):
        spec = minimal_spec()
        spec['nodes'][0]['box'] = [20, 45, 100, 40]
        spec['nodes'][1]['box'] = [180, 45, 100, 40]
        spec['edges'][0]['points'] = [[120, 65], [180, 65]]
        spec['nodes'].append({
            'id': 'grp', 'shape': 'group', 'box': [10, 5, 280, 95],
            'label': 'Group Container', 'container_fill': '#F0F4F8',
            'border_style': 'dashed'
        })
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])

        # Non-group container_fill rejected
        bad_spec = minimal_spec()
        bad_spec['nodes'][0]['container_fill'] = '#F0F4F8'
        with self.assertRaises(ValueError):
            renderer.validate_spec(bad_spec)

    # 6. Badges
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_badge_rendering_and_contrast_checks(self):
        spec = minimal_spec()
        spec['nodes'][0]['badge'] = 'INPUT'
        spec['nodes'][0]['badge_fill'] = '#1B2A38'
        spec['nodes'][0]['badge_text_color'] = '#FFFFFF'
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])
        badge_text = next((t for t in report['text'] if t['id'] == 'a:badge'), None)
        self.assertIsNotNone(badge_text)
        self.assertEqual(badge_text['text'], 'INPUT')
        self.assertGreaterEqual(badge_text['contrast'], 4.5)

        # Low contrast badge rejected
        bad_spec = minimal_spec()
        bad_spec['nodes'][0]['badge'] = 'FAIL'
        bad_spec['nodes'][0]['badge_fill'] = '#EEEEEE'
        bad_spec['nodes'][0]['badge_text_color'] = '#FFFFFF'
        bad_report = self.draw(bad_spec)
        self.assertFalse(bad_report['passed_geometry_checks'])
        self.assertTrue(any('Badge a:badge contrast' in e for e in bad_report['errors']))

    # 7. Arrow Scale & Crossing Jump
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_arrow_scale_and_crossing_jump(self):
        spec = {
            'title': 'Crossing Test',
            'canvas': {'width_pt': 300, 'height_pt': 240},
            'style': {'arrow_scale': 7.5, 'crossing_jump': True},
            'nodes': [
                {'id': 'a', 'label': 'A', 'box': [20, 100, 60, 30]},
                {'id': 'b', 'label': 'B', 'box': [200, 100, 60, 30]},
                {'id': 'c', 'label': 'C', 'box': [110, 20, 60, 30]},
                {'id': 'd', 'label': 'D', 'box': [110, 180, 60, 30]},
            ],
            'edges': [
                {'id': 'ab', 'from': 'a', 'to': 'b', 'points': [[80, 115], [200, 115]]},
                {'id': 'cd', 'from': 'c', 'to': 'd', 'points': [[140, 50], [140, 180]]},
            ],
            'allowed_crossings': [
                {'edges': ['ab', 'cd'], 'reason': 'Independent orthogonal paths'}
            ]
        }
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['style']['arrow_scale'], 7.5)

    # 8. Legend
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_legend_rendering_and_collision(self):
        spec = minimal_spec()
        spec['legend'] = {
            'box': [20, 140, 260, 24],
            'items': [
                {'label': 'Category A', 'color': '#0072B2'},
                {'label': 'Category B', 'color': '#D55E00'}
            ]
        }
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])
        leg_items = [t for t in report['text'] if t['id'].startswith('legend:item-')]
        self.assertEqual(len(leg_items), 2)

        # Legend overlapping node triggers error
        bad_spec = minimal_spec()
        bad_spec['legend'] = {
            'box': [20, 30, 150, 40], # overlaps node a
            'items': [{'label': 'Item', 'color': '#0072B2'}]
        }
        bad_report = self.draw(bad_spec)
        self.assertFalse(bad_report['passed_geometry_checks'])
        self.assertTrue(any('Legend overlaps node a' in e for e in bad_report['errors']))

    # 9. Vector Icons
    def test_vector_icons_complete_library(self):
        icons_list = vector_icons.list_icons()
        self.assertEqual(len(icons_list), 30)
        for name in icons_list:
            svg = vector_icons.as_svg(name)
            uri = vector_icons.as_data_uri(name)
            self.assertTrue(svg.startswith('<svg'))
            self.assertTrue(uri.startswith('data:image/svg+xml;base64,'))

    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_vector_icon_rendering_does_not_flag_raster(self):
        spec = minimal_spec()
        spec['icons'] = [
            {'id': 'vicon', 'vector_icon': 'database', 'node': 'a', 'placement': 'title', 'size_pt': [12, 12], 'alt': 'Database'}
        ]
        report = self.draw(spec)
        self.assertTrue(report['passed_geometry_checks'])
        self.assertEqual(report['icons'][0]['format'], 'vector')
        self.assertFalse(report.get('raster_icons_in_vector_exports', False))

    # 10. Draw.io Parity
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_drawio_parity_with_container_fill_shadow_and_icons(self):
        spec = minimal_spec()
        spec['nodes'][0]['box'] = [20, 45, 100, 40]
        spec['nodes'][1]['box'] = [180, 45, 100, 40]
        spec['edges'][0]['points'] = [[120, 65], [180, 65]]
        spec['style'] = {'shadow': True}
        spec['nodes'].append({
            'id': 'grp', 'shape': 'group', 'box': [10, 5, 280, 95],
            'label': 'Group Container', 'container_fill': '#F0F4F8'
        })
        spec['icons'] = [
            {'id': 'vicon', 'vector_icon': 'cpu', 'node': 'a', 'placement': 'title', 'size_pt': [12, 12], 'alt': 'CPU'}
        ]
        spec['legend'] = {
            'box': [20, 150, 260, 24],
            'items': [{'label': 'Proc', 'color': '#0072B2'}]
        }
        report = self.draw(spec, drawio=True)
        self.assertTrue(report['passed_geometry_checks'])
        drawio_file = self.out / 'test-fig.drawio'
        self.assertTrue(drawio_file.exists())
        content = drawio_file.read_text(encoding='utf-8')
        self.assertIn('shadow=1;', content)
        self.assertIn('fillColor=#F0F4F8', content)
        self.assertIn('data:image/svg+xml;base64,', content)
        self.assertIn('legend-frame', content)

    # 11. Showcase Templates Pass Geometry Checks
    @unittest.skipUnless(HAS_MPL, 'Optional Matplotlib is not installed')
    def test_bundled_showcase_templates(self):
        for tpl_name in ['ml-architecture.json', 'multi-panel-method.json']:
            with self.subTest(template=tpl_name):
                path = ROOT / 'templates' / tpl_name
                spec = json.loads(path.read_text(encoding='utf-8'))
                report = self.draw(spec, drawio=True, eps=True)
                self.assertTrue(report['passed_geometry_checks'], report['errors'])


if __name__ == '__main__':
    unittest.main()
