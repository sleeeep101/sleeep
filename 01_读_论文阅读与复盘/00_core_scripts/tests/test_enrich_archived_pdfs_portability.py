import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "enrich_archived_pdfs.py"
SPEC = importlib.util.spec_from_file_location("enrich_archived_pdfs", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class EnrichArchivedPdfsPortabilityTests(unittest.TestCase):
    def test_default_root_is_the_cloned_workflow_root(self) -> None:
        self.assertEqual(module.DEFAULT_ROOT, MODULE_PATH.parents[2])

    def test_rendered_markdown_redacts_the_local_source_path(self) -> None:
        rendered = module.render_markdown(
            Path("C:" + r"\Users\Example\Private Research\paper.pdf"),
            "a" * 64,
            "Synthetic extraction text.",
            "pypdf",
            "",
        )
        self.assertIn("source_pdf: paper.pdf", rendered)
        self.assertIn("source_path_redacted: true", rendered)
        self.assertNotIn("C:" + r"\Users\Example", rendered)

    def test_no_machine_specific_markitdown_fallback_is_baked_in(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("D:" + r"\ruanjian\tools", source)
        self.assertIn("PDF_INGEST_MARKITDOWN", source)
        self.assertIn("workflow_root not in sys.path", source)


if __name__ == "__main__":
    unittest.main()
