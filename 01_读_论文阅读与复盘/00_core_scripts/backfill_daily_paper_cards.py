#!/usr/bin/env python3
"""Backfill daily paper report cards without score filtering.

默认处理今天；可用 --days 或 --start-date/--end-date 回补最近日报。
"""

from __future__ import annotations

import os
from pathlib import Path as _BootstrapPath

# This script was saved once with UTF-8 text decoded as Windows-1252.  Keep a
# small compatibility bootstrap so the existing script can execute correctly
# while retaining its historical source file and command-line interface.
if os.environ.get("ACADEMIC_CARD_SCRIPT_UTF8_FIXED") != "1":
    _source_path = _BootstrapPath(__file__)
    _source_text = _source_path.read_text(encoding="utf-8")
    try:
        _fixed_text = _source_text.encode("cp1252").decode("utf-8")
    except UnicodeError:
        _fixed_text = _source_text
    if _fixed_text != _source_text:
        os.environ["ACADEMIC_CARD_SCRIPT_UTF8_FIXED"] = "1"
        exec(compile(_fixed_text, str(_source_path), "exec"), {"__name__": __name__, "__file__": __file__})
        raise SystemExit(0)

import argparse
import json
import re
import sys
from datetime import date as dt_date
from datetime import timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts"
REPORT_DIR = ROOT / "01_读_论文阅读与复盘/01_每日论文"
FULLTEXT_ROOT = ROOT / "01_读_论文阅读与复盘/02_论文阅读库/fulltext_papers"
PAPER_SOURCES = ROOT / "01_读_论文阅读与复盘/02_论文阅读库/paper_sources"

sys.path.insert(0, str(SCRIPTS))
from fulltext_utils import (  # noqa: E402
    chinese_text_quality_check,
    extract_text_from_html,
    extract_text_from_pdf,
    parse_fulltext_sections,
)

# ── 共享常量 ──
_shared_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_shared_dir))
try:
    from _shared_constants import (  # noqa: E402
        BANNED_EXPRESSIONS,
        REPLACEMENTS,
        STANDALONE_LUE_PATTERNS,
        METHOD_KEYWORDS,
        DATA_HINTS,
        RESULT_HINTS,
        LIMIT_HINTS,
        SECTION_HEADINGS,
        apply_banned_repairs,
        remaining_banned,
    )
except ImportError:
    # Fallback: define minimal versions
    BANNED_EXPRESSIONS = []
    REPLACEMENTS = {}
    STANDALONE_LUE_PATTERNS = []
    METHOD_KEYWORDS = []
    DATA_HINTS = []
    RESULT_HINTS = []
    LIMIT_HINTS = []
    SECTION_HEADINGS = {}
    def apply_banned_repairs(text): return (text, 0)
    def remaining_banned(text): return []


DEFAULT_SOURCE_MODE = "checked"


# METHOD_KEYWORDS imported from _shared_constants


# DATA_HINTS imported from _shared_constants

# RESULT_HINTS imported from _shared_constants

# LIMIT_HINTS imported from _shared_constants

# SECTION_HEADINGS imported from _shared_constants


# BANNED_EXPRESSIONS / REPLACEMENTS imported from _shared_constants


# STANDALONE_LUE_PATTERNS imported from _shared_constants


def parse_iso_date(value: str) -> dt_date:
    try:
        return dt_date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"日期必须是 YYYY-MM-DD：{value}") from exc


def resolve_dates(args: argparse.Namespace) -> List[str]:
    if args.start_date or args.end_date:
        start = args.start_date or args.end_date
        end = args.end_date or args.start_date
        if start > end:
            raise SystemExit("--start-date 不能晚于 --end-date")
        days = (end - start).days
        return [(start + timedelta(days=i)).isoformat() for i in range(days + 1)]
    if args.days:
        end = args.date or dt_date.today()
        start = end - timedelta(days=args.days - 1)
        return [(start + timedelta(days=i)).isoformat() for i in range(args.days)]
    return [(args.date or dt_date.today()).isoformat()]


# apply_banned_repairs imported from _shared_constants


