"""
pdf_ingest — 统一 PDF/图片 阅读入口。

整合三条旧路径为一条:
  1. pdf_extractor.py 提取管线 (pymupdf4llm → pymupdf → easyocr → tesseract → pdfplumber → pypdf → markitdown)
  2. fulltext_utils.py 全文下载+解析+阅读等级判定
  3. ingest_pdf.py / import_claude_paper_reading.py CLI 包装

Public API:
  - ingest_pdf()          → 单篇 PDF 摄入
  - ingest_dir()          → 批量目录摄入
  - import_claude_reading() → 导入 Claude 手动阅读产出
  - list_available()      → 列出可用引擎
  - ExtractionResult      → 提取结果数据结构
"""

from .ingest_pdf import (
    ExtractionResult,
    ingest_pdf,
    ingest_dir,
    list_available,
)

from .import_manual_claude import import_claude_reading

__all__ = [
    "ExtractionResult",
    "ingest_pdf",
    "ingest_dir",
    "import_claude_reading",
    "list_available",
]
