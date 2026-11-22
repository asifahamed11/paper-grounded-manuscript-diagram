import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R, P = load('render_diagram'), load('prepare_icon')


def method():
    return {'title':'Illustrative icon workflow', 'canvas':{'width_pt':252,'height_pt':160},
            'nodes':[{'id':'records','box':[20,10,210,42],'label':'Reviewed records','icon_space_pt':40},
                     {'id':'analysis','box':[20,100,210,42],'label':'Analysis'}],
            'edges':[{'from':'records','to':'analysis','points':[[125,52],[125,100]]}],
            'icons':[{'id':'records-icon','path':'assets/records.png','box':[28,20,22,22],
                      'node':'records','alt':'Stored records'}]}


class IconSpecTests(unittest.TestCase):
    def test_invalid_paths_and_outside_boxes_are_rejected_without_dependencies(self):
        for path in ['../icon.png','https://example.com/icon.png','C:/icon.png','/icon.png','a\\icon.png','a.svg']:
            spec = method(); spec['icons'][0]['path'] = path
            with self.assertRaises(ValueError):R.validate_spec(spec)
        spec = method(); spec['icons'][0]['box'] = [250,0,20,20]
        with self.assertRaises(ValueError):R.validate_spec(spec)

    def test_icon_owner_and_reserved_strip_are_required(self):
        for change in [{'node':'unknown'}, {'box':[100,20,22,22]}, {'alt':''}]:
            spec = method(); spec['icons'][0].update(change)
            with self.assertRaises(ValueError):R.validate_spec(spec)
        spec = method(); spec['nodes'][0].pop('icon_space_pt')
        with self.assertRaises(ValueError):R.validate_spec(spec)

    def test_duplicate_ids_and_malformed_lists(self):
        spec = method(); spec['icons'].append(copy.deepcopy(spec['icons'][0]))
        with self.assertRaises(ValueError):R.validate_spec(spec)
        spec['icons'] = {}
        with self.assertRaises(ValueError):R.validate_spec(spec)


try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
try:
    import matplotlib
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


@unittest.skipUnless(HAS_PIL, 'Optional Pillow is not installed')
class CutoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'raw.png'; self.output = self.root/'icon.png'

    def test_connected_exterior_preserves_enclosed_white(self):
        image = Image.new('RGBA',(80,60),'white')
        ImageDraw.Draw(image).rectangle((20,10,59,49),outline='black',width=4)
        image.save(self.source)
        report = P.prepare(self.source,self.output)
        with Image.open(self.output) as cutout:
            self.assertEqual(cutout.size,(56,56))
            self.assertEqual(cutout.getpixel((0,0))[3],0)
            self.assertEqual(cutout.getpixel((28,28)),(255,255,255,255))
        self.assertEqual(report['mode'],'white')
        self.assertTrue(report['warnings'])
        with Image.open(self.root/'icon-background-check.png') as preview:
            self.assertEqual(preview.size,(168,56))
        self.assertTrue((self.root/'icon.json').is_file())

    def test_native_soft_alpha_is_preserved(self):
        image = Image.new('RGBA',(60,60))
        ImageDraw.Draw(image).rectangle((15,15,44,44),fill=(0,114,178,128))
        image.save(self.source)
        report = P.prepare(self.source,self.output)
        self.assertEqual(report['mode'],'alpha')
        with Image.open(self.output) as out:
            self.assertEqual(out.getpixel((15,15)),(0,114,178,128))

    def test_single_colour_matte_recovers_alpha_without_white_halo(self):
        foreground = (0,114,178)
        image = Image.new('RGBA',(60,60),'white')
        for x, alpha in [(20,64),(21,128),(22,255)]:
            image.putpixel((x,20),tuple(round(c*alpha/255+255*(1-alpha/255)) for c in foreground)+(255,))
        result = P.solid_matte(image,'#0072B2')
        for x, alpha in [(20,64),(21,128),(22,255)]:
            self.assertEqual(result.getpixel((x,20))[:3],foreground)
            self.assertLessEqual(abs(result.getpixel((x,20))[3]-alpha),1)

    def test_single_colour_matte_refuses_multicolour_or_near_white(self):
        for foreground in ['#FFFFFF','#0072B2']:
            with self.assertRaises(ValueError):P.solid_matte(Image.new('RGBA',(3,3),'red'),foreground)

    def test_local_mask_and_unmatting(self):
        image = Image.new('RGBA',(40,40),'white')
        image.putpixel((20,20),(127,184,216,255)); image.save(self.source)
        mask = Image.new('L',(40,40)); mask.putpixel((20,20),128)
        mask_path = self.root/'mask.png'; mask.save(mask_path)
        P.prepare(self.source,self.output,mask=mask_path,unmatte_white=True)
        with Image.open(self.output) as out:
            r,g,b,a = out.getpixel((8,8))
            self.assertEqual(a,128); self.assertLessEqual(r,1)
            self.assertLessEqual(abs(g-114),1); self.assertLessEqual(abs(b-178),1)

    def test_empty_clipped_nonwhite_and_opaque_failures(self):
        for image, mode in [(Image.new('RGBA',(30,30),'white'),'white'),
                            (Image.new('RGBA',(30,30),'red'),'white'),
                            (Image.new('RGBA',(30,30),'red'),'alpha')]:
            image.save(self.source)
            with self.assertRaises(ValueError):P.prepare(self.source,self.output,mode=mode)
            self.assertFalse(self.output.exists())
        image = Image.new('RGBA',(30,30)); ImageDraw.Draw(image).rectangle((0,5,10,15),fill='blue')
        image.save(self.source)
        with self.assertRaises(ValueError):P.prepare(self.source,self.output)

    def test_no_overwrite_bad_mask_or_wrong_extension(self):
        image = Image.new('RGBA',(30,30)); ImageDraw.Draw(image).rectangle((5,5,24,24),fill='blue')
        image.save(self.source)
        with self.assertRaises(ValueError):P.prepare(self.source,self.source)
        with self.assertRaises(ValueError):P.prepare(self.source,self.output.with_suffix('.jpg'))
        Image.new('L',(2,2),255).save(self.root/'mask.png')
        with self.assertRaises(ValueError):P.prepare(self.source,self.output,mask=self.root/'mask.png')
        P.prepare(self.source,self.output)
        with self.assertRaises(ValueError):P.prepare(self.source,self.output)