# remaining_banned imported from _shared_constants


def normalize(s: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", s).lower()


def strip_existing_block(text: str, date: str) -> str:
    start = f"<!-- 论文日报卡片补齐开始:{date} -->"
    end = f"<!-- 论文日报卡片补齐结束:{date} -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.S)
    return pattern.sub("", text).rstrip() + "\n"


def next_section_number(text: str) -> int:
    nums = [int(m.group(1)) for m in re.finditer(r"^##\s+(\d+)(?:\.|\s)", text, re.M)]
    return (max(nums) + 1) if nums else 1


def load_metadata(date: str) -> List[Dict]:
    out = []
    base = PAPER_SOURCES / date
    if not base.exists():
        return out
    for path in base.rglob("metadata.json"):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            meta["_metadata_dir"] = str(path.parent)
            out.append(meta)
        except Exception:
            continue
    return out


def title_from_path(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"^[0-9a-f]{12}_", "", stem, flags=re.I)
    stem = stem.replace("__", "：")
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip()
    if re.search(r"[\u4e00-\u9fff]", stem) and " " not in stem:
        return stem
    if re.search(r"[\u4e00-\u9fff]", path.stem):
        raw = path.stem
        raw = re.sub(r"^[0-9a-f]{12}_", "", raw, flags=re.I)
        if "_" in raw:
            raw = raw.rsplit("_", 1)[0]
        return raw
    return stem


def author_from_path(path: Path) -> str:
    stem = path.stem
    if "_" in stem and re.search(r"[\u4e00-\u9fff]", stem):
        tail = stem.rsplit("_", 1)[-1].strip()
        if 1 <= len(tail) <= 8:
            return tail
    return "未识别"


def find_metadata(path: Path, metas: List[Dict]) -> Optional[Dict]:
    title = normalize(title_from_path(path))
    best = None
    best_score = 0
    for meta in metas:
        mt = normalize(meta.get("title", ""))
        if not mt:
            continue
        overlap = len(set(title) & set(mt))
        denom = max(1, min(len(set(title)), len(set(mt))))
        score = overlap / denom
        if title and (title in mt or mt in title):
            score = 1.0
        if score > best_score:
            best_score = score
            best = meta
    return best if best_score >= 0.55 else None


def list_target_files(date: str, report_text: str, source_mode: str = DEFAULT_SOURCE_MODE) -> List[Path]:
    base = FULLTEXT_ROOT / date
    if not base.exists():
        return []
    files = sorted(
        [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".html"}],
        key=lambda p: str(p),
    )
    prefixed = [p for p in files if re.match(r"^[0-9a-f]{12}_", p.name, re.I)]
    checked = [p for p in files if "未入库" in str(p)]
    if source_mode == "all":
        return files
    if source_mode == "prefixed":
        return prefixed
    if source_mode == "checked":
        return checked
    if prefixed:
        return prefixed
    if checked:
        return checked
    return files


def clean_text(text: str, max_chars: int = 160000) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars]


def split_sentences(text: str) -> List[str]:
    compact = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[。！？.!?])\s+", compact)
    out = []
    for s in parts:
        s = s.strip(" ;；:：")
        if 24 <= len(s) <= 260:
            out.append(s)
    return out


def pick_sentences(sentences: Iterable[str], hints: List[str], limit: int = 3) -> List[str]:
    picked = []
    for s in sentences:
        low = s.lower()
        if any(h.lower() in low for h in hints):
            if s not in picked:
                picked.append(s)
        if len(picked) >= limit:
            break
    return picked


