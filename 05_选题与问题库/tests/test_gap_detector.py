"""Regression tests for local-evidence screening."""

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout


MODULE_PATH = Path(__file__).resolve().parent.parent / "gap_detector.py"
SPEC = importlib.util.spec_from_file_location("gap_detector", MODULE_PATH)
gap_detector = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gap_detector)


class GapDetectorTests(unittest.TestCase):
    def test_exact_and_partial_do_not_double_count(self) -> None:
        result = gap_detector.detect_gaps(
            ["urban heat", "heat island", "coastal flooding"],
            {"urban heat", "urban heat island"},
        )
        self.assertEqual(result["total_keywords"], 3)
        self.assertEqual(result["covered"], 1)
        self.assertEqual(result["uncovered"], ["heat island", "coastal flooding"])
        self.assertEqual(len(result["partial_matches"]), 1)
        self.assertEqual(result["gap_score"], 0.67)

    def test_explicit_graph_path_loads_only_paper_topics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text(
                json.dumps(
                    {"nodes": [
                        {"entity_type": "Paper", "topics": ["Spatial equity"]},
                        {"entity_type": "Person", "topics": ["Must not load"]},
                    ]}
                ),
                encoding="utf-8",
            )
            self.assertEqual(gap_detector.load_kg_topics(path), {"spatial equity"})

    def test_missing_graph_is_not_evidence_of_a_gap(self) -> None:
        self.assertEqual(gap_detector.load_kg_topics(Path("not-a-real-graph.json")), set())

    def test_missing_evidence_withholds_the_gap_score(self) -> None:
        result = gap_detector.detect_gaps(["coastal flooding"], set(), evidence_available=False)
        self.assertIsNone(result["gap_score"])
        self.assertFalse(result["evidence_available"])
        self.assertIn("do not infer", result["recommendation"])

    def test_cli_uses_the_public_example_as_explicit_evidence(self) -> None:
        example = MODULE_PATH.parents[1] / "knowledge_graph" / "examples" / "public_graph.json"
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = gap_detector.main(["gully erosion", "--kg-file", str(example)])
        self.assertEqual(exit_code, 0)
        self.assertIn("Graph evidence loaded: True", output.getvalue())
        self.assertIn("Exact coverage: 1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
