import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "00_core_scripts" / "check_material_completeness.py"
SPEC = importlib.util.spec_from_file_location("check_material_completeness", MODULE_PATH)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


class MaterialCompletenessTests(unittest.TestCase):
    def test_short_keyword_only_is_not_enough_material(self) -> None:
        results = checker.check_materials("research question")
        self.assertFalse(results["research_question"]["found"])

    def test_substantive_research_question_is_recognized(self) -> None:
        text = "Research question: " + "How does terrain affect erosion risk across nested catchments? " * 2
        results = checker.check_materials(text)
        self.assertTrue(results["research_question"]["found"])

    def test_missing_claim_evidence_matrix_is_reported(self) -> None:
        results = checker.check_materials("Research question: " + "x" * 80)
        self.assertIn("claim_evidence", results)
        self.assertFalse(results["claim_evidence"]["found"])

    def test_cli_report_redacts_the_input_absolute_path(self) -> None:
        material = (
            "研究问题：" + "坡面地形如何影响沟蚀风险？" * 5 + "\n"
            "主张—证据矩阵：主张 A 对应图 1 和可复核统计。\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "private_materials.md"
            input_path.write_text(material, encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = checker.main(["--input", str(input_path)])
            report = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("输入文件: private_materials.md (local path redacted)", report)
            self.assertNotIn(str(input_path), report)


if __name__ == "__main__":
    unittest.main()