def extract_section_text(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        clean = line.strip()
        if not clean or len(clean) > 90:
            continue
        low = clean.lower()
        for name, patterns in SECTION_HEADINGS.items():
            for pat in patterns:
                if re.match(rf"^\s*(\d+[\.\s、-]*)?{pat}\b", low, re.I):
                    hits.append((i, name))
                    break
            else:
                continue
            break
    sections: Dict[str, str] = {}
    for idx, (line_no, name) in enumerate(hits):
        end = hits[idx + 1][0] if idx + 1 < len(hits) else min(len(lines), line_no + 180)
        block = "\n".join(lines[line_no + 1:end]).strip()
        if block and name not in sections:
            sections[name] = block[:12000]
    return sections


def detect_methods(title: str, text: str, limit: int = 6) -> List[str]:
    hay = (title + "\n" + text[:50000]).lower()
    methods = []
    for key, label in METHOD_KEYWORDS:
        if key.lower() in hay and label not in methods:
            methods.append(label)
    return methods[:limit]


def infer_category(title: str, text: str) -> str:
    hay = (title + "\n" + text[:20000]).lower()
    if any(k in hay for k in ["remote sensing", "遥感", "landsat", "sentinel", "modis", "hyperspectral"]):
        return "遥感/GIS"
    if any(k in hay for k in ["gis", "dem", "空间", "地理信息", "可达性", "生态敏感", "土地利用"]):
        return "遥感/GIS"
    if any(k in hay for k in ["transformer", "neural", "gan", "bayesian", "causal", "agent", "llm"]):
        return "AI/计算机"
    if any(k in hay for k in ["ecosystem", "生态", "洪涝", "土壤", "侵蚀", "灾害"]):
        return "生态环境"
    return "交叉学科"


def infer_year(meta: Optional[Dict], text: str, date: str) -> str:
    if meta and meta.get("year"):
        return str(meta["year"])
    m = re.search(r"\b(20[0-2][0-9])\b", text[:6000])
    return m.group(1) if m else "\u6b63\u6587\u5e74\u4efd\u5b57\u6bb5\u4e0d\u8db3"


def short_or_default(items: List[str], fallback: str) -> List[str]:
    return items if items else [fallback]


def bullets(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_transfer(title: str, text: str, methods: List[str]) -> List[str]:
    hay = (title + "\n" + text[:30000]).lower()
    out = []
    if any(k in hay for k in ["dem", "digital elevation", "地形", "坡度", "坡向", "高程"]):
        out.append("可迁移到 DEM 地形因子提取、坡面过程分析、流域地貌或灾害敏感性评价。")
    if any(k in hay for k in ["gis", "spatial", "空间", "可达性", "网络分析", "核密度", "插值"]):
        out.append("可迁移到 GIS 空间叠加、缓冲区、网络可达性、热点识别或空间插值任务。")
    if any(k in hay for k in ["remote sensing", "遥感", "landsat", "sentinel", "modis", "hyperspectral"]):
        out.append("可迁移到遥感样本构建、分类识别、时序变化检测或多源栅格融合。")
    if any(k in hay for k in ["risk", "sensitivity", "敏感", "风险", "灾害", "生态"]):
        out.append("可迁移到生态敏感性、洪涝风险、滑坡易发性或国土空间适宜性评价。")
    if any(k in hay for k in ["transformer", "neural", "gan", "bayesian", "causal", "llm", "agent"]):
        out.append("可迁移到小样本建模、因果分析、深度学习基准测试或自动化科研工具链设计。")
    if not out and methods:
        out.append(f"可把“{methods[0]}”整理为可复用的课程作业或研究生方法复刻模板。")
    if not out:
        out.append("可作为论文选题背景、方法比较或中文学术表达积累材料。")
    out.append("本次补卡不按原评分过滤，低分论文也保留其可复查信息和取舍依据。")
    return out[:5]


def build_card(date: str, idx: int, path: Path, meta: Optional[Dict]) -> str:
    if path.suffix.lower() == ".pdf":
        # Try pdf_ingest first, fallback to fulltext_utils
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
            from pdf_ingest import ingest_pdf
            result = ingest_pdf(str(path), engine="auto")
            if result and result.get("status") == "success" and result.get("text"):
                ext = {"text": result["text"], "status": "ok", "text_length_chars": len(result["text"]), "text_length_words": len(result["text"].split())}
            else:
                ext = extract_text_from_pdf(str(path))
        except Exception:
            ext = extract_text_from_pdf(str(path))
    else:
        ext = extract_text_from_html(str(path))
    text = clean_text(ext.get("text", ""))
    sentences = split_sentences(text)
    section_meta = parse_fulltext_sections(text)
    section_text = extract_section_text(text)
    quality = chinese_text_quality_check(text) if re.search(r"[\u4e00-\u9fff]", text) else {"quality": "ok", "issues": []}

    title = meta.get("title") if meta else title_from_path(path)
    title = title or title_from_path(path)
    authors = meta.get("authors") if meta else None
    if isinstance(authors, list) and authors:
        author_text = "、".join(str(a) for a in authors[:5])
    else:
        author_text = (meta or {}).get("first_author") or author_from_path(path)
    year = infer_year(meta, text, date)
    source = (meta or {}).get("source") or ("本地 PDF" if path.suffix.lower() == ".pdf" else "本地 HTML")
    abstract = (meta or {}).get("abstract", "")
    if not abstract:
        abstract = section_text.get("abstract", "")[:700]

    methods = detect_methods(title, text)
    data_sents = pick_sentences(sentences, DATA_HINTS, 4)
    method_sents = pick_sentences(
        split_sentences(section_text.get("methods", "") or text[:40000]),
        [keyword.split()[0] for keyword, _label in METHOD_KEYWORDS] + ["method", "模型", "方法", "计算", "分析"],
        4,
    )
    result_source = section_text.get("results", "") + "\n" + section_text.get("discussion", "") + "\n" + section_text.get("conclusion", "")
    result_sents = pick_sentences(split_sentences(result_source or text), RESULT_HINTS, 4)
    limit_sents = pick_sentences(sentences, LIMIT_HINTS, 2)

    if abstract:
        rq = split_sentences(abstract)
        research_problem = rq[0] if rq else f"该文围绕《{title}》展开，核心是把主题转化为可检索、可比较或可建模的问题。"
    else:
        research_problem = f"该文围绕《{title}》展开，核心是把主题转化为可检索、可比较或可建模的问题。"

    category = infer_category(title, text)
    text_len = ext.get("text_length_chars", 0)
    word_len = ext.get("text_length_words", 0)
    sec_names = section_meta.get("detected_sections", [])
    evidence = "全文文本已抽取" if ext.get("status") == "ok" else f"文本抽取失败：{ext.get('error', '未知原因')}"
    if quality.get("quality") in {"suspicious", "corrupted"}:
        evidence += f"；中文文本质量提示：{quality.get('quality')}（{'；'.join(quality.get('issues', [])[:2])}）"

    method_lines = methods[:]
    method_lines += [s for s in method_sents if s not in method_lines]
    method_lines = short_or_default(method_lines[:6], "正文中方法字段不够稳定，先保留题名和摘要层面的研究线索，供复核使用。")

    result_lines = short_or_default(
        result_sents[:4],
        "自动抽取未稳定识别结果段落；本卡片先保留全文路径、研究问题、数据和方法线索，避免低分或结构异常论文完全缺卡。",
    )

    limit_lines = short_or_default(
        limit_sents[:2],
        "未在自动抽取文本中稳定识别局限性段落；若进入正式精读，应复核实验边界、数据适用范围和结论外推条件。",
    )

    data_lines = short_or_default(
        data_sents[:4],
        "自动抽取未稳定识别数据来源；可从本地全文路径继续核对样本、区域、影像、统计资料或实验数据。",
    )

    transfer_lines = build_transfer(title, text, methods)
    code_tasks = [
        "把论文中的数据、方法、结果字段整理成一张可检索的 Obsidian 表格。",
        "若方法可复现，拆成一个最小 GIS/遥感/统计分析 notebook：数据读取、预处理、指标计算、结果图。",
        "把图表表达和结论句式加入中文学术表达积累库，保留来源日报日期。",
    ]

    title_cn_note = "中文题名需复核润色" if not re.search(r"[\u4e00-\u9fff]", title) else "中文题名已来自文件名或论文题名"

    lines = [
        f"### 补卡-{date}-{idx:02d}｜{title}",
        "",
        "#### 补充知识卡片",
        f"- **标题:** {title}",
        f"- **题名处理:** {title_cn_note}",
        f"- **作者:** {author_text}",
        f"- **年份:** {year}",
        f"- **来源:** {source}",
        f"- **论文分类:** {category}",
        f"- **本地全文路径:** `{path}`",
        f"- **证据状态:** {evidence}",
        f"- **正文有效长度:** {text_len} 字符 / {word_len} 词",
        f"- **识别章节:** {', '.join(sec_names) if sec_names else '未稳定识别'}",
        f"- **分数处理:** 本次按用户要求补齐卡片，不以评分高低作为是否生成卡片的门槛。",
        "",
        f"- **一句话总结:** 这篇论文围绕“{title}”提供了可检查的研究线索；当前卡片基于本地全文自动抽取，适合先补齐日报，再决定是否进入正式精读或长期知识库。",
        f"- **研究问题:** {research_problem}",
        "- **数据来源:**",
        bullets(data_lines),
        "- **方法流程:**",
        bullets(method_lines),
        "- **主要结果:**",
        bullets(result_lines),
        "- **局限与复核点:**",
        bullets(limit_lines),
        "- **可迁移到 GIS / 遥感 / DEM / 空间分析的点:**",
        bullets(transfer_lines),
        "- **可转 AI Code / 学习任务:**",
        bullets(code_tasks),
        "- **处理建议:** 先保留在日报补充卡片中；若要入长期知识库，再按全文证据、重复情况和个人研究方向进行二次筛选。",
        "",
    ]
    return "\n".join(lines)


def should_skip_file(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".bak") or name in {"final_checks.json", "cleanup_manifest.md"}


def normalize_supplement_evidence(text: str) -> str:
    """Apply the evidence boundary required by the paper-reading workflow."""
    evidence = "\u81ea\u52a8\u63d0\u53d6\u6b63\u6587\uff1b\u672a\u8fbe\u5230 PDF_TEXT_FULL \u5173\u952e\u7ae0\u8282\u8986\u76d6\u9608\u503c\uff0c\u4e0d\u5c06\u81ea\u52a8\u63d0\u53d6\u89c6\u4e3a\u4eba\u5de5\u5168\u6587\u7cbe\u8bfb\u3002"
    read_status = "\u5426\uff08\u4ec5\u57fa\u4e8e\u81ea\u52a8\u63d0\u53d6\u6b63\u6587\uff0c\u9700\u8981\u4eba\u5de5\u590d\u6838\uff09"
    uncertainty = "\u6837\u672c\u3001\u53c2\u6570\u3001\u7edf\u8ba1\u68c0\u9a8c\u548c\u7ed3\u679c\u4ec5\u5728\u81ea\u52a8\u63d0\u53d6\u4e2d\u53ef\u89c1\u65f6\u624d\u8bb0\u5f55\uff1b\u672a\u7a33\u5b9a\u8bc6\u522b\u7684\u5185\u5bb9\u5747\u5f85\u5168\u6587\u590d\u6838\u3002"
    text = re.sub(
        r"(- \*\*\u8bc1\u636e\u72b6\u6001:\*\* ).*",
        lambda match: (
            match.group(1)
            + evidence
            + "\n\n- **\u9605\u8bfb\u7b49\u7ea7:** PDF_TEXT_PARTIAL"
            + "\n\n- **\u662f\u5426\u5df2\u8bfb\u5168\u6587:** "
            + read_status
        ),
        text,
    )
    text = re.sub(
        r"(- \*\*\u5c40\u9650\u4e0e\u590d\u6838\u70b9:\*\*\n(?:- .*\n)+)",
        lambda match: match.group(1) + "- **\u4e0d\u786e\u5b9a\u9879:** " + uncertainty + "\n",
        text,
    )
    return text


def build_supplement(date: str, report_text: str, source_mode: str = DEFAULT_SOURCE_MODE) -> tuple[str, int]:
    files = [p for p in list_target_files(date, report_text, source_mode) if not should_skip_file(p)]
    metas = load_metadata(date)
    if not files:
        return "", 0

    cards = []
    for i, path in enumerate(files, 1):
        meta = find_metadata(path, metas)
        print(f"[{date}] {i}/{len(files)} {path.name}", flush=True)
        try:
            cards.append(build_card(date, i, path, meta))
        except Exception as exc:
            cards.append(
                "\n".join([
                    f"### 补卡-{date}-{i:02d}｜{title_from_path(path)}",
                    "",
                    "#### 补充知识卡片",
                    f"- **标题:** {title_from_path(path)}",
                    f"- **本地全文路径:** `{path}`",
                    f"- **证据状态:** 自动补卡失败：{exc}",
                    "- **分数处理:** 本次按用户要求补齐卡片，不以评分高低作为是否生成卡片的门槛。",
                    "- **处理建议:** 保留源文件路径，复核或重新抽取。",
                    "",
                ])
            )

    section_no = next_section_number(report_text)
    start = f"<!-- 论文日报卡片补齐开始:{date} -->"
    end = f"<!-- 论文日报卡片补齐结束:{date} -->"
    heading = f"## {section_no}. 论文日报卡片补齐（不按分数过滤）"
    intro = [
        start,
        "",
        heading,
        "",
        "> 本节为事后补齐。生成原则：只要最近日报中已有本地全文或已检查源文件，就补充卡片；不再因为评分偏低、未入库或自动门控而缺卡。自动抽取内容用于学习与复核，不等同于人工终审。",
        "",
        f"- **补齐日期:** {date}",
        f"- **补齐文件数:** {len(files)}",
        "- **分数策略:** 不按分数过滤，低分论文也保留摘要、方法、结果、迁移点和处理建议。",
        "",
    ]
    supplement, repairs = apply_banned_repairs("\n".join(intro + cards + [end, ""]))
    supplement = normalize_supplement_evidence(supplement)
    return supplement, repairs


def main() -> int:
    parser = argparse.ArgumentParser(description="补齐每日论文日报卡片，不按分数过滤。")
    parser.add_argument("--date", type=parse_iso_date, help="处理单日，格式 YYYY-MM-DD；默认今天。")
    parser.add_argument("--days", type=int, help="从 --date 或今天往前回补 N 天。")
    parser.add_argument("--start-date", type=parse_iso_date, help="回补起始日期，格式 YYYY-MM-DD。")
    parser.add_argument("--end-date", type=parse_iso_date, help="回补结束日期，格式 YYYY-MM-DD。")
    parser.add_argument(
        "--source-mode",
        choices=["auto", "all", "prefixed", "checked"],
        default=DEFAULT_SOURCE_MODE,
        help="来源文件选择策略。auto 优先哈希前缀文件，其次未入库已检查目录。",
    )
    parser.add_argument("--dry-run", action="store_true", help="只生成预览统计，不写入日报。")
    args = parser.parse_args()
    dates = resolve_dates(args)

    changed = []
    skipped = []
    total_repairs = 0
    residual_hits: Dict[str, List[str]] = {}
    for date in dates:
        report_path = REPORT_DIR / f"{date}_论文阅读日报.md"
        if not report_path.exists():
            print(f"[skip] report missing: {report_path}")
            skipped.append({"date": date, "reason": "report missing"})
            continue
        text = report_path.read_text(encoding="utf-8")
        text = strip_existing_block(text, date)
        supplement, repairs = build_supplement(date, text, args.source_mode)
        total_repairs += repairs
        if not supplement:
            print(f"[skip] no source files: {date}")
            skipped.append({"date": date, "reason": "no source files"})
            continue
        new_text = text.rstrip() + "\n\n---\n\n" + supplement
        banned = remaining_banned(new_text)
        if banned:
            residual_hits[str(report_path)] = banned
        if not args.dry_run:
            report_path.write_text(new_text, encoding="utf-8")
        changed.append(str(report_path))
    print(json.dumps({
        "dates": dates,
        "dry_run": args.dry_run,
        "changed": changed,
        "skipped": skipped,
        "count": len(changed),
        "banned_repairs": total_repairs,
        "banned_remaining": residual_hits,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
