"""
ingest_pdf.py — 统一 PDF/图片 摄入管线。

整合三条旧路径:
  旧1. pdf_extractor.py → 6级提取级联 + OCR
  旧2. fulltext_utils.py → 下载 + 提取 + 阅读等级判定
  旧3. ingest_pdf.py CLI → pdf_ingest 模块 (此前为空壳)

引擎优先级 (--engine auto):
  pymupdf4llm → pymupdf(fitz) → pdfplumber → pypdf
  → easyocr(扫描件OCR) → tesseract(备选OCR)
  → markitdown(终极兜底)

输出结构:
  data/pdf_library/processed/<pdf_stem>/
    paper.md              # 全文 Markdown
    metadata.json         # 引擎/模式/字符数/可信度
    chunks.jsonl          # 分块 (每行 JSON)
    extraction_report.md  # 质量检测报告
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════════════

def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def _get_data_root() -> Path:
    """读取 config/paths.json 或使用默认路径。"""
    config_file = _get_project_root() / "config" / "paths.json"
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            aw = cfg.get("academic_workflow", {})
            root = aw.get("root", str(_get_project_root()))
            return Path(root)
        except Exception:
            pass
    return _get_project_root()

PROJECT_ROOT = _get_project_root()
DATA_ROOT = _get_data_root()
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "pdf_library" / "processed"

# Tesseract 路径
_TESSERACT_PATHS = [
    os.environ.get("PDF_INGEST_TESSERACT", ""),
    r"<LOCAL_PATH> Files\Tesseract-OCR\tesseract.exe",
    r"<LOCAL_PATH> Files (x86)\Tesseract-OCR\tesseract.exe",
]
_TESSERACT_EXE: Optional[str] = None

# MarkItDown 路径
_MARKITDOWN_PATHS = [
    os.environ.get("PDF_INGEST_MARKITDOWN", ""),
]

# ═══════════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ExtractionResult:
    """PDF 提取结果。"""
    text: str = ""
    method: str = "none"
    char_count: int = 0
    word_count: int = 0
    pages: int = 0
    has_ocr: bool = False
    has_tables: bool = False
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[str] = field(default_factory=list)
    error: str = ""
    warnings: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    reading_level: str = ""          # META_ONLY|ABSTRACT_ONLY|PDF_TEXT_PARTIAL|PDF_TEXT_FULL|HUMAN_CONFIRMED
    confidence: str = "low"          # high|medium|low
    chunks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════
# 引擎发现
# ═══════════════════════════════════════════════════════════════════

def _find_tesseract() -> Optional[str]:
    global _TESSERACT_EXE
    if _TESSERACT_EXE is not None:
        return _TESSERACT_EXE
    for p in _TESSERACT_PATHS:
        if Path(p).exists():
            _TESSERACT_EXE = p
            return p
    import shutil
    found = shutil.which("tesseract")
    if found:
        _TESSERACT_EXE = found
        return found
    try:
        import pytesseract
        exe = pytesseract.pytesseract.tesseract_cmd
        if exe and Path(exe).exists():
            _TESSERACT_EXE = exe
            return exe
    except Exception:
        pass
    return None


def _find_markitdown() -> Optional[str]:
    for p in _MARKITDOWN_PATHS:
        if Path(p).exists():
            return p
    import shutil
    return shutil.which("markitdown")


def list_available() -> List[str]:
    """列出所有可用引擎。"""
    engines = []
    # pymupdf4llm
    try:
        import pymupdf4llm  # noqa
        engines.append("pymupdf4llm")
    except ImportError:
        pass
    # pymupdf
    try:
        import pymupdf  # noqa
        engines.append("pymupdf")
    except ImportError:
        pass
    # pdfplumber
    try:
        import pdfplumber  # noqa
        engines.append("pdfplumber")
    except ImportError:
        pass
    # pypdf
    try:
        import pypdf  # noqa
        engines.append("pypdf")
    except ImportError:
        pass
    # easyocr
    try:
        import easyocr  # noqa
        engines.append("easyocr")
    except ImportError:
        pass
    # tesseract
    if _find_tesseract():
        engines.append("tesseract")
    # markitdown
    if _find_markitdown():
        engines.append("markitdown")
    # manual_claude (always available)
    engines.append("manual_claude")
    return engines


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def _count_words(text: str) -> int:
    return len(re.findall(r"[a-zA-Z]+", text))


def _safe_filename(name: str, max_len: int = 60) -> str:
    illegal = r'[<>:"/\\|?*\x00-\x1f]'
    clean = re.sub(illegal, "_", name)
    clean = re.sub(r"\s+", "_", clean)
    return clean.strip("._")[:max_len] or "unnamed"


def _hash_file(path: Path) -> str:
    """SHA256 文件哈希。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ═══════════════════════════════════════════════════════════════════
