import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "ingest_pdf.py"


class PortableEnginePathTests(unittest.TestCase):
    def test_no_user_specific_tool_path_is_baked_in(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("D:" + r"\ruanjian\tools", source)
        self.assertIn("PDF_INGEST_TESSERACT", source)
        self.assertIn("PDF_INGEST_MARKITDOWN", source)

    def test_engine_listing_can_run_without_a_pdf_argument(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("group = parser.add_mutually_exclusive_group(required=False)", source)
        self.assertIn("unless --list-engines is used", source)


if __name__ == "__main__":
    unittest.main()