@unittest.skipUnless(HAS_PIL and HAS_MPL, 'Optional rendering dependencies are not installed')
class IconRenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); (self.root/'assets').mkdir()
        image = Image.new('RGBA',(128,128))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((24,12,104,116),radius=10,fill='#0072B2')
        draw.line((42,48,86,48),fill='white',width=5)
        image.save(self.root/'assets/records.png')

    def draw(self,spec):
        return R.render(spec,self.root/'output',dpi=150,asset_dir=self.root)

    def test_in_node_asset_exports_embed_and_portable_source(self):
        report = self.draw(method())
        self.assertTrue(report['passed_geometry_checks'],report['errors'])
        self.assertGreaterEqual(report['icons'][0]['native_dpi'],300)
        self.assertTrue(report['raster_icons_in_vector_exports'])
        svg = self.root/'output/figure-01.svg'
        tree = ET.parse(svg)
        images = list(tree.iter('{http://www.w3.org/2000/svg}image'))
        self.assertEqual(len(images),1)
        self.assertTrue(images[0].get('{http://www.w3.org/1999/xlink}href').startswith('data:image/png;base64,'))
        self.assertTrue(load('validate_svg').validate(svg)['passed_basic_structural_checks'])
        source = self.root/'output/figure-01-source.json'
        self.assertTrue((source.parent/json.loads(source.read_text())['icons'][0]['path']).is_file())
        # Move the deliverable; it must not depend on the original raw assets.
        moved = self.root/'moved'; shutil.copytree(source.parent,moved)
        shutil.rmtree(self.root/'assets')
        rerun = R.render(json.loads((moved/source.name).read_text()),self.root/'rerun',dpi=150,asset_dir=moved)
        self.assertTrue(rerun['passed_geometry_checks'])

    def test_fit_preserves_aspect_ratio(self):
        with Image.open(self.root/'assets/records.png') as image:
            image.resize((256,128)).save(self.root/'assets/records.png')
        report = self.draw(method())
        self.assertTrue(report['passed_geometry_checks'])
        x,y,X,Y = report['icons'][0]['bounds_pt']
        self.assertAlmostEqual((X-x)/(Y-y),2)

    def test_icon_resampling_does_not_introduce_dark_ringing(self):
        report = self.draw(method())
        x,y,X,Y = report['icons'][0]['bounds_pt']
        with Image.open(self.root/'output/figure-01.png') as image:
            patch = image.convert('RGB').crop((int(x*150/72),int(y*150/72),int(X*150/72),int(Y*150/72)))
            pixels = list(patch.getdata())
        # Source blue and white composited on white cannot create black fringes.
        self.assertTrue(all(g>=113 and b>=177 for r,g,b in pixels))
        self.assertGreater(sum(r<20 and abs(g-114)<5 and abs(b-178)<5 for r,g,b in pixels),20)

    def test_low_resolution_and_label_collisions_fail_exports(self):
        with Image.open(self.root/'assets/records.png') as image:
            image.resize((16,16)).save(self.root/'assets/records.png')
        report = self.draw(method())
        self.assertFalse(report['passed_geometry_checks']); self.assertEqual(report['exports'],[])
        self.assertTrue(any('native DPI' in e for e in report['errors']))

    def test_standalone_asset_collisions_with_route_and_annotation(self):
        spec = method(); spec['icons'][0].pop('node'); spec['icons'][0]['box']=[114,65,22,22]
        spec['annotations']=[{'box':[100,60,60,34],'label':'Caption'}]
        report = self.draw(spec)
        self.assertTrue(any('crosses icon' in e for e in report['errors']))
        self.assertTrue(any('overlaps label' in e for e in report['errors']))

    def test_opaque_and_blank_assets_fail(self):
        for fill in ['white',(0,0,0,0)]:
            Image.new('RGBA',(128,128),fill).save(self.root/'assets/records.png')
            with self.assertRaises(ValueError):self.draw(method())

    def test_cli_resolves_asset_paths_from_spec_not_working_directory(self):
        source = self.root/'diagram.json'; source.write_text(json.dumps(method()))
        result = subprocess.run([sys.executable,str(ROOT/'scripts/render_diagram.py'),str(source),
                                 '--output-dir',str(self.root/'cli'),'--dpi','150'],cwd=ROOT,
                                capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
