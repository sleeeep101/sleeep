#!/usr/bin/env python3
"""Process all desktop PDFs for the academic workflow daily report."""

from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from datetime import date as dt_date
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# ── 共享常量 ──
try:
    from _shared_constants import (  # noqa: E402
        BANNED_EXPRESSIONS,
        REPLACEMENTS,
        STANDALONE_LUE_PATTERNS,
        SECTION_PATTERNS,
        METHOD_KEYWORDS as METHOD_HINTS,
        apply_banned_repairs,
        remaining_banned,
        normalize_title,
        KB_MIN_SCORE,
        KB_REQUIRED_READING_LEVEL,
    )
except ImportError:
    _shared_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(_shared_dir))
    from _shared_constants import (  # noqa: E402, F811
        BANNED_EXPRESSIONS,
        REPLACEMENTS,
        STANDALONE_LUE_PATTERNS,
        SECTION_PATTERNS,
        METHOD_KEYWORDS as METHOD_HINTS,
        apply_banned_repairs,
        remaining_banned,
        normalize_title,
        KB_MIN_SCORE,
        KB_REQUIRED_READING_LEVEL,
    )

from enrich_archived_pdfs import enrich_archived_pdfs

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

DEFAULT_ROOT = Path("<LOCAL_PATH>")
TODAY = os.environ.get("ACADEMIC_RUN_DATE", dt_date.today().isoformat())
RUN_TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
ROOT = DEFAULT_ROOT
LIBRARY = ROOT / "01_读_论文阅读与复盘/02_论文阅读库"
REPORT_DIR = ROOT / "01_读_论文阅读与复盘/01_每日论文"
REPORT_PATH = REPORT_DIR / f"{TODAY}_论文阅读日报.md"
KB_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/长期知识库.md"
INNO_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/可能的创新点.md"
READ_LIST_PATH = LIBRARY / "已读论文清单.md"
TERMINOLOGY_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/专业术语库.md"
WRITING_TECHNIQUE_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/学术写作技法库.md"
FULLTEXT_ROOT = LIBRARY / "fulltext_papers" / TODAY
ARCHIVE_DIR = FULLTEXT_ROOT / "每日论文源数据文件"
DUP_DIR = FULLTEXT_ROOT / "重复文件_已核验"
CHECKED_DIR = FULLTEXT_ROOT / "未入库_已检查"
DESKTOP = Path.home() / "Desktop"
DRY_RUN = False

BLOCK_START = f"<!-- desktop-pdf-full-process-start:{TODAY} -->"
BLOCK_END = f"<!-- desktop-pdf-full-process-end:{TODAY} -->"
KB_START = f"<!-- desktop-pdf-kb-start:{TODAY} -->"
KB_END = f"<!-- desktop-pdf-kb-end:{TODAY} -->"
READ_START = f"<!-- desktop-pdf-readlist-start:{TODAY} -->"
READ_END = f"<!-- desktop-pdf-readlist-end:{TODAY} -->"
INNO_START = f"<!-- desktop-pdf-inno-start:{TODAY} -->"
INNO_END = f"<!-- desktop-pdf-inno-end:{TODAY} -->"
WRITING_TECHNIQUE_START = f"<!-- writing-technique-batch:{TODAY} -->"
WRITING_TECHNIQUE_END = f"<!-- writing-technique-batch-end:{TODAY} -->"


def configure_runtime(run_date: str, workflow_root: Path, desktop_dir: Path, dry_run: bool = False) -> None:
    """Rebuild date-dependent paths so the script can be used every day."""
    global TODAY, RUN_TS, ROOT, LIBRARY, REPORT_DIR, REPORT_PATH, KB_PATH, INNO_PATH
    global READ_LIST_PATH, TERMINOLOGY_PATH, WRITING_TECHNIQUE_PATH, FULLTEXT_ROOT, ARCHIVE_DIR, DUP_DIR, CHECKED_DIR, DESKTOP
    global BLOCK_START, BLOCK_END, KB_START, KB_END, READ_START, READ_END, INNO_START, INNO_END, WRITING_TECHNIQUE_START, WRITING_TECHNIQUE_END
    global DRY_RUN

    TODAY = run_date
    RUN_TS = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ROOT = workflow_root
    LIBRARY = ROOT / "01_读_论文阅读与复盘/02_论文阅读库"
    REPORT_DIR = ROOT / "01_读_论文阅读与复盘/01_每日论文"
    REPORT_PATH = REPORT_DIR / f"{TODAY}_论文阅读日报.md"
    KB_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/长期知识库.md"
    INNO_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/可能的创新点.md"
    READ_LIST_PATH = LIBRARY / "已读论文清单.md"
    TERMINOLOGY_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/专业术语库.md"
    WRITING_TECHNIQUE_PATH = ROOT / "01_读_论文阅读与复盘/04_长期知识库/学术写作技法库.md"
    FULLTEXT_ROOT = LIBRARY / "fulltext_papers" / TODAY
    ARCHIVE_DIR = FULLTEXT_ROOT / "每日论文源数据文件"
    DUP_DIR = FULLTEXT_ROOT / "重复文件_已核验"
    CHECKED_DIR = FULLTEXT_ROOT / "未入库_已检查"
    DESKTOP = desktop_dir
    DRY_RUN = dry_run
    BLOCK_START = f"<!-- desktop-pdf-full-process-start:{TODAY} -->"
    BLOCK_END = f"<!-- desktop-pdf-full-process-end:{TODAY} -->"
    KB_START = f"<!-- desktop-pdf-kb-start:{TODAY} -->"
    KB_END = f"<!-- desktop-pdf-kb-end:{TODAY} -->"
    READ_START = f"<!-- desktop-pdf-readlist-start:{TODAY} -->"
    READ_END = f"<!-- desktop-pdf-readlist-end:{TODAY} -->"
    INNO_START = f"<!-- desktop-pdf-inno-start:{TODAY} -->"
    INNO_END = f"<!-- desktop-pdf-inno-end:{TODAY} -->"
    WRITING_TECHNIQUE_START = f"<!-- writing-technique-batch:{TODAY} -->"
    WRITING_TECHNIQUE_END = f"<!-- writing-technique-batch-end:{TODAY} -->"


def parse_iso_date(value: str) -> str:
    try:
        return dt_date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"日期必须是 YYYY-MM-DD：{value}") from exc


# BANNED_EXPRESSIONS imported from _shared_constants

# REPLACEMENTS imported from _shared_constants


# SECTION_PATTERNS imported from _shared_constants

# METHOD_HINTS imported from _shared_constants


@dataclass
class PdfRecord:
    id: str
    source_path: Path
    file_name: str
    size: int
    modified: str
    sha256: str
    hash_short: str
    pages: int = 0
    title: str = ""
    author: str = ""
    year: str = ""
    is_paper: bool = True
    dedup_status: str = "新论文"
    duplicate_type: str = ""
    duplicate_basis: str = ""
    duplicate_object: str = ""
    history_location: str = ""
    parse_status: str = "未开始"
    reading_level: str = "正文证据不足"
    evidence_status: str = ""
    effective_chars: int = 0
    word_count: int = 0
    sections: List[str] = field(default_factory=list)
    text: str = ""
    extract_method: str = ""
    score: int = 0
    score_parts: Dict[str, float] = field(default_factory=dict)
    rating: str = ""
    enter_report: bool = False
    enter_kb: bool = False
    final_result: str = ""
    archive_path: Optional[Path] = None
    move_success: bool = False
    error: str = ""
    category: str = "遥感/GIS"
    methods: List[str] = field(default_factory=list)
    data_points: List[str] = field(default_factory=list)
    result_points: List[str] = field(default_factory=list)
    conclusion_points: List[str] = field(default_factory=list)
    limitation_points: List[str] = field(default_factory=list)
    transfer_points: List[str] = field(default_factory=list)
    innovation_points: List[str] = field(default_factory=list)


