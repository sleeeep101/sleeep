"""只使用临时合成 PDF 验证公开下载后的最小摄入闭环。"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "ingest_pdf.py"


def make_minimal_pdf(path: Path) -> None:
    """写入一个不含真实论文或个人资料的单页 PDF。"""
    sentence = "Public synthetic PDF fixture for extraction verification. "
    fixture_text = sentence * 20
    stream = b"BT /F1 14 Tf 72 720 Td (" + fixture_text.encode("ascii") + b") Tj ET"
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = []
    for obj in objects:
        offsets.append(len(content))
        content.extend(obj)
    xref_offset = len(content)
    content.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    path.write_bytes(content)


class PublicFixtureEndToEndTests(unittest.TestCase):
    def test_pypdf_extracts_a_public_synthetic_pdf_to_markdown(self) -> None:
        spec = importlib.util.spec_from_file_location("pdf_ingest_module", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pdf_path = tmp_path / "public_synthetic.pdf"
            output_root = tmp_path / "processed"
            make_minimal_pdf(pdf_path)

            result = module.ingest_pdf(pdf_path, engine="fallback_text", output_dir=output_root)

            self.assertEqual(result["status"], "success")
            self.assertGreater(result["char_count"], 0)
            markdown = (output_root / "public_synthetic" / "paper.md").read_text(encoding="utf-8")
            metadata = (output_root / "public_synthetic" / "metadata.json").read_text(encoding="utf-8")
            report = (output_root / "public_synthetic" / "extraction_report.md").read_text(encoding="utf-8")
            self.assertIn("Public synthetic PDF fixture for extraction verification.", markdown)
            self.assertIn('"source_file": "public_synthetic.pdf"', metadata)
            self.assertIn('"source_path_redacted": true', metadata)
            for output in (markdown, metadata, report):
                self.assertNotIn(str(tmp_path), output)


if __name__ == "__main__":
    unittest.main()
