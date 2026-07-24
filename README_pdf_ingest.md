# PDF Ingestion Module — 统一 PDF/图片 阅读入口

> 整合了 3 条旧路径为 1 个统一 `pdf_ingest` 包。

## 整合前后对比

| | 旧（3 条路径） | 新（1 条路径） |
|---|---|---|
| 提取管线 | `pdf_extractor.py` (6引擎级联) | → `pdf_ingest/ingest_pdf.py` |
| 下载+分级 | `fulltext_utils.py` (下载+解析+等级判定) | → `pdf_ingest/ingest_pdf.py` |
| CLI入口 | `ingest_pdf.py` + `import_claude_paper_reading.py` | → 委托至 `pdf_ingest` 包 |

## 架构

```
pdf_ingest/
├── __init__.py               # Public API
├── ingest_pdf.py             # 主摄入管线 (提取→OCR→分级→归档)
└── import_manual_claude.py   # Claude 手动阅读导入
```

## 提取引擎 (7引擎级联)

| 优先级 | 引擎 | 用途 |
|--------|------|------|
| 1 | **pymupdf4llm** | 结构化 Markdown (学术论文最佳) |
| 2 | **pymupdf (fitz)** | 纯文本提取 |
| 3 | **pdfplumber** | 文本 + 表格提取 |
| 4 | **pypdf** | 轻量级纯文本兜底 |
| 5 | **easyocr** | OCR 扫描件 (中英双语, 纯 Python) |
| 6 | **tesseract** | OCR 备选 (需系统安装) |
| 7 | **markitdown** | 通用文档转换 (终极兜底) |

## 图片 OCR 支持

图片文件 (PNG/JPG/TIFF) 也会自动走 OCR 管线 (easyocr → tesseract)，无需单独命令。

## 自动解析方式

```bash
# 单篇 PDF
python scripts/ingest_pdf.py --pdf "path/to/paper.pdf"

# 批量目录
python scripts/ingest_pdf.py --dir "path/to/pdf_folder"

# 指定引擎
python scripts/ingest_pdf.py --pdf "paper.pdf" --engine pymupdf4llm
python scripts/ingest_pdf.py --pdf "paper.pdf" --engine fallback_text

# 强制 OCR (扫描件)
python scripts/ingest_pdf.py --pdf "paper.pdf" --force-ocr

# 强制重新处理
python scripts/ingest_pdf.py --pdf "paper.pdf" --force

# 查看可用引擎
python scripts/ingest_pdf.py --list-engines
```

引擎优先级（`--engine auto`）: pymupdf4llm → pymupdf → pdfplumber → pypdf → easyocr → tesseract → markitdown

## Claude 手动后备方式

当 PDF 无法自动解析时（扫描件/编码损坏/依赖失败），将论文交给 Claude 阅读：

```bash
python scripts/import_claude_paper_reading.py --source "data/pdf_library/manual_claude_input/my_reading.md" --pdf "path/to/original.pdf"
```

## 什么时候该用 Claude 手动阅读

1. PyMuPDF4LLM 提取文本为空或极低（<50 字符/页）
2. PDF 是扫描版，OCR 未配置
3. PDF 编码损坏，中文乱码不可恢复
4. 本地依赖冲突，短时间无法修复
5. 论文很重要，不值得为环境问题中断阅读流程

## Python API

```python
from pdf_ingest import ingest_pdf, ingest_dir, import_claude_reading, list_available

# 检查可用引擎
print(list_available())  # ['pymupdf4llm', 'pymupdf', 'pdfplumber', ...]

# 单篇 PDF
result = ingest_pdf("path/to/paper.pdf")
print(result["status"], result["reading_level"], result["method"])

# 批量
results = ingest_dir("path/to/pdf_folder")

# 导入 Claude 阅读
result = import_claude_reading("my_reading.md", "original.pdf")
```

## 输出文件结构

```
data/pdf_library/processed/<pdf_stem>/
  paper.md              # 全文 Markdown（Claude 版含免责声明）
  metadata.json         # 元信息（引擎/模式/字符数/可信度/阅读等级）
  chunks.jsonl          # 分块（每行 JSON）
  extraction_report.md  # 质量检测报告
```

## metadata.json 关键字段

- `engine_used`: pymupdf4llm | pymupdf | easyocr | tesseract | markitdown | manual_claude
- `extraction_mode`: automatic | manual_claude
- `confidence`: high | medium | low
- `reading_level`: PDF_TEXT_FULL | PDF_TEXT_PARTIAL | ABSTRACT_ONLY | META_ONLY
- `ocr_required`: true/false
- `manual_claude_used`: true/false
- `quality_score`: 0-1 文本质量评分

## 阅读等级说明

| 等级 | 含义 | 可信度 |
|------|------|--------|
| PDF_TEXT_FULL | 全文自动提取，≥15000字符，覆盖≥3类关键章节 | high/medium |
| PDF_TEXT_PARTIAL | 已提取正文但未达全文标准 | medium |
| ABSTRACT_ONLY | 仅摘要级内容 | low |
| META_ONLY | 仅元数据，无文本 | low |

## 基础安装

```bash
pip install pymupdf4llm pymupdf pypdf
```

## 可选安装

```bash
# pdfplumber — 表格提取
pip install pdfplumber

# easyocr — 扫描件 OCR (中英双语, 纯 Python, 无系统依赖)
pip install easyocr

# markitdown — 通用文档转换兜底
pip install markitdown
```

## 重型可选（不默认安装）

```bash
# Tesseract — 备选 OCR (需系统安装)
# 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
# 安装后: pip install pytesseract

# Docling — 复杂PDF、表格、版面、OCR
pip install docling

# MinerU — 科研文献公式/表格
pip install magic-pdf

# Marker — PDF/Office/HTML/EPUB 转 MD
pip install marker-pdf

# PaddleOCR — 中文扫描版 OCR
pip install paddleocr paddlepaddle

# Surya — OCR + 版面分析
pip install surya-ocr
```