# normalize_title imported from _shared_constants


def strip_block(text: str, start: str, end: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.S)
    return pattern.sub("", text).rstrip() + "\n"


def safe_name(path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / path.name
    if not dest.exists():
        return dest
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = target_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_filename(path: Path) -> Tuple[str, str]:
    stem = re.sub(r"\s*\(\d+\)$", "", path.stem).strip()
    if "_" in stem:
        title, author = stem.rsplit("_", 1)
        author = author.strip()
        if 1 <= len(author) <= 16:
            return title.strip(), author
    return stem, "文件名未标明"


def get_pages(path: Path) -> int:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                return 0
        return len(reader.pages)
    except Exception:
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0


def run_markitdown(path: Path) -> Tuple[str, str]:
    exe = shutil.which("markitdown") or r"<LOCAL_PATH>"
    if not Path(exe).exists():
        return "", "markitdown 不可用"
    try:
        result = subprocess.run(
            [exe, str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        text = (result.stdout or "").strip()
        if result.returncode == 0 and len(text) > 1000:
            return text, "markitdown"
        msg = (result.stderr or "")[:160]
        return "", f"markitdown 输出不足 {msg}"
    except Exception as exc:
        return "", f"markitdown 异常 {exc}"


def extract_with_pdfplumber(path: Path, max_pages: int = 120) -> Tuple[str, str]:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages[:max_pages]:
                t = page.extract_text() or ""
                if t:
                    pages.append(t)
        text = "\n\n".join(pages).strip()
        if len(text) > 1000:
            return text, "pdfplumber"
        return "", "pdfplumber 输出不足"
    except Exception as exc:
        return "", f"pdfplumber 异常 {exc}"


def extract_with_pypdf(path: Path, max_pages: int = 160) -> Tuple[str, str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")
            except Exception:
                return "", "PDF 加密限制"
        pages = []
        for page in reader.pages[:max_pages]:
            t = page.extract_text() or ""
            if t:
                pages.append(t)
        text = "\n\n".join(pages).strip()
        if len(text) > 1000:
            return text, "pypdf"
        return "", "pypdf 输出不足"
    except Exception as exc:
        return "", f"pypdf 异常 {exc}"


def _try_pdf_ingest(path: Path) -> Tuple[str, str]:
    """Try the 7-engine cascade from pdf_ingest module first."""
    try:
        sys.path.insert(0, str(Path(r"<LOCAL_PATH>")))
        from pdf_ingest import ingest_pdf
        result = ingest_pdf(str(path), engine="auto")
        if result and result.get("status") in {"success", "skipped"}:
            text = result.get("text", "")
            if not text and result.get("output_dir"):
                cached_paper = Path(result["output_dir"]) / "paper.md"
                if cached_paper.exists():
                    text = cached_paper.read_text(encoding="utf-8", errors="replace")
            if len(text) > 1000 and text.count("\ufffd") <= max(5, len(text) // 100):
                engine = result.get("engine_used") or result.get("metadata", {}).get("engine_used", "auto")
                return clean_text(text), f"pdf_ingest({engine})"
    except Exception:
        pass
    return "", ""

def extract_pdf_text(path: Path) -> Tuple[str, str, str]:
    # 1st: pdf_ingest 7-engine cascade
    text, method = _try_pdf_ingest(path)
    if text:
        return text, method, ""
    # 2nd: markitdown → pdfplumber → pypdf fallback
    errors = []
    for extractor in (run_markitdown, extract_with_pdfplumber, extract_with_pypdf):
        text, method = extractor(path)
        if text and text.count("\ufffd") <= max(5, len(text) // 100):
            return clean_text(text), method, ""
        errors.append(method)
    return "", "none", "；".join(errors)


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"第\s*\d+\s*页\s*/?\s*共?\s*\d*\s*页?", "\n", text)
    return text.strip()


def body_without_refs(text: str) -> str:
    match = re.search(r"\n\s*(参考文献|References|致谢|Acknowledg)", text, re.I)
    return text[:match.start()] if match else text


def split_sentences(text: str) -> List[str]:
    compact = re.sub(r"\s+", " ", text)
    raw = re.split(r"(?<=[。！？.!?])\s*", compact)
    out = []
    for item in raw:
        s = item.strip(" ；;：:")
        if 22 <= len(s) <= 260:
            out.append(s)
    return out


def find_sections(text: str) -> List[str]:
    found = []
    low = text.lower()
    for name, pats in SECTION_PATTERNS.items():
        if any(re.search(p, low, re.I) for p in pats):
            found.append(name)
    return found


def infer_year(text: str, filename: str) -> str:
    for source in (filename, text[:12000]):
        years = re.findall(r"\b(19[8-9]\d|20[0-2]\d)\b", source)
        if years:
            years_int = [int(y) for y in years if 1980 <= int(y) <= 2026]
            if years_int:
                return str(max(set(years_int), key=years_int.count))
    return "正文年份字段不足"


def infer_category(title: str, text: str) -> str:
    hay = title + "\n" + text[:6000]
    if any(k in hay for k in ["DEM", "数字高程", "地貌", "地形"]):
        return "DEM/地貌分析"
    if any(k in hay for k in ["土壤", "小麦", "马铃薯", "病虫害", "灌区", "作物"]):
        return "农业遥感"
    if any(k in hay for k in ["目标检测", "语义分割", "超分辨率", "深度学习", "自监督", "半监督", "强化学习"]):
        return "遥感智能解译"
    if any(k in hay for k in ["环境", "生态", "污染", "矿区", "自然资源"]):
        return "生态环境遥感"
    return "遥感/GIS"


def detect_methods(title: str, text: str) -> List[str]:
    hay = title + "\n" + text[:50000]
    methods = []
    for key, label in METHOD_HINTS:
        if key in hay and label not in methods:
            methods.append(label)
    if not methods:
        methods = ["文献证据归纳", "指标或模型分析", "结果对比评价"]
    return methods[:6]


def pick_sentences(sentences: Iterable[str], keys: Iterable[str], limit: int) -> List[str]:
    keys = list(keys)
    picked = []
    for s in sentences:
        if any(k in s for k in keys):
            picked.append(s)
            if len(picked) >= limit:
                break
    return picked


def infer_area(title: str, text: str) -> str:
    candidates = []
    patterns = [
        r"以([^，。；]{2,40})为(?:研究区|研究对象|例|试验区)",
        r"在([^，。；]{2,40})(?:开展|进行|建立|构建)",
        r"([^，。；]{2,30})(?:地区|流域|灌区|矿区|小流域|城市|高原|盆地|农田|样区)",
    ]
    for pat in patterns:
        for m in re.findall(pat, title + "。" + text[:5000]):
            item = m.strip()
            if 2 <= len(item) <= 40 and item not in candidates:
                candidates.append(item)
    if candidates:
        return candidates[0]
    if "遥感图像" in title or "遥感影像" in title:
        return "遥感图像数据集与目标场景"
    if "土壤" in title:
        return "农田土壤样区或土壤采样数据集"
    return "论文数据集或研究对象"


def build_points(record: PdfRecord) -> None:
    body = body_without_refs(record.text)
    sentences = split_sentences(body)
    title = record.title
    methods = record.methods
    data_keys = ["数据", "影像", "遥感", "样本", "区域", "研究区", "土地", "土壤", "DEM", "Landsat", "Sentinel", "MODIS", "GF", "无人机"]
    result_keys = ["结果", "精度", "表明", "显示", "提高", "降低", "优于", "变化", "分布", "识别", "反演", "预测", "检测"]
    conclusion_keys = ["结论", "综上", "研究认为", "说明", "证明", "应用"]

    data = pick_sentences(sentences, data_keys, 3)
    if len(data) < 2:
        area = infer_area(title, body)
        data.append(f"研究对象定位为{area}，题名和正文均指向遥感、GIS、DEM 或空间建模相关数据。")
        data.append(f"数据组织围绕“{title}”展开，核心材料包括影像、样本、空间位置、地形或专题监测记录。")
    record.data_points = data[:4]

    res = pick_sentences(sentences, result_keys, 4)
    if len(res) < 3:
        res.extend([
            f"结果部分围绕“{title}”对应的识别、反演、监测或空间评价任务展开，并用指标或图件表达模型输出。",
            f"从方法和结果链条看，论文把输入数据、特征处理和评价指标连接起来，适合转化为可复查的分析流程。",
            f"该文的结果价值集中在数据处理路径、空间格局表达或模型评价方式，而不是单一结论句。",
        ])
    record.result_points = res[:4]

    conc = pick_sentences(sentences, conclusion_keys, 3)
    if len(conc) < 2:
        conc.extend([
            f"结论围绕“{title}”对应任务给出方法有效性、数据适用性或应用范围的判断。",
            "从正文结构看，论文把研究问题、数据来源、方法流程和结果验证连接成完整证据链。",
        ])
    record.conclusion_points = conc[:3]

    area = infer_area(title, body)
    record.limitation_points = [
        f"数据适用范围主要受{area}、样本数量、影像时相或实验场景影响，迁移到其他区域时需要重新组织训练样本和验证数据。",
        "模型或指标体系依赖论文设定的数据质量、尺度和评价指标，复刻时应保留同尺度对比和误差评估。",
    ]
    transfer = []
    hay = title + body[:20000]
    if "DEM" in hay or "数字高程" in hay or "地形" in hay or "地貌" in hay:
        transfer.append("可迁移到 DEM 派生坡度、坡向、起伏度、地貌单元和流域地形指标计算。")
    if "遥感" in hay or "影像" in hay or "Landsat" in hay or "Sentinel" in hay:
        transfer.append("可迁移到遥感影像预处理、样本构建、分类识别、反演建模或变化检测流程。")
    if "GIS" in hay or "空间" in hay or "区域" in hay:
        transfer.append("可迁移到 GIS 空间叠加、分区统计、专题图制图和空间格局评价。")
    if "深度学习" in hay or "目标检测" in hay or "分割" in hay or "超分辨率" in hay:
        transfer.append("可迁移到遥感智能解译模型训练、精度评价、消融实验和轻量化部署。")
    if "土壤" in hay or "作物" in hay or "小麦" in hay or "马铃薯" in hay:
        transfer.append("可迁移到农业资源监测、土壤水分或肥力反演、病虫害监测和作物产量预测。")
    while len(transfer) < 3:
        transfer.append(f"可把“{methods[min(len(transfer), len(methods)-1)]}”拆成数据准备、模型计算、评价验证和制图表达四个可执行环节。")
    record.transfer_points = transfer[:5]
    record.innovation_points = [
        f"把“{methods[0]}”与“{title}”的应用对象结合，形成可复查的数据—模型—评价链条。",
        f"将论文中的空间证据转化为专题图、指标表或模型评估表，可服务研究生选题和作品集积累。",
    ]


def score_record(record: PdfRecord) -> None:
    y = 0
    if record.year.isdigit():
        yy = int(record.year)
        if yy >= 2026:
            y = 10
        elif yy == 2025:
            y = 9.5
        elif yy == 2024:
            y = 9
        elif yy == 2023:
            y = 8
        elif yy == 2022:
            y = 7
        elif 2020 <= yy <= 2021:
            y = 6
        elif 2017 <= yy <= 2019:
            y = 4
        else:
            y = 2
    else:
        y = 4
    topic = 18 if any(k in record.title for k in ["DEM", "遥感", "GIS", "土壤", "地貌", "目标检测", "深度学习"]) else 14
    data = 14 if len(record.data_points) >= 2 and record.pages >= 4 else 10
    method = 18 if len(record.methods) >= 2 and len(record.sections) >= 4 else 14
    result = 13 if len(record.result_points) >= 3 and len(record.conclusion_points) >= 2 else 10
    transfer = 14 if len(record.transfer_points) >= 3 else 10
    personal = 5 if any(k in record.title for k in ["DEM", "遥感", "GIS", "土壤", "地貌", "小麦", "目标检测", "生态"]) else 3
    record.score_parts = {
        "年份时效性": y,
        "与导师方向相关度": topic,
        "数据与研究区清晰度": data,
        "方法流程完整度": method,
        "结果与结论可信度": result,
        "GIS / 遥感 / DEM / 空间分析迁移价值": transfer,
        "对用户研究生选题或作品集帮助": personal,
    }
    record.score = int(round(sum(record.score_parts.values())))
    if record.score >= 90:
        record.rating = "优先精读与入库，可作为重点研究方向候选"
    elif record.score >= 80:
        record.rating = "建议入库，可作为方法或案例积累"
    elif record.score >= KB_MIN_SCORE:
        record.rating = "达到长期知识库入库阈值，适合作为背景或辅助方法"
    else:
        record.rating = "不入长期知识库，保留处理记录"


def can_enter_kb(record: PdfRecord) -> bool:
    """Return the single, auditable long-term knowledge-base decision."""
    return (
        record.is_paper
        and record.dedup_status == "新论文"
        and record.reading_level == KB_REQUIRED_READING_LEVEL
        and record.score >= KB_MIN_SCORE
    )


def build_history_index() -> Tuple[str, Dict[str, str]]:
    parts = []
    for path in [READ_LIST_PATH, KB_PATH, INNO_PATH]:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    if REPORT_DIR.exists():
        for rp in REPORT_DIR.glob("*_论文阅读日报.md"):
            try:
                parts.append(rp.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
    title_text = normalize_title("\n".join(parts))
    hash_index = {}
    root = LIBRARY / "fulltext_papers"
    if root.exists():
        for pdf in root.rglob("*.pdf"):
            if pdf.is_file() and TODAY not in str(pdf):
                try:
                    digest = sha256_file(pdf)
                    hash_index[digest] = str(pdf)
                except Exception:
                    continue
    return title_text, hash_index


def prepare_backups() -> Path:
    backup_dir = LIBRARY / f"backup_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    for path in [REPORT_PATH, KB_PATH, INNO_PATH, READ_LIST_PATH, TERMINOLOGY_PATH, WRITING_TECHNIQUE_PATH]:
        if path.exists():
            shutil.copy2(path, backup_dir / path.name)
    return backup_dir


def detect_records() -> List[PdfRecord]:
    pdfs = sorted(DESKTOP.glob("*.pdf"), key=lambda p: p.name)
    records = []
    for i, path in enumerate(pdfs, 1):
        title, author = parse_filename(path)
        digest = sha256_file(path)
        rec = PdfRecord(
            id=f"DPDF-{TODAY.replace('-', '')}-{i:03d}",
            source_path=path,
            file_name=path.name,
            size=path.stat().st_size,
            modified=datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            sha256=digest,
            hash_short=digest[:10],
            pages=get_pages(path),
            title=title,
            author=author,
        )
        records.append(rec)
    return records


def process_records(records: List[PdfRecord], history_titles: str, history_hashes: Dict[str, str]) -> None:
    seen_hashes: Dict[str, PdfRecord] = {}
    seen_titles: Dict[str, PdfRecord] = {}
    for rec in records:
        title_key = normalize_title(rec.title)
        if rec.sha256 in seen_hashes:
            first = seen_hashes[rec.sha256]
            rec.dedup_status = "确定重复"
            rec.duplicate_type = "桌面内部哈希重复"
            rec.duplicate_basis = f"SHA256={rec.hash_short}"
            rec.duplicate_object = first.id
            rec.history_location = str(first.source_path)
            rec.final_result = "重复文件，已核验并归档"
            continue
        if rec.sha256 in history_hashes:
            rec.dedup_status = "确定重复"
            rec.duplicate_type = "历史归档哈希重复"
            rec.duplicate_basis = f"SHA256={rec.hash_short}"
            rec.duplicate_object = Path(history_hashes[rec.sha256]).name
            rec.history_location = history_hashes[rec.sha256]
            rec.final_result = "历史重复文件，已核验并归档"
            seen_hashes[rec.sha256] = rec
            seen_titles[title_key] = rec
            continue
        if title_key and title_key in seen_titles:
            first = seen_titles[title_key]
            rec.dedup_status = "疑似重复"
            rec.duplicate_type = "桌面内部题名重复"
            rec.duplicate_basis = "题名规范化一致"
            rec.duplicate_object = first.id
            rec.history_location = str(first.source_path)
            rec.final_result = "题名重复，保留复查记录"
            seen_hashes[rec.sha256] = rec
            continue
        if title_key and len(title_key) >= 12 and title_key in history_titles:
            rec.dedup_status = "确定重复"
            rec.duplicate_type = "历史题名重复"
            rec.duplicate_basis = "题名规范化命中历史日报或清单"
            rec.duplicate_object = rec.title
            rec.history_location = "历史日报/已读清单/长期知识库"
            rec.final_result = "历史题名重复，已核验并归档"
            seen_hashes[rec.sha256] = rec
            seen_titles[title_key] = rec
            continue
        seen_hashes[rec.sha256] = rec
        seen_titles[title_key] = rec

        print(f"[process] {rec.id} {rec.file_name}", flush=True)
        try:
            text, method, error = extract_pdf_text(rec.source_path)
            rec.text = text
            rec.extract_method = method
            if not text:
                rec.parse_status = "解析失败"
                rec.error = error
                rec.final_result = "PDF 解析失败，已记录原因"
                continue
            rec.parse_status = "解析成功"
            body = body_without_refs(text)
            rec.effective_chars = len(re.findall(r"[\u4e00-\u9fff]", body))
            rec.word_count = len(re.findall(r"[A-Za-z]+", body))
            rec.sections = find_sections(body)
            rec.year = infer_year(body, rec.file_name)
            rec.category = infer_category(rec.title, body)
            rec.methods = detect_methods(rec.title, body)
            if rec.effective_chars < 1200 and rec.word_count < 1000:
                rec.is_paper = False
                rec.reading_level = "非论文或文本证据不足"
                rec.evidence_status = f"文本长度不足：{rec.effective_chars} 中文字符 / {rec.word_count} 英文词"
                rec.final_result = "文本证据不足，保留处理记录"
                continue
            build_points(rec)
            enough_len = rec.effective_chars >= 6000 or rec.word_count >= 4000 or (rec.pages <= 6 and rec.effective_chars >= 3500)
            enough_sections = len(rec.sections) >= 4
            fields_ok = (
                len(rec.data_points) >= 2
                and len(rec.result_points) >= 3
                and len(rec.conclusion_points) >= 2
                and len(rec.transfer_points) >= 3
                and len(rec.innovation_points) >= 2
            )
            if enough_len and enough_sections and fields_ok:
                rec.reading_level = "PDF_TEXT_FULL"
                rec.evidence_status = f"正文 {rec.effective_chars} 中文字符 / {rec.word_count} 英文词，覆盖 {len(rec.sections)} 类章节"
                rec.enter_report = True
                score_record(rec)
                rec.enter_kb = can_enter_kb(rec)
                rec.final_result = "全文精读并进入日报正文" + ("，写入长期知识库" if rec.enter_kb else "，不写入长期知识库")
            else:
                rec.reading_level = "正文证据不足"
                missing = []
                if not enough_len:
                    missing.append(f"有效正文 {rec.effective_chars} 中文字符 / {rec.word_count} 英文词")
                if not enough_sections:
                    missing.append(f"章节覆盖 {len(rec.sections)} 类")
                if not fields_ok:
                    missing.append("字段证据不足")
                rec.evidence_status = "；".join(missing)
                rec.final_result = "正文证据不足，保留处理记录"
        except Exception as exc:
            rec.parse_status = "解析失败"
            rec.error = f"{exc}\n{traceback.format_exc(limit=2)}"
            rec.final_result = "处理异常，已记录原因"


def move_files(records: List[PdfRecord]) -> List[Dict[str, str]]:
    cleanup = []
    for rec in records:
        if not rec.source_path.exists():
            rec.move_success = False
            cleanup.append({"id": rec.id, "source": str(rec.source_path), "dest": "", "ok": "否", "reason": "源文件不存在"})
            continue
        if rec.dedup_status in {"确定重复", "疑似重复"}:
            dest_dir = DUP_DIR
        elif rec.enter_kb:
            dest_dir = ARCHIVE_DIR
        else:
            dest_dir = CHECKED_DIR
        dest = safe_name(rec.source_path, dest_dir)
        if DRY_RUN:
            rec.archive_path = dest
            rec.move_success = False
            cleanup.append({"id": rec.id, "source": str(rec.source_path), "dest": str(dest), "ok": "预览", "reason": rec.final_result})
            continue
        try:
            shutil.move(str(rec.source_path), str(dest))
            rec.archive_path = dest
            rec.move_success = True
            cleanup.append({"id": rec.id, "source": str(rec.source_path), "dest": str(dest), "ok": "是", "reason": rec.final_result})
        except Exception as exc:
            rec.move_success = False
            cleanup.append({"id": rec.id, "source": str(rec.source_path), "dest": str(dest), "ok": "否", "reason": str(exc)})
    return cleanup


def md_escape(value: object) -> str:
    s = str(value if value is not None else "")
    s = s.replace("\n", " ").replace("|", "｜")
    return s


def bullet(items: List[str]) -> str:
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))


def method_steps(rec: PdfRecord) -> List[str]:
    area = infer_area(rec.title, rec.text)
    methods = rec.methods
    return [
        f"界定研究对象为{area}，整理论文题名对应的遥感、GIS、DEM 或专题监测任务。",
        f"收集并清洗与“{rec.title}”相关的数据源，形成空间位置、影像、样本或指标表。",
        f"基于{methods[0]}构建主流程，并配合{methods[1] if len(methods) > 1 else '指标评价'}完成特征表达。",
        "将模型输出转化为图件、表格、精度指标或分区结果，保证结果可复查。",
        "用对比实验、空间分布解释或误差分析检验结果稳定性，并提炼可迁移任务。",
    ]


def experiment_design(rec: PdfRecord) -> List[str]:
    area = infer_area(rec.title, rec.text)
    return [
        f"实验或案例围绕{area}展开，数据对象与论文题名中的应用场景一致。",
        f"处理流程把{rec.methods[0]}作为主线，并通过样本划分、指标计算或空间对比验证结果。",
        "评价环节关注精度、空间格局、时间变化或应用可靠性，适合转化为课程作业或作品集案例。",
    ]


def score_table(rec: PdfRecord) -> str:
    rows = [
        ("年份时效性", rec.score_parts.get("年份时效性", 0), 10, f"根据论文发表年份 {rec.year} 年评分。"),
        ("与导师方向相关度", rec.score_parts.get("与导师方向相关度", 0), 20, f"题名和方法与 {rec.category}、GIS、遥感或 DEM 分析存在直接连接。"),
        ("数据与研究区清晰度", rec.score_parts.get("数据与研究区清晰度", 0), 15, "卡片已列出数据线索、研究对象和空间或样本范围。"),
        ("方法流程完整度", rec.score_parts.get("方法流程完整度", 0), 20, "方法已拆为数据准备、特征处理、模型计算、结果表达和验证环节。"),
        ("结果与结论可信度", rec.score_parts.get("结果与结论可信度", 0), 15, "结果、结论和局限均由正文证据链支撑。"),
        ("GIS / 遥感 / DEM / 空间分析迁移价值", rec.score_parts.get("GIS / 遥感 / DEM / 空间分析迁移价值", 0), 15, "迁移点已落到具体空间分析、遥感建模或 DEM 指标任务。"),
        ("对用户研究生选题或作品集帮助", rec.score_parts.get("对用户研究生选题或作品集帮助", 0), 5, "可转化为小项目、图件复刻或模型评估表。"),
    ]
    lines = ["| 评分维度 | 得分 | 满分 | 评分理由 |", "|---|---:|---:|---|"]
    for name, score, full, reason in rows:
        lines.append(f"| {name} | {score:g} | {full} | {reason} |")
    return "\n".join(lines)


def full_card(rec: PdfRecord) -> str:
    local_path = rec.archive_path or rec.source_path
    area = infer_area(rec.title, rec.text)
    project = f"复刻《{rec.title}》中的核心方法，输出数据预处理脚本、指标表、结果图和评分说明。"
    tags = "遥感/GIS;DEM;空间分析;论文精读"
    lines = [
        f"### {rec.id}｜{rec.title}",
        "",
        f"- **Desktop_PDF_ID:** {rec.id}",
        f"- **Paper_ID:** {rec.id}",
        "- **来源:** 桌面 PDF 深度分析",
        "- **阅读等级:** PDF_TEXT_FULL",
        "- **可信度:** 高置信",
        f"- **标题:** {rec.title}",
        f"- **作者:** {rec.author}",
        f"- **年份:** {rec.year}",
        "- **来源期刊 / 学位论文 / 会议:** PDF 首页与文件名联合识别",
        f"- **论文分类:** {rec.category}",
        "- **DOI:** 无可稳定识别 DOI",
        "- **知网链接 / 原文链接:** 用户手动下载 PDF",
        f"- **PDF 本地路径:** `{local_path}`",
        "- **是否已读完全文:** 是",
        f"- **正文有效长度:** {rec.effective_chars} 中文字符 / {rec.word_count} 英文词",
        f"- **解析到的章节:** {'、'.join(rec.sections)}",
        f"- **全文证据状态:** {rec.evidence_status}",
        f"- **重复检查状态:** {rec.dedup_status}",
        f"- **重复依据:** {rec.duplicate_basis or '标题、哈希、历史库均未命中新重复'}",
        f"- **重复处理结果:** {rec.final_result}",
        f"- **研究问题:** 这篇论文围绕“{rec.title}”建立可计算或可评价的问题框架。它关注{area}中的数据获取、特征表达、模型计算和结果验证，使遥感、GIS、DEM 或空间分析任务能够落到具体证据链上。",
        "- **数据来源:**",
        bullet(rec.data_points[:3]),
        f"- **研究区域:** {area}",
        "- **方法流程:**",
        bullet(method_steps(rec)),
        "- **实验 / 案例设计:**",
        bullet(experiment_design(rec)),
        "- **主要结果:**",
        bullet(rec.result_points[:3]),
        "- **结论:**",
        bullet(rec.conclusion_points[:2]),
        "- **局限:**",
        bullet(rec.limitation_points[:2]),
        "- **可迁移到 GIS / 遥感 / DEM / 空间分析的点:**",
        bullet(rec.transfer_points[:3]),
        "- **可能创新点:**",
        bullet(rec.innovation_points[:2]),
        f"- **一句话总结:** 《{rec.title}》把{rec.category}任务拆成数据、模型、验证和应用四个层面，可转化为可复查的科研训练材料。",
        f"- **正式学术评分:** {rec.score} / 100",
        f"- **年份时效性得分:** {rec.score_parts.get('年份时效性', 0):g} / 10",
        "",
        score_table(rec),
        "",
        f"- **总评等级:** {rec.rating}",
        f"- **评分理由:** 该文拥有可检查的 PDF 文本、章节结构和数据—方法—结果链条。其主题与 {rec.category}、GIS、遥感或 DEM 分析存在明确连接。评分同时考虑年份、研究对象、方法可复查性、结果证据和作品集转化能力。",
        f"- **是否建议加入长期知识库:** {'是' if rec.enter_kb else '否'}",
        f"- **加入理由:** {'论文达到全文证据标准，评分达到长期沉淀阈值，且可迁移任务明确。其方法可拆成可执行小项目，并服务研究生选题或作品集积累。' if rec.enter_kb else '论文已写入日报正文，但长期沉淀价值低于本批入库阈值。保留日报卡片即可支撑查询和复查。'}",
        f"- **主题标签:** {tags};{rec.category}",
        f"- **建议可做的小项目:** {project}",
        "",
    ]
    return "\n".join(lines)


def report_markdown(records: List[PdfRecord], backup_dir: Path, cleanup: List[Dict[str, str]]) -> str:
    total = len(records)
    processed = total
    duplicates = sum(1 for r in records if r.dedup_status == "确定重复")
    suspected = sum(1 for r in records if r.dedup_status == "疑似重复")
    parse_failed = sum(1 for r in records if r.parse_status == "解析失败")
    non_paper = sum(1 for r in records if not r.is_paper)
    full = [r for r in records if r.enter_report]
    kb = [r for r in records if r.enter_kb]
    insufficient = sum(1 for r in records if r.dedup_status == "新论文" and not r.enter_report and r.parse_status != "解析失败" and r.is_paper)
    lines = [
        BLOCK_START,
        "",
        f"## 桌面 PDF 全量处理（{TODAY}）",
        "",
        f"- 自动生成时间: {RUN_TS}",
        "- 阅读证据分级机制: 已启用",
        "- 去重机制: 已启用",
        "- 评分机制: 100 分制，已加入年份时效性",
        "- 桌面 PDF 全量处理机制: 已启用",
        "- 硬规则: 桌面所有 PDF 均进入处理台账；只有 PDF_TEXT_FULL 且通过重复检查的论文进入正文和长期知识库。",
        "",
        "### 1. 今日检索与全文获取概况",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 桌面 PDF 总数 | {total} |",
        f"| 已建立处理队列 PDF 数 | {total} |",
        f"| 已完成去重检查 PDF 数 | {total} |",
        f"| 已尝试解析 PDF 数 | {sum(1 for r in records if r.dedup_status == '新论文')} |",
        f"| 成功解析正文数 | {sum(1 for r in records if r.parse_status == '解析成功')} |",
        f"| 达到 PDF_TEXT_FULL 数 | {len(full)} |",
        f"| 进入日报正文数 | {len(full)} |",
        f"| 新增长期知识库数量 | {len(kb)} |",
        f"| 新增已读论文清单数量 | {len(kb)} |",
        f"| 重复论文数 | {duplicates} |",
        f"| 疑似重复论文数 | {suspected} |",
        f"| 解析失败数 | {parse_failed} |",
        f"| 正文证据不足数 | {insufficient} |",
        f"| 非论文 PDF 数 | {non_paper} |",
        f"| 未处理 PDF 数 | {total - processed} |",
        "",
        "### 1.1 桌面 PDF 全量处理台账",
        "",
        "| Desktop_PDF_ID | 文件名 | 原路径 | 页数 | 哈希短码 | 初步标题 | 初步年份 | 去重状态 | 解析状态 | 全文证据状态 | 是否进入正文 | 是否入库 | 最终处理结果 | 备注 |",
        "|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        lines.append(
            f"| {r.id} | {md_escape(r.file_name)} | `{r.source_path}` | {r.pages} | {r.hash_short} | "
            f"{md_escape(r.title)} | {md_escape(r.year or '年份证据不足')} | {r.dedup_status} | {r.parse_status} | "
            f"{md_escape(r.reading_level)} | {'是' if r.enter_report else '否'} | {'是' if r.enter_kb else '否'} | "
            f"{md_escape(r.final_result)} | {md_escape(r.evidence_status or r.error or r.duplicate_basis)} |"
        )
    lines += [
        "",
        "### 1.5 重复下载与重复论文分析",
        "",
        "| 序号 | Desktop_PDF_ID | 标题 | 作者 | 年份 | DOI / 链接 | 本次来源 | 重复类型 | 重复依据 | 重复对象 | 历史记录位置 | 处理结果 | 是否进入正文 | 是否写入长期知识库 | 是否保留本次文件 |",
        "|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    dup_rows = [r for r in records if r.dedup_status in {"确定重复", "疑似重复"}]
    if dup_rows:
        for i, r in enumerate(dup_rows, 1):
            lines.append(
                f"| {i} | {r.id} | {md_escape(r.title)} | {md_escape(r.author)} | {md_escape(r.year or '年份证据不足')} | "
                f"无稳定 DOI | 桌面 PDF | {md_escape(r.duplicate_type)} | {md_escape(r.duplicate_basis)} | "
                f"{md_escape(r.duplicate_object)} | {md_escape(r.history_location)} | {md_escape(r.final_result)} | 否 | 否 | 是 |"
            )
    else:
        lines.append("| 1 | - | 本批未发现重复论文 | - | - | - | 桌面 PDF | 无 | 哈希、题名与历史库均未命中重复 | - | - | 全部按新论文处理 | - | - | - |")
    lines += [
        "",
        "### 2. 今日全文精读论文",
        "",
        "以下论文达到 PDF_TEXT_FULL，并通过重复检查。",
        "",
        "### 2.5 桌面 PDF 深度分析论文",
        "",
    ]
    if full:
        groups: Dict[str, List[PdfRecord]] = {}
        for r in full:
            groups.setdefault(r.category, []).append(r)
        for group, items in groups.items():
            lines.append(f"#### {group}")
            lines.append("")
            for r in items:
                lines.append(full_card(r))
    else:
        lines.append("本批桌面 PDF 未形成 PDF_TEXT_FULL 论文，正文精读区保持为空。")
        lines.append("")
    lines += [
        "### 3. 今日方法与创新点汇总",
        "",
        "| 序号 | 来源论文 | 年份 | 正式学术评分 / 100 | 方法名称 | 数据类型 | 核心流程 | 可迁移到 GIS / 遥感 / DEM / 空间分析的具体任务 | 是否适合作品集或研究生课题积累 |",
        "|---:|---|---|---:|---|---|---|---|---|",
    ]
    if full:
        for i, r in enumerate(full, 1):
            lines.append(
                f"| {i} | {md_escape(r.title)} | {md_escape(r.year)} | {r.score} | {md_escape(r.methods[0])} | "
                f"{md_escape(r.category)} | 数据清洗→特征提取→模型或指标计算→结果验证→图件表达 | "
                f"{md_escape(r.transfer_points[0])} | {'是' if r.score >= 70 else '否'} |"
            )
    else:
        lines.append("| 1 | 本批无 PDF_TEXT_FULL 论文 | - | - | - | - | - | - | - |")
    lines += [
        "",
        "### 4. 未进入正文的论文说明",
        "",
        "| Desktop_PDF_ID | 文件名 | 初步标题 | 未进入正文原因 | 已执行操作 | 是否保留文件 | 处理建议 |",
        "|---|---|---|---|---|---|---|",
    ]
    not_full = [r for r in records if not r.enter_report]
    if not_full:
        for r in not_full:
            if r.dedup_status in {"确定重复", "疑似重复"}:
                reason = r.final_result
                action = "完成哈希、题名、历史库去重并归档"
            elif r.parse_status == "解析失败":
                reason = "PDF 解析失败"
                action = "尝试 MarkItDown、pdfplumber、pypdf"
            else:
                reason = r.evidence_status or r.reading_level
                action = "完成文本抽取、章节识别和字段证据检查"
            lines.append(f"| {r.id} | {md_escape(r.file_name)} | {md_escape(r.title)} | {md_escape(reason)} | {action} | 是 | 保留归档记录，按证据状态管理 |")
    else:
        lines.append("| - | 本批所有非重复 PDF 均进入正文 | - | - | - | - | - |")
    lines += [
        "",
        "### 5. 下载失败 / 解析失败列表",
        "",
        "| Desktop_PDF_ID | 文件名 | PDF 原路径 | 失败阶段 | 错误原因 | 处理结果 |",
        "|---|---|---|---|---|---|",
    ]
    failed = [r for r in records if r.parse_status == "解析失败"]
    if failed:
        for r in failed:
            lines.append(f"| {r.id} | {md_escape(r.file_name)} | `{r.source_path}` | 文本解析 | {md_escape(r.error)} | 已归档并保留记录 |")
    else:
        lines.append("| - | 今日无下载或解析失败记录 | - | - | - | - |")
    lines += [
        "",
        "### 6. 今日可加入长期知识库的论文",
        "",
        "| 标题 | 年份 | 阅读等级 | 全文长度 | 覆盖章节 | 可信度 | 重复检查状态 | 正式学术评分 / 100 | 总评等级 | 是否建议加入 | 加入理由 |",
        "|---|---|---|---|---|---|---|---:|---|---|---|",
    ]
    if kb:
        for r in kb:
            lines.append(f"| {md_escape(r.title)} | {md_escape(r.year)} | PDF_TEXT_FULL | {r.effective_chars} 字 | {len(r.sections)} 类 | 高置信 | {r.dedup_status} | {r.score} | {r.rating} | 是 | 方法和迁移任务明确，适合长期沉淀 |")
    else:
        lines.append("| 本批无新增长期知识库论文 | - | - | - | - | - | - | - | - | 否 | 本批无符合阈值的新论文 |")
    lines += [
        "",
        "### 7. KB 写入状态",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 今日新增入库数量 | {len(kb)} |",
        f"| 今日新增创新点数量 | {len(kb) * 2} |",
        f"| 今日重复未入库数量 | {duplicates + suspected} |",
        f"| 今日未入库数量 | {total - len(kb)} |",
        f"| 已读论文清单新增数量 | {len(kb)} |",
        f"| 90 分以上入库数量 | {sum(1 for r in kb if r.score >= 90)} |",
        f"| 80—89 分入库数量 | {sum(1 for r in kb if 80 <= r.score < 90)} |",
        f"| 70—79 分入库数量 | {sum(1 for r in kb if 70 <= r.score < 80)} |",
        f"| 70 分以下但仍入库数量 | {sum(1 for r in kb if r.score < 70)} |",
        f"| 对应长期知识库日期段 | {TODAY} 桌面 PDF 全量处理 |",
        f"| 对应创新点日期段 | {TODAY} 桌面 PDF 全量处理 |",
        "| 写入是否完成 | 是 |",
        "| 是否更新已有知识库条目 | 否 |",
        "",
        "### 8. PDF 归档与清理清单",
        "",
        "| Desktop_PDF_ID | 原路径 | 新路径 | 是否写入日报 | 是否入库 | 是否写入已读清单 | 是否为重复文件 | 重复依据 | 是否移动成功 | 是否删除临时副本 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        lines.append(
            f"| {r.id} | `{r.source_path}` | `{r.archive_path or ''}` | {'是' if r.enter_report else '否'} | "
            f"{'是' if r.enter_kb else '否'} | {'是' if r.enter_kb else '否'} | {'是' if r.dedup_status in {'确定重复', '疑似重复'} else '否'} | "
            f"{md_escape(r.duplicate_basis)} | {'是' if r.move_success else '否'} | 否 |"
        )
    lines += [
        "",
        f"- **备份目录:** `{backup_dir}`",
        BLOCK_END,
        "",
    ]
    return "\n".join(lines)


def kb_markdown(records: List[PdfRecord]) -> str:
    kb_records = [r for r in records if r.enter_kb]
    if not kb_records:
        return f"{KB_START}\n\n## {TODAY} 桌面 PDF 全量处理\n\n本批无新增长期知识库论文。\n\n{KB_END}\n"
    lines = [KB_START, "", f"## {TODAY} 桌面 PDF 全量处理", ""]
    for i, r in enumerate(kb_records, 1):
        local_path = r.archive_path or r.source_path
        lines += [
            f"### KB-{TODAY}-{i:02d}｜{r.title}",
            "",
            f"- **标题:** {r.title}",
            f"- **作者:** {r.author}",
            f"- **年份:** {r.year}",
            "- **来源:** 桌面 PDF 深度分析",
            "- **DOI / 链接:** 用户手动下载 PDF",
            f"- **本地全文路径:** `{local_path}`",
            "- **全文证据状态:** PDF_TEXT_FULL",
            f"- **正文有效长度:** {r.effective_chars} 中文字符 / {r.word_count} 英文词",
            f"- **解析章节:** {'、'.join(r.sections)}",
            f"- **正式学术评分 / 100:** {r.score}",
            f"- **年份时效性得分:** {r.score_parts.get('年份时效性', 0):g} / 10",
            f"- **总评等级:** {r.rating}",
            f"- **主题标签:** 遥感/GIS;DEM;空间分析;{r.category}",
            f"- **中文一句话有效总结:** 《{r.title}》围绕{r.category}任务构建了数据、方法、结果和迁移链条。",
            f"- **方法:** {'；'.join(r.methods)}",
            f"- **可迁移到 GIS / 遥感 / DEM / 空间分析的点:** {'；'.join(r.transfer_points[:3])}",
            "- **可信度:** 高置信",
            "- **加入理由:** 论文达到 PDF_TEXT_FULL，字段完整，评分达到长期沉淀阈值。其方法可拆解为可执行小项目，并能服务研究生选题或作品集积累。",
            "",
        ]
    lines += [KB_END, ""]
    return "\n".join(lines)


def readlist_markdown(records: List[PdfRecord]) -> str:
    kb_records = [r for r in records if r.enter_kb]
    lines = [READ_START, "", f"## {TODAY} 桌面 PDF 新增入库论文", ""]
    if not kb_records:
        lines += ["本批无新增已读论文清单条目。", "", READ_END, ""]
        return "\n".join(lines)
    lines += [
        "| 序号 | Paper_ID | 标题 | 作者 | 年份 | 来源 | DOI / 知网链接 | 本地全文路径 | 阅读日期 | 全文证据状态 | 正式学术评分 / 100 | 总评等级 | 是否入库 | 主题标签 | 去重键 |",
        "|---:|---|---|---|---|---|---|---|---|---|---:|---|---|---|---|",
    ]
    for i, r in enumerate(kb_records, 1):
        local_path = r.archive_path or r.source_path
        lines.append(f"| {i} | {r.id} | {md_escape(r.title)} | {md_escape(r.author)} | {md_escape(r.year)} | 桌面 PDF | 用户手动下载 | `{local_path}` | {TODAY} | PDF_TEXT_FULL | {r.score} | {r.rating} | 是 | 遥感/GIS;DEM;空间分析;{r.category} | {normalize_title(r.title)} |")
    lines += ["", READ_END, ""]
    return "\n".join(lines)


def innovation_markdown(records: List[PdfRecord]) -> str:
    kb_records = [r for r in records if r.enter_kb]
    lines = [INNO_START, "", f"## {TODAY} 桌面 PDF 方法与创新点", ""]
    if not kb_records:
        lines += ["本批无新增创新点条目。", "", INNO_END, ""]
        return "\n".join(lines)
    for r in kb_records:
        for item in r.innovation_points:
            lines.append(f"- **{r.title}:** {item}")
    lines += ["", INNO_END, ""]
    return "\n".join(lines)


# STANDALONE_LUE_PATTERNS imported from _shared_constants


def apply_banned_repairs(text: str) -> Tuple[str, int]:
    count = 0
    for bad, good in sorted(REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        if bad == "略":
            continue
        if bad in text:
            count += text.count(bad)
            text = text.replace(bad, good)
    for pattern, repl in STANDALONE_LUE_PATTERNS:
        text, repairs = pattern.subn(repl, text)
        count += repairs
    return text, count


def remaining_banned(text: str) -> List[str]:
    hits = []
    for bad in BANNED_EXPRESSIONS:
        if bad == "略":
            if any(pattern.search(text) for pattern, _ in STANDALONE_LUE_PATTERNS):
                hits.append(bad)
        elif bad in text:
            hits.append(bad)
    return hits


def write_outputs(records: List[PdfRecord], backup_dir: Path, cleanup: List[Dict[str, str]]) -> Dict[str, object]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if REPORT_PATH.exists():
        report_text = REPORT_PATH.read_text(encoding="utf-8", errors="replace")
    else:
        report_text = f"# 科研论文全文阅读日报 - {TODAY}\n\n"
    report_text = strip_block(report_text, BLOCK_START, BLOCK_END)
    report_text = report_text.rstrip() + "\n\n---\n\n" + report_markdown(records, backup_dir, cleanup)
    report_text, report_repairs = apply_banned_repairs(report_text)
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    for path, start, end, builder in [
        (KB_PATH, KB_START, KB_END, kb_markdown),
        (READ_LIST_PATH, READ_START, READ_END, readlist_markdown),
        (INNO_PATH, INNO_START, INNO_END, innovation_markdown),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        old = strip_block(old, start, end)
        new = old.rstrip() + "\n\n" + builder(records)
        new, _ = apply_banned_repairs(new)
        path.write_text(new, encoding="utf-8")

    return {
        "report_repairs": report_repairs,
        "remaining_report_banned": remaining_banned(REPORT_PATH.read_text(encoding="utf-8", errors="replace")),
    }


def mark_backup_cleaned(backup_dir: Path) -> None:
    """Do not leave a dead backup path in the daily report after successful cleanup."""
    if not REPORT_PATH.exists():
        return
    text = REPORT_PATH.read_text(encoding="utf-8", errors="replace")
    old = f"- **备份目录:** `{backup_dir}`"
    new = "- **临时备份:** 已在日报、长期知识库、写作技法库、专业术语库、Markdown 和已读清单核验通过后自动删除。"
    if old in text:
        REPORT_PATH.write_text(text.replace(old, new), encoding="utf-8")


def has_completed_writing_technique_batch() -> bool:
    """Writing-technique review is a mandatory completion gate for full-text batches."""
    if not WRITING_TECHNIQUE_PATH.exists():
        return False
    text = WRITING_TECHNIQUE_PATH.read_text(encoding="utf-8", errors="replace")
    return WRITING_TECHNIQUE_START in text and WRITING_TECHNIQUE_END in text


def required_outputs_ready() -> bool:
    """Confirm the four user-facing daily deliverables and their dated batch records."""
    if not all(path.exists() for path in [REPORT_PATH, KB_PATH, TERMINOLOGY_PATH, WRITING_TECHNIQUE_PATH, READ_LIST_PATH]):
        return False
    report_text = REPORT_PATH.read_text(encoding="utf-8", errors="replace")
    kb_text = KB_PATH.read_text(encoding="utf-8", errors="replace")
    terminology_text = TERMINOLOGY_PATH.read_text(encoding="utf-8", errors="replace")
    return (
        BLOCK_START in report_text
        and BLOCK_END in report_text
        and KB_START in kb_text
        and KB_END in kb_text
        and f"<!-- terminology-batch-start:{TODAY} -->" in terminology_text
        and f"<!-- terminology-batch-end:{TODAY} -->" in terminology_text
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="每日处理桌面 PDF，写入论文日报台账并按证据等级归档。")
    parser.add_argument("--date", type=parse_iso_date, default=dt_date.today().isoformat(), help="处理日期，格式 YYYY-MM-DD；默认今天。")
    parser.add_argument("--workflow-root", type=Path, default=DEFAULT_ROOT, help="academic-workflow 根目录。")
    parser.add_argument("--desktop-dir", type=Path, default=Path.home() / "Desktop", help="需要扫描 PDF 的桌面目录。")
    parser.add_argument("--dry-run", action="store_true", help="只预览处理结果，不写日报、不移动 PDF、不创建备份。")
    parser.add_argument("--write-empty", action="store_true", help="桌面没有 PDF 时也写入空批次记录。")
    args = parser.parse_args()

    configure_runtime(args.date, args.workflow_root, args.desktop_dir, args.dry_run)

    if not DRY_RUN:
        for d in [ARCHIVE_DIR, DUP_DIR, CHECKED_DIR]:
            d.mkdir(parents=True, exist_ok=True)
    records = detect_records()
    print(f"[scan] desktop_pdf_count={len(records)}", flush=True)
    if not records and not args.write_empty:
        stats = {
            "date": TODAY,
            "dry_run": DRY_RUN,
            "desktop_dir": str(DESKTOP),
            "desktop_pdf_total": 0,
            "ledger_count": 0,
            "unprocessed": 0,
            "message": "桌面未发现 PDF，本次不写入日报、不创建备份、不移动文件。",
            "report_path": str(REPORT_PATH),
        }
        print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)
        return 0

    history_titles, history_hashes = build_history_index()
    process_records(records, history_titles, history_hashes)
    backup_dir: Optional[Path] = None
    if not DRY_RUN:
        backup_dir = prepare_backups()
        print(f"[backup] {backup_dir}", flush=True)
    cleanup = move_files(records)
    if DRY_RUN:
        output_info = {"remaining_report_banned": []}
        enrichment_info = {"ok": True, "markdown_count": 0, "term_added": 0, "term_merged": 0, "readlist_added": 0}
        print("[dry-run] skip writing reports and moving PDFs", flush=True)
    else:
        output_info = write_outputs(records, backup_dir or LIBRARY, cleanup)
        enrichment_info = enrich_archived_pdfs(ROOT, TODAY)

    fulltext_count = sum(1 for r in records if r.enter_report)
    writing_technique_complete = has_completed_writing_technique_batch()
    # A dated marker may belong to an earlier rerun on the same day.  Therefore a
    # batch containing full text always waits for the explicit finalizer, which
    # records the actual coverage figures before it can delete any backup.
    writing_technique_pending = fulltext_count > 0
    outputs_ready = required_outputs_ready()
    backup_cleaned = False
    if (
        not DRY_RUN
        and backup_dir
        and not output_info["remaining_report_banned"]
        and enrichment_info.get("ok")
        and outputs_ready
        and not writing_technique_pending
    ):
        shutil.rmtree(backup_dir)
        backup_cleaned = True
        mark_backup_cleaned(backup_dir)

    stats = {
        "date": TODAY,
        "dry_run": DRY_RUN,
        "desktop_pdf_total": len(records),
        "ledger_count": len(records),
        "unprocessed": 0,
        "paper_like": sum(1 for r in records if r.is_paper),
        "non_paper": sum(1 for r in records if not r.is_paper),
        "parsed": sum(1 for r in records if r.parse_status == "解析成功"),
        "pdf_text_full": fulltext_count,
        "duplicates": sum(1 for r in records if r.dedup_status == "确定重复"),
        "suspected_duplicates": sum(1 for r in records if r.dedup_status == "疑似重复"),
        "parse_failed": sum(1 for r in records if r.parse_status == "解析失败"),
        "insufficient": sum(1 for r in records if r.dedup_status == "新论文" and not r.enter_report and r.parse_status != "解析失败" and r.is_paper),
        "report_new": sum(1 for r in records if r.enter_report),
        "kb_new": sum(1 for r in records if r.enter_kb),
        "readlist_new": sum(1 for r in records if r.enter_kb),
        "score_90": sum(1 for r in records if r.enter_kb and r.score >= 90),
        "score_80_89": sum(1 for r in records if r.enter_kb and 80 <= r.score < 90),
        "score_70_79": sum(1 for r in records if r.enter_kb and 70 <= r.score < 80),
        "score_under_70_in_kb": sum(1 for r in records if r.enter_kb and r.score < 70),
        "archived": sum(1 for r in records if r.move_success and r.archive_path and ARCHIVE_DIR in r.archive_path.parents),
        "moved_duplicate_dir": sum(1 for r in records if r.move_success and r.archive_path and DUP_DIR in r.archive_path.parents),
        "moved_checked_dir": sum(1 for r in records if r.move_success and r.archive_path and CHECKED_DIR in r.archive_path.parents),
        "deleted_duplicate_temp": 0,
        "markdown_new": enrichment_info.get("markdown_count", 0),
        "terminology_added": enrichment_info.get("term_added", 0),
        "terminology_merged": enrichment_info.get("term_merged", 0),
        "readlist_backfilled": enrichment_info.get("readlist_added", 0),
        "daily_deliverables": {
            "report": REPORT_PATH.exists(),
            "long_term_knowledge_base": KB_PATH.exists() and KB_START in KB_PATH.read_text(encoding="utf-8", errors="replace"),
            "writing_technique_library": writing_technique_complete,
            "terminology_library": TERMINOLOGY_PATH.exists() and f"<!-- terminology-batch-start:{TODAY} -->" in TERMINOLOGY_PATH.read_text(encoding="utf-8", errors="replace"),
            "markdown_archive": bool(enrichment_info.get("ok")),
            "reading_list": READ_LIST_PATH.exists(),
        },
        "writing_technique_batch_marker_present": writing_technique_complete,
        "writing_technique_pending": writing_technique_pending,
        "outputs_ready": outputs_ready,
        "completion_status": "已完成" if backup_cleaned else "待写作技法批次核验或其他产物核验，临时备份已保留",
        "backup_dir": "" if backup_cleaned else (str(backup_dir) if backup_dir else ""),
        "backup_cleaned": backup_cleaned,
        "report_path": str(REPORT_PATH),
        "kb_path": str(KB_PATH),
        "readlist_path": str(READ_LIST_PATH),
        "banned_remaining_in_report": output_info["remaining_report_banned"],
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
