import importlib.util
import tempfile
import unittest
import csv
import subprocess
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ScorePapersTests(unittest.TestCase):
    def test_ranking_prefers_higher_relevance(self):
        module = load_script("score_papers", "score_papers.py")
        records = [
            {"title": "A", "year": 2025, "citations": 10, "relevance": 95, "figure_relevance": 90},
            {"title": "B", "year": 2025, "citations": 10, "relevance": 20, "figure_relevance": 20},
        ]
        ranked = module.calculate_scores(records, current_year=2026)
        self.assertEqual(ranked[0]["title"], "A")
        self.assertGreater(ranked[0]["weighted_score"], ranked[1]["weighted_score"])

    def test_empty_list(self):
        module = load_script("score_papers", "score_papers.py")
        self.assertEqual(module.calculate_scores([]), [])

    def test_nonfinite_inputs_and_future_year(self):
        module=load_script('score_papers','score_papers.py')
        ranked=module.calculate_scores([{'title':'A','year':'NaN','citations':'Infinity','relevance':'NaN'},
                                        {'title':'B','year':2099,'citations':0}],current_year=2026)
        self.assertTrue(all(x['recency_score']==0 for x in ranked))
        self.assertTrue(all(x['weighted_score']==0 for x in ranked))

    def test_csv_preserves_fields_present_in_later_records(self):
        module=load_script('score_papers','score_papers.py')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'nested/out.csv';module.write_csv([{'title':'A'},{'title':'B','doi':'10.example/test'}],p)
            with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            self.assertEqual(rows[1]['doi'],'10.example/test')


class SvgValidatorTests(unittest.TestCase):
    def test_valid_svg(self):
        module = load_script("validate_svg", "validate_svg.py")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.svg';p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><text x="1" y="5">A</text></svg>')
            self.assertTrue(module.validate(p)['passed_basic_structural_checks'])

    def test_invalid_dimensions_and_viewbox_fail_real_validator(self):
        module=load_script('validate_svg','validate_svg.py')
        cases=['<svg/>','<svg width="0" height="10" viewBox="0 0 10 10"/>',
               '<svg width="10" height="10" viewBox="0 0 NaN 10"/>',
               '<svg xmlns="urn:wrong" width="10" height="10" viewBox="0 0 10 10"/>']
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.svg'
            for s in cases:
                p.write_text(s);self.assertFalse(module.validate(p)['passed_basic_structural_checks'])

    def test_active_and_external_svg_content_rejected(self):
        module=load_script('validate_svg','validate_svg.py')
        payloads=['<script>alert(1)</script>','<image href="file:///private/image.png"/>',
                  '<rect onload="bad()"/>','<style>@import "https://example.com/font.css";</style>',
                  '<rect fill="url(https://example.com/image)"/>','<foreignObject/>',
                  '<set attributeName="href" to="https://example.com"/>']
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.svg'
            for s in payloads:
                p.write_text('<svg width="10" height="10" viewBox="0 0 10 10">'+s+'</svg>')
                self.assertFalse(module.validate(p)['passed_basic_structural_checks'],s)

    def test_xml_stylesheet_is_rejected(self):
        module=load_script('validate_svg','validate_svg.py')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.svg';p.write_text('<?xml-stylesheet href="https://example.com/style.css"?><svg width="10" height="10" viewBox="0 0 10 10"/>')
            self.assertFalse(module.validate(p)['passed_basic_structural_checks'])

    def test_cli_nonzero_for_bad_svg_and_nested_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.svg';p.write_text('<svg/>');report=Path(tmp)/'report/nested.json'
            run=subprocess.run([sys.executable,str(ROOT/'scripts/validate_svg.py'),str(p),'--json',str(report)],capture_output=True,text=True)
            self.assertEqual(run.returncode,1);self.assertFalse(json.loads(report.read_text())['passed_basic_structural_checks'])


class OptionalHelperTests(unittest.TestCase):
    def test_contact_sheet_does_not_include_itself_on_rerun(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Optional Pillow not installed')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);Image.new('RGB',(100,1000),'white').save(p/'tall.png')
            cmd=[sys.executable,str(ROOT/'scripts/build_contact_sheet.py'),str(p),'--output',str(p/'sheet.png'),'--thumb-width','100','--thumb-height','100']
            for _ in range(2):
                run=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
                self.assertIn('with 1 image(s)',run.stdout)
            with Image.open(p/'sheet.png') as result:self.assertLessEqual(result.height,142)

    def test_pdf_end_page_zero_is_not_silently_all_pages(self):
        try:import fitz
        except ImportError:self.skipTest('Optional PyMuPDF not installed')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'paper.pdf';d=fitz.open();d.new_page();d.save(p);d.close()
            cmd=[sys.executable,str(ROOT/'scripts/extract_pdf_figures.py'),str(p),'--end-page','0','--output-dir',str(Path(tmp)/'out')]
            run=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(run.returncode,2)


if __name__ == "__main__":
    unittest.main()
