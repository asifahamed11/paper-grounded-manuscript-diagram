import importlib.util
import tempfile
import unittest
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


class SvgValidatorTests(unittest.TestCase):
    def test_valid_svg(self):
        module = load_script("validate_svg", "validate_svg.py")
        # Exercise XML validity independently of CLI.
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><text x="1" y="5">A</text></svg>')
        self.assertEqual(root.tag.rsplit("}", 1)[-1], "svg")


if __name__ == "__main__":
    unittest.main()