# 文本清洗
# ═══════════════════════════════════════════════════════════════════

def _clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    text = re.sub(r"第\s*\d+\s*页\s*/?\s*共?\s*\d*\s*页?", "", text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════
# 提取引擎
# ═══════════════════════════════════════════════════════════════════

# ── 1. pymupdf4llm ──

def _extract_pymupdf4llm(path: Path) -> Tuple[str, str, int]:
    try:
        import pymupdf4llm
        text = pymupdf4llm.to_markdown(str(path))
        if text and len(text.strip()) > 500:
            return text.strip(), "pymupdf4llm", 0
        return "", "pymupdf4llm 输出不足", 0
    except ImportError:
        return "", "pymupdf4llm 未安装", 0
    except Exception as exc:
        return "", f"pymupdf4llm 异常: {exc}", 0


# ── 2. pymupdf (fitz) ──

def _extract_pymupdf(path: Path) -> Tuple[str, str, int]:
    try:
        import pymupdf
        doc = pymupdf.open(str(path))
        page_count = doc.page_count
        pages = []
        for page in doc:
            t = page.get_text()
            if t:
                pages.append(t.strip())
        doc.close()
        text = "\n\n".join(pages)
        if len(text.strip()) > 500:
            return text.strip(), "pymupdf", page_count
        return "", "pymupdf 输出不足", page_count
    except ImportError:
        return "", "pymupdf 未安装", 0
    except Exception as exc:
        return "", f"pymupdf 异常: {exc}", 0


# ── 3. pdfplumber ──

def _extract_pdfplumber(path: Path) -> Tuple[str, str, List[str]]:
    try:
        import pdfplumber
        pages_list = []
        tables = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages_list.append(t)
                page_tables = page.extract_tables()
                for tbl in page_tables:
                    if tbl:
                        tbl_text = "\n".join(
                            "\t".join(str(c or "") for c in row) for row in tbl
                        )
                        tables.append(tbl_text)
        text = "\n\n".join(pages_list).strip()
        if len(text) > 500:
            return text, "pdfplumber", tables
        return "", "pdfplumber 输出不足", tables
    except ImportError:
        return "", "pdfplumber 未安装", []
    except Exception as exc:
        return "", f"pdfplumber 异常: {exc}", []


# ── 4. pypdf ──

def _extract_pypdf(path: Path) -> Tuple[str, str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                return "", "PDF 加密限制"
        pages = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t:
                pages.append(t)
        text = "\n\n".join(pages).strip()
        if len(text) > 500:
            return text, "pypdf"
        return "", "pypdf 输出不足"
    except ImportError:
        return "", "pypdf 未安装"
    except Exception as exc:
        return "", f"pypdf 异常: {exc}"


# ── 5. easyocr ──

def _extract_easyocr(path: Path, page_count: int = 0) -> Tuple[str, str]:
    try:
        import pymupdf
        import easyocr
        import numpy as np

        doc = pymupdf.open(str(path))
        actual_pages = page_count or doc.page_count

        reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)

        all_text = []
        for i, page in enumerate(doc):
            if i >= actual_pages:
                break
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            results = reader.readtext(img, detail=0)
            page_text = " ".join(results)
            if page_text:
                all_text.append(page_text)

        doc.close()
        text = "\n\n".join(all_text)
        if len(text.strip()) > 200:
            return text.strip(), "easyocr"
        return "", "easyocr 输出不足"
    except ImportError as e:
        return "", f"easyocr 依赖缺失: {e}"
    except Exception as exc:
        return "", f"easyocr 异常: {exc}"


# ── 6. tesseract ──

def _extract_tesseract(path: Path, page_count: int = 0) -> Tuple[str, str]:
    tesseract_exe = _find_tesseract()
    if not tesseract_exe:
        return "", "Tesseract 未安装"

    try:
        import pymupdf
        import pytesseract
        import numpy as np

        pytesseract.pytesseract.tesseract_cmd = tesseract_exe

        doc = pymupdf.open(str(path))
        actual_pages = page_count or doc.page_count

        all_text = []
        for i, page in enumerate(doc):
            if i >= actual_pages:
                break
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            if text.strip():
                all_text.append(text.strip())

        doc.close()
        combined = "\n\n".join(all_text)
        if len(combined.strip()) > 200:
            return combined.strip(), "tesseract"
        return "", "tesseract 输出不足"
    except ImportError as e:
        return "", f"tesseract 依赖缺失: {e}"
    except Exception as exc:
        return "", f"tesseract 异常: {exc}"


# ── 7. markitdown ──

def _extract_markitdown(path: Path) -> Tuple[str, str]:
    exe = _find_markitdown()
    if not exe:
        return "", "markitdown 不可用"

    try:
        result = subprocess.run(
            [exe, str(path)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        text = (result.stdout or "").strip()
        if result.returncode == 0 and len(text) > 1000:
            return text, "markitdown"
        return "", "markitdown 输出不足"
    except Exception as exc:
        return "", f"markitdown 异常: {exc}"


# ═══════════════════════════════════════════════════════════════════
# 章节解析
# ═══════════════════════════════════════════════════════════════════

_SECTION_PATTERNS = [
    ("abstract",     [r"(?i)^\s*abstract\s*$"]),
    ("introduction", [r"(?i)^\s*(introduction|引言|绪论|研究背景)\s*$"]),
    ("related_work", [r"(?i)^\s*(related work|相关研究|研究进展|文献综述)\s*$"]),
    ("study_area",   [r"(?i)^\s*(study area|研究区[域]?|试验区|样区)\s*$"]),
    ("data",         [r"(?i)^\s*(data|数据|材料|样本|数据来源|数据与方法)\s*$"]),
    ("method",       [r"(?i)^\s*(method|方法|模型|算法|技术路线|研究方法)\s*$"]),
    ("experiment",   [r"(?i)^\s*(experiment|实验|试验|案例|应用|验证)\s*$"]),
    ("results",      [r"(?i)^\s*(results|结果|分析结果|精度评价|评价结果)\s*$"]),
    ("discussion",   [r"(?i)^\s*(discussion|讨论|分析)\s*$"]),
    ("conclusion",   [r"(?i)^\s*(conclusion|结论|总结)\s*$"]),
]


def _parse_sections(text: str) -> Dict[str, str]:
    lines = text.split("\n")
    sections: Dict[str, str] = {}
    current_section = "preamble"
    current_text: List[str] = []

    for line in lines:
        matched = False
        for sec_name, patterns in _SECTION_PATTERNS:
            for pat in patterns:
                if re.match(pat, line.strip()):
                    if current_text:
                        sections[current_section] = "\n".join(current_text).strip()
                    current_section = sec_name
                    current_text = []
                    matched = True
                    break
            if matched:
                break
        if not matched:
            current_text.append(line)

    if current_text:
        sections[current_section] = "\n".join(current_text).strip()

    return sections


# ═══════════════════════════════════════════════════════════════════
# 质量评估
# ═══════════════════════════════════════════════════════════════════

def _quality_score(text: str) -> float:
    """评估提取文本质量 0-1。"""
    if not text or len(text) < 500:
        return 0.0

    score = 0.0
    length = len(text)

    # 长度 (0-0.3)
    if length > 50000:
        score += 0.3
    elif length > 10000:
        score += 0.2
    elif length > 2000:
        score += 0.1

    # 有效字符比例 (0-0.3)
    printable = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
    ratio = printable / max(length, 1)
    if ratio > 0.95:
        score += 0.3
    elif ratio > 0.85:
        score += 0.2
    elif ratio > 0.7:
        score += 0.1

    # 段落结构 (0-0.2)
    paragraphs = [p for p in text.split("\n\n") if len(p.strip()) > 50]
    if len(paragraphs) > 20:
        score += 0.2
    elif len(paragraphs) > 5:
        score += 0.1

    # 中英混合合理性 (0-0.2)
    cjk = len(re.findall(r"[一-鿿]", text))
    eng = len(re.findall(r"[a-zA-Z]", text))
    if cjk > 100 or eng > 500:
        score += 0.2
    elif cjk > 20 or eng > 100:
        score += 0.1

    return min(score, 1.0)


def _chinese_quality_check(text: str) -> Dict:
    """中文文本编码质量检测。"""
    issues = []
    text_len = len(text)

    if text_len < 100:
        return {"quality": "corrupted", "issues": ["文本过短 (<100字符)"],
                "chinese_char_ratio": 0.0, "garbled_char_count": 0, "short_line_ratio": 1.0}

    chinese_chars = len(re.findall(r'[一-鿿㐀-䶿]', text))
    chinese_ratio = chinese_chars / max(text_len, 1)

    garbled_patterns = [
        r'[�]',
        r'[■-◿]',
        r'[À-ÿ]{4,}',
        r'[\x80-\x9f]{2,}',
    ]
    garbled_count = 0
    for pat in garbled_patterns:
        garbled_count += len(re.findall(pat, text))

    lines = text.split('\n')
    unique_chars = len(set(text))
    if unique_chars / max(text_len, 1) < 0.05:
        issues.append(f"字符多样性极低 ({unique_chars}唯一字符/{text_len}总字符)")

    short_lines = [l for l in lines if 0 < len(l.strip()) < 10]
    short_line_ratio = len(short_lines) / max(len(lines), 1)
    if short_line_ratio > 0.5:
        issues.append(f"短行比例过高 ({short_line_ratio:.0%})")

    cn_keywords = ['摘要', '方法', '结果', '讨论', '结论', '引言',
                   '研究', '数据', '分析', '实验', '模型', '参考文献']
    missing_keywords = [kw for kw in cn_keywords if kw not in text]
    if len(missing_keywords) >= 8:
        issues.append(f"中文章节关键词大量缺失 (缺失{len(missing_keywords)}/{len(cn_keywords)}个)")

    if text_len < 500:
        quality = "corrupted"
    elif (text_len > 2000 and chinese_ratio < 0.05) or garbled_count > 50:
        quality = "corrupted"
    elif garbled_count > 10 or short_line_ratio > 0.6:
        quality = "suspicious"
    else:
        quality = "ok"

    return {
        "quality": quality,
        "issues": issues,
        "chinese_char_ratio": round(chinese_ratio, 4),
        "garbled_char_count": garbled_count,
        "short_line_ratio": round(short_line_ratio, 4),
    }


def _is_scanned(text: str, page_count: int) -> bool:
    if page_count <= 1:
        return False
    chars_per_page = len(text) / max(page_count, 1)
    return chars_per_page < 200


# ═══════════════════════════════════════════════════════════════════
# 阅读等级判定
# ═══════════════════════════════════════════════════════════════════

def _classify_reading_level(
    text: str,
    sections: Dict[str, str],
    method: str,
    extraction_mode: str,
) -> Tuple[str, str, str]:
    """判定阅读等级。

    Returns:
        (reading_level, confidence, reason)
    """
    text_len = len(text)
    word_count = _count_words(text)

    # 无文本
    if not text or text_len < 100:
        return "META_ONLY", "low", "无可用文本内容"

    # 仅摘要级（极短文本）
    if text_len < 500:
        return "ABSTRACT_ONLY", "low", f"文本过短 ({text_len} 字符)"

    # 手动 Claude 阅读
    if extraction_mode == "manual_claude":
        if text_len > 5000:
            return "PDF_TEXT_FULL", "medium", "Claude 手动阅读，内容完整"
        elif text_len > 1000:
            return "PDF_TEXT_PARTIAL", "medium", "Claude 手动阅读，部分内容"
        else:
            return "ABSTRACT_ONLY", "low", "Claude 仅提供摘要级笔记"

    # 自动提取 — 检查章节覆盖
    key_sections = ["abstract", "introduction", "method", "results", "discussion", "conclusion"]
    covered = sum(1 for s in key_sections if s in sections)
    has_method = "method" in sections or "data" in sections
    has_results = "results" in sections or "discussion" in sections or "conclusion" in sections

    # 全文标准: ≥15000 字符 或 ≥2000 英文词, 且覆盖 ≥3 类关键章节, 且含方法+结果
    has_min_length = text_len >= 15000 or word_count >= 2000
    has_enough_sections = covered >= 3

    if has_min_length and has_enough_sections and has_method and has_results:
        return (
            "PDF_TEXT_FULL",
            "high" if text_len > 50000 else "medium",
            f"全文自动提取，{text_len}字符/{word_count}词，覆盖{covered}类关键章节",
        )

    # 部分正文
    if text_len > 500:
        return (
            "PDF_TEXT_PARTIAL",
            "medium",
            f"已提取正文但未达全文标准 ({text_len}字符, {covered}类章节)",
        )

    return "ABSTRACT_ONLY", "low", f"正文不足 ({text_len}字符)"


# ═══════════════════════════════════════════════════════════════════
# 文本分块
# ═══════════════════════════════════════════════════════════════════

def _chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """将文本分成重叠块。"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

def ingest_pdf(
    pdf_path: str | Path,
    *,
    engine: str = "auto",
    output_dir: Optional[str | Path] = None,
    force: bool = False,
    force_ocr: bool = False,
    write_images: bool = False,
    max_pages: int = 200,
) -> Dict[str, Any]:
    """统一 PDF 摄入入口。

    整合三条旧路径:
      - pdf_extractor.py 的 6 级提取级联
      - fulltext_utils.py 的阅读等级判定
      - CLI 的元数据归档

    Args:
        pdf_path: PDF 文件路径
        engine: 提取引擎。auto=pymupdf4llm/fallback_text/manual_claude
        output_dir: 输出目录 (默认: data/pdf_library/processed/)
        force: 强制重新处理
        force_ocr: 强制 OCR 模式
        write_images: 是否写入页面图片
        max_pages: 最大处理页数

    Returns:
        dict with status, output_dir, char_count, chunks, confidence, ...
    """
    path = Path(pdf_path)
    if not path.exists():
        return {"status": "failed", "error": f"文件不存在: {pdf_path}"}

    # 输出目录
    if output_dir:
        out_root = Path(output_dir)
    else:
        out_root = DEFAULT_OUTPUT
    pdf_stem = path.stem
    pdf_out = out_root / pdf_stem

    # 检查是否已处理
    metadata_file = pdf_out / "metadata.json"
    if metadata_file.exists() and not force:
        try:
            meta = json.loads(metadata_file.read_text(encoding="utf-8"))
            return {"status": "skipped", "output_dir": str(pdf_out),
                    "metadata": meta, "reason": "already processed"}
        except Exception:
            pass

    pdf_out.mkdir(parents=True, exist_ok=True)

    # ── 提取 ──
    result = ExtractionResult()
    result.metadata["file"] = str(path)
    result.metadata["file_hash"] = _hash_file(path)
    result.metadata["file_size"] = path.stat().st_size
    result.metadata["engine_requested"] = engine

    if engine == "manual_claude":
        # 手动模式：跳过自动提取
        result.method = "manual_claude"
        result.error = "manual_claude 模式需单独导入 Claude 阅读产出"
        result.reading_level = "META_ONLY"
        result.confidence = "low"
    else:
        # ── 阶段 1: 文本提取 (级联) ──
        _run_extraction(result, path, engine, force_ocr)

        # ── 阶段 2: 页数统计 ──
        if not result.pages:
            try:
                import pymupdf
                doc = pymupdf.open(str(path))
                result.pages = doc.page_count
                doc.close()
            except Exception:
                pass

        # ── 阶段 3: 质量评估 ──
        result.char_count = len(result.text)
        result.word_count = _count_words(result.text)
        result.quality_score = _quality_score(result.text)

        # ── 阶段 4: 章节解析 ──
        if result.text:
            result.sections = _parse_sections(result.text)

        # ── 阶段 5: 阅读等级判定 ──
        extraction_mode = "automatic" if result.method != "manual_claude" else "manual_claude"
        result.reading_level, result.confidence, level_reason = _classify_reading_level(
            result.text, result.sections, result.method, extraction_mode
        )

        # ── 阶段 6: 中文质量检查 ──
        cn_quality = {"quality": "ok", "issues": []}
        if re.search(r'[一-鿿]', result.text) and len(result.text) > 100:
            cn_quality = _chinese_quality_check(result.text)
        if cn_quality["quality"] == "corrupted":
            if result.reading_level == "PDF_TEXT_FULL":
                result.reading_level = "PDF_TEXT_PARTIAL"
                result.confidence = "medium"
                level_reason += f"; 中文编码损坏: {'; '.join(cn_quality['issues'][:3])}"

        # ── 阶段 7: 分块 ──
        if result.text:
            result.chunks = _chunk_text(result.text)

    # ── 写入输出文件 ──
    _write_outputs(result, pdf_out, write_images, path)

    return {
        "status": "success" if result.text else ("failed" if result.error else "low_quality"),
        "output_dir": str(pdf_out),
        "char_count": result.char_count,
        "word_count": result.word_count,
        "chunks": len(result.chunks),
        "pages": result.pages,
        "method": result.method,
        "confidence": result.confidence,
        "reading_level": result.reading_level,
        "quality_score": round(result.quality_score, 2),
        "has_ocr": result.has_ocr,
        "has_tables": result.has_tables,
        "error": result.error,
        "warnings": result.warnings,
    }


def _run_extraction(
    result: ExtractionResult,
    path: Path,
    engine: str,
    force_ocr: bool,
) -> None:
    """运行提取级联。"""

    # 单引擎模式
    if engine == "pymupdf4llm":
        text, method, _ = _extract_pymupdf4llm(path)
        if text:
            result.text = _clean_text(text)
            result.method = method
        else:
            result.warnings.append(method)
        return

    if engine == "fallback_text":
        # pymupdf → pypdf
        text, method, pages = _extract_pymupdf(path)
        result.pages = pages
        if text:
            result.text = _clean_text(text)
            result.method = method
        else:
            result.warnings.append(method)
            text, method = _extract_pypdf(path)
            if text:
                result.text = _clean_text(text)
                result.method = method
            else:
                result.warnings.append(method)
        return

    # auto 模式 — 完整级联
    if not force_ocr:
        # 1a. pymupdf4llm (最佳)
        text, method, _ = _extract_pymupdf4llm(path)
        if text:
            result.text = _clean_text(text)
            result.method = method
        else:
            result.warnings.append(method)

        # 1b. pymupdf
        if not result.text:
            text, method, pages = _extract_pymupdf(path)
            result.pages = pages
            if text:
                result.text = _clean_text(text)
                result.method = method
            else:
                result.warnings.append(method)

        # 1c. pdfplumber (含表格)
        if not result.text:
            text, method, tables = _extract_pdfplumber(path)
            if text:
                result.text = _clean_text(text)
                result.method = method
                result.tables = tables
                result.has_tables = bool(tables)
            else:
                result.warnings.append(method)

        # 1d. pypdf (最轻兜底)
        if not result.text:
            text, method = _extract_pypdf(path)
            if text:
                result.text = _clean_text(text)
                result.method = method
            else:
                result.warnings.append(method)

    # OCR 阶段 (文本提取失败 或 强制 OCR)
    if not result.text or force_ocr:
        # easyocr (首选)
        text, method = _extract_easyocr(path, page_count=result.pages)
        if text:
            result.text = _clean_text(text)
            result.method = method
            result.has_ocr = True
        else:
            result.warnings.append(method)

        # tesseract (备选)
        if not result.text:
            text, method = _extract_tesseract(path, page_count=result.pages)
            if text:
                result.text = _clean_text(text)
                result.method = method
                result.has_ocr = True
            else:
                result.warnings.append(method)

    # 终极兜底: markitdown
    if not result.text:
        text, method = _extract_markitdown(path)
        if text:
            cleaned = _clean_text(text)
            if cleaned.count("\ufffd") <= max(5, len(cleaned) // 100):
                result.text = cleaned
                result.method = method
            else:
                result.warnings.append(f"{method} output contains excessive replacement characters")
        else:
            result.warnings.append(method)

    # 标记扫描件
    if _is_scanned(result.text, result.pages):
        result.warnings.append("疑似扫描件，建议 OCR")
        result.metadata["ocr_recommended"] = True


def _write_outputs(
    result: ExtractionResult,
    out_dir: Path,
    write_images: bool,
    source_path: Path,
) -> None:
    """写入输出文件，默认不把本机绝对路径写入可发布产物。"""

    # 仅保留文件名与哈希：绝对路径会暴露用户名、目录结构或研究项目名称。
    source_name = source_path.name

    # paper.md
    paper_md = out_dir / "paper.md"
    header = "<!--\n"
    header += f"  source: {source_name}\n"
    header += f"  method: {result.method}\n"
    header += f"  extraction_mode: {'manual_claude' if result.method == 'manual_claude' else 'automatic'}\n"
    header += f"  confidence: {result.confidence}\n"
    if result.method == "manual_claude":
        header += f"  manual_claude_used: true\n"
        header += "  disclaimer: 本文由 Claude 手动阅读生成，可能存在遗漏或理解偏差，仅供参考。\n"
    header += "-->\n\n"
    paper_md.write_text(header + result.text, encoding="utf-8")

    # metadata.json
    metadata = {
        "source_file": source_name,
        "source_path_redacted": True,
        "file_hash": result.metadata.get("file_hash", ""),
        "file_size": result.metadata.get("file_size", 0),
        "engine_requested": result.metadata.get("engine_requested", "auto"),
        "engine_used": result.method,
        "extraction_mode": "manual_claude" if result.method == "manual_claude" else "automatic",
        "confidence": result.confidence,
        "reading_level": result.reading_level,
        "char_count": result.char_count,
        "word_count": result.word_count,
        "pages": result.pages,
        "quality_score": round(result.quality_score, 2),
        "has_ocr": result.has_ocr,
        "has_tables": result.has_tables,
        "ocr_required": result.metadata.get("ocr_recommended", False),
        "manual_claude_used": result.method == "manual_claude",
        "sections": list(result.sections.keys()),
        "error": result.error,
        "warnings": result.warnings,
        "processed_at": datetime.now().isoformat(),
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # chunks.jsonl
    if result.chunks:
        with open(out_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
            for i, chunk in enumerate(result.chunks):
                f.write(json.dumps({"index": i, "text": chunk}, ensure_ascii=False) + "\n")

    # extraction_report.md
    report_lines = [
        "# Extraction Report\n",
        f"- **Source:** `{source_name}` (local path redacted)",
        f"- **Method:** {result.method}",
        f"- **Mode:** {'manual_claude' if result.method == 'manual_claude' else 'automatic'}",
        f"- **Confidence:** {result.confidence}",
        f"- **Reading Level:** {result.reading_level}",
        f"- **Characters:** {result.char_count}",
        f"- **Words:** {result.word_count}",
        f"- **Pages:** {result.pages}",
        f"- **Quality Score:** {result.quality_score:.2f}",
        f"- **OCR:** {result.has_ocr}",
        f"- **Tables:** {result.has_tables}",
        f"- **Sections:** {', '.join(result.sections.keys()) or 'none'}",
    ]
    if result.error:
        report_lines.append(f"- **Error:** {result.error}")
    if result.warnings:
        report_lines.append(f"- **Warnings:** {'; '.join(result.warnings)}")
    report_lines.append(f"\n## Text Preview\n\n```\n{result.text[:500]}\n```")
    (out_dir / "extraction_report.md").write_text("\n".join(report_lines), encoding="utf-8")


def ingest_dir(
    dir_path: str | Path,
    *,
    engine: str = "auto",
    output_dir: Optional[str | Path] = None,
    force: bool = False,
) -> List[Dict[str, Any]]:
    """批量摄入目录下所有 PDF。

    Args:
        dir_path: 包含 PDF 的目录路径
        engine: 提取引擎
        output_dir: 输出根目录
        force: 强制重新处理

    Returns:
        每篇 PDF 的结果字典列表
    """
    path = Path(dir_path)
    if not path.is_dir():
        return [{"status": "failed", "error": f"目录不存在: {dir_path}"}]

    pdf_files = sorted(path.glob("*.pdf")) + sorted(path.glob("*.PDF"))
    if not pdf_files:
        return [{"status": "failed", "error": f"目录中无 PDF: {dir_path}"}]

    results = []
    for pdf_file in pdf_files:
        result = ingest_pdf(pdf_file, engine=engine, output_dir=output_dir, force=force)
        results.append(result)

    return results


# ═══════════════════════════════════════════════════════════════════
# CLI (兼容旧 scripts/ingest_pdf.py 调用方式)
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="统一 PDF/图片 摄入管线")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--pdf", help="单篇 PDF 文件路径")
    group.add_argument("--dir", help="包含 PDF 的目录路径")
    parser.add_argument("--engine", default="auto",
                       choices=["auto", "pymupdf4llm", "fallback_text", "manual_claude"])
    parser.add_argument("--output", help="自定义输出目录")
    parser.add_argument("--force", action="store_true", help="强制重新处理")
    parser.add_argument("--force-ocr", action="store_true", help="强制 OCR")
    parser.add_argument("--write-images", action="store_true", help="写入页面图片")
    parser.add_argument("--list-engines", action="store_true", help="列出可用引擎并退出")
    args = parser.parse_args()

    if args.list_engines:
        available = list_available()
        print(f"可用引擎: {', '.join(available)}")
        print(f"模式: auto (级联全部), pymupdf4llm (单引擎), fallback_text (pymupdf+pypdf), manual_claude (手动)")
        sys.exit(0)

    if not args.pdf and not args.dir:
        parser.error("one of --pdf or --dir is required unless --list-engines is used")

    if args.pdf:
        print(f"Ingesting: {args.pdf}")
        print(f"Engine: {args.engine}")
        result = ingest_pdf(
            args.pdf, engine=args.engine, output_dir=args.output,
            force=args.force, force_ocr=args.force_ocr,
        )
        print(f"\nResult: {result.get('status')}")
        if result.get("status") in ("success", "low_quality"):
            print(f"  Output: {result.get('output_dir')}")
            print(f"  Method: {result.get('method')}")
            print(f"  Chars: {result.get('char_count', 0)}")
            print(f"  Chunks: {result.get('chunks', 0)}")
            print(f"  Confidence: {result.get('confidence', '?')}")
            print(f"  Reading Level: {result.get('reading_level', '?')}")
        else:
            print(f"  Error: {result.get('error', result.get('reason', '?'))}")

    elif args.dir:
        results = ingest_dir(args.dir, engine=args.engine, output_dir=args.output, force=args.force)
        success = sum(1 for r in results if r.get("status") in ("success", "low_quality"))
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        failed = sum(1 for r in results if r.get("status") == "failed")
        print(f"\nDone: {success} success, {skipped} skipped, {failed} failed")
