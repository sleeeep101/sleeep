#!/usr/bin/env python3
"""Build durable Markdown assets from an archived daily PDF batch.

This module is deliberately independent of the desktop staging area: it takes the
already archived PDFs as the source of truth, creates one Markdown document per
PDF, and refreshes the terminology index idempotently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


# Keep the script portable when the workflow is cloned to another machine.
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
READING_RELATIVE = Path("01_读_论文阅读与复盘")
TERMINOLOGY_NAME = "专业术语库.md"
READLIST_NAME = "已读论文清单.md"


@dataclass(frozen=True)
class CorpusRecord:
    pdf: Path
    markdown: Path
    sha256: str
    method: str
    char_count: int
    error: str = ""


TERM_CATALOG = (
    ("CGCS2000", "K", "国家大地坐标系2000（CGCS2000）", "我国统一的三维地心坐标参考框架，用于测绘与空间数据的坐标基准统一。"),
    ("WebGIS", "B", "WebGIS", "通过浏览器发布、查询、分析和共享空间数据的地理信息系统架构。"),
    ("数字孪生", "Z", "数字孪生地理信息系统", "以三维地理空间模型耦合业务或传感数据，用于状态映射、仿真与决策支持的 GIS 体系。"),
    ("三维GIS", "B", "三维地理信息系统（3D GIS）", "表达和分析具有高程或三维几何信息的地理对象、场景与过程的 GIS 系统。"),
    ("空间聚类", "B", "空间聚类分析", "依据空间邻近性与属性相似性识别地理对象聚集结构的空间分析方法。"),
    ("国土空间规划", "B", "国土空间规划 GIS 支撑", "以空间数据、用途管制单元和多目标评价支撑国土空间规划编制与实施评估的方法体系。"),
    ("地质灾害监测预警", "H", "地质灾害 GIS 监测预警", "融合灾害点位、环境因子和时空监测信息进行风险识别、预警与应急响应的 GIS 应用。"),
    ("城市地下空间", "B", "城市地下空间 GIS 规划", "以地下管线、地质、工程和权属等空间数据支撑地下空间开发协调的 GIS 规划方法。"),
    ("智慧城市", "B", "智慧城市地理信息系统", "整合城市多源时空数据，为城市运行监测、服务协同和治理决策提供地理信息支撑的系统。"),
    ("遥感", "C", "遥感与 GIS 集成", "将遥感影像解译成果与 GIS 空间数据管理、分析和制图流程耦合的技术路径。"),
    ("OBE", "Z", "成果导向教育（Outcome-Based Education, OBE）", "从预期学习成果反向设计课程目标、教学活动和评价标准的教育设计理念。"),
    ("项目式学习", "Z", "GIS 项目式学习", "以真实空间问题和可交付 GIS 成果组织学习任务、协作与评价的教学模式。"),
    ("翻转课堂", "Z", "GIS 翻转课堂", "将知识输入前置到课前、把课堂时间用于 GIS 实践、讨论和反馈的教学组织方式。"),
    ("混合式教学", "Z", "GIS 混合式教学", "整合线上资源、线下实践和过程性评价的 GIS 课程教学设计方式。"),
    ("3S", "Z", "3S 技术一体化", "协同使用遥感、地理信息系统和全球卫星导航定位技术开展空间信息获取、处理与应用的技术体系。"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def has_excessive_replacement_characters(text: str) -> bool:
    """Reject visibly corrupted extraction output before it becomes durable Markdown."""
    return text.count("\ufffd") > max(5, len(text) // 100)


def extract_pdf_text(pdf: Path) -> tuple[str, str, str]:
    """Use the shared seven-engine PDF pipeline, with a light local fallback."""
    try:
        workflow_root = str(DEFAULT_ROOT)
        if workflow_root not in sys.path:
            sys.path.insert(0, workflow_root)
        from pdf_ingest import ingest_pdf

        # The shared pipeline normally writes rich intermediate artifacts.  This
        # workflow only needs its extracted Markdown, so use an auto-cleaned
        # temporary directory and retain the durable copy under ``md/YYYY-MM-DD``.
        with tempfile.TemporaryDirectory(prefix="academic_pdf_ingest_") as temp_dir:
            result = ingest_pdf(pdf, engine="auto", output_dir=temp_dir, force=True)
            generated = Path(str(result.get("output_dir", ""))) / "paper.md"
            if generated.exists():
                text = generated.read_text(encoding="utf-8", errors="replace")
                text = re.sub(r"^<!--.*?-->\s*", "", text, count=1, flags=re.S)
                text = clean_text(text)
                if len(text) >= 200 and not has_excessive_replacement_characters(text):
                    method = str(result.get("method") or "pdf_ingest")
                    return text, f"pdf_ingest/{method}", ""
                ingest_error = "pdf_ingest output contains excessive replacement characters"
            else:
                ingest_error = str(result.get("error") or "pdf_ingest output too short")[:240]
    except Exception as exc:  # fall through to the lightweight local fallback
        ingest_error = f"pdf_ingest unavailable: {exc}"[:240]

    # Keep this fallback for environments where the shared pipeline itself cannot
    # be imported; it is intentionally not the primary workflow path.
    executable = os.environ.get("PDF_INGEST_MARKITDOWN") or shutil.which("markitdown")
    if executable and Path(executable).is_file():
        try:
            result = subprocess.run(
                [executable, str(pdf)], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
            text = clean_text(result.stdout or "")
            if result.returncode == 0 and len(text) >= 200 and not has_excessive_replacement_characters(text):
                return text, "markitdown", ""
        except (OSError, subprocess.TimeoutExpired) as exc:
            markitdown_error = str(exc)
        else:
            markitdown_error = (result.stderr or "MarkItDown output too short")[:240]
    else:
        markitdown_error = "MarkItDown unavailable"
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf))
        if reader.is_encrypted:
            reader.decrypt("")
        text = clean_text("\n\n".join(page.extract_text() or "" for page in reader.pages))
        if len(text) >= 200:
            return text, "pypdf", ""
        return "", "pypdf", f"{ingest_error}; {markitdown_error}; pypdf output too short"
    except Exception as exc:  # pragma: no cover - library-specific error messages
        return "", "pypdf", f"{ingest_error}; {markitdown_error}; pypdf failed: {exc}"


def markdown_target(md_dir: Path, pdf: Path, digest: str) -> Path:
    stem = re.sub(r'[\\/:*?"<>|]+', "_", pdf.stem).strip(" .") or "unnamed"
    target = md_dir / f"{stem}.md"
    if not target.exists():
        return target
    existing = target.read_text(encoding="utf-8", errors="replace")[:600]
    if f"source_sha256: {digest}" in existing:
        return target
    return md_dir / f"{stem}_{digest[:10]}.md"


def clean_surrogates(text: str) -> str:
    """Remove lone surrogate characters (U+D800–U+DFFF) that break UTF-8 encoding."""
    if not text:
        return text
    return re.sub(r"[\ud800-\udfff]", "�", text)


def render_markdown(pdf: Path, digest: str, text: str, method: str, error: str) -> str:
    header = [
        "<!--",
        f"  source_pdf: {pdf.name}",
        "  source_path_redacted: true",
        f"  source_sha256: {digest}",
        f"  conversion_method: {method}",
        f"  converted_at: {datetime.now().isoformat(timespec='seconds')}",
        "-->",
        "",
        f"# {pdf.stem}",
        "",
    ]
    if error:
        header.extend(["## 转换状态", "", f"转换失败：{error}", ""])
    return "\n".join(header) + text + "\n"


def convert_daily_pdfs(workflow_root: Path, run_date: str, *, force: bool = False) -> list[CorpusRecord]:
    library = workflow_root / READING_RELATIVE / "02_论文阅读库"
    source_dir = library / "fulltext_papers" / run_date
    md_dir = library / "md" / run_date
    md_dir.mkdir(parents=True, exist_ok=True)
    records: list[CorpusRecord] = []
    for pdf in sorted(source_dir.rglob("*.pdf")):
        digest = sha256_file(pdf)
        target = markdown_target(md_dir, pdf, digest)
        if target.exists() and not force:
            content = target.read_text(encoding="utf-8", errors="replace")
            if not has_excessive_replacement_characters(content):
                records.append(CorpusRecord(pdf, target, digest, "existing", len(content)))
                continue
        text, method, error = extract_pdf_text(pdf)
        target.write_text(clean_surrogates(render_markdown(pdf, digest, text, method, error)), encoding="utf-8")
        records.append(CorpusRecord(pdf, target, digest, method, len(text), error))
    return records


def matched_terms(text: str) -> list[tuple[str, str, str, str]]:
    return [term for term in TERM_CATALOG if term[0].lower() in text.lower()]


def next_term_ids(terminology: str) -> dict[str, int]:
    ids: dict[str, int] = {}
    for category, number in re.findall(r"^###\s+([A-Z])-([0-9]{3})", terminology, re.M):
        ids[category] = max(ids.get(category, 0), int(number))
    return ids


def update_terminology(workflow_root: Path, run_date: str, records: Iterable[CorpusRecord]) -> dict[str, int]:
    path = workflow_root / READING_RELATIVE / "04_长期知识库" / TERMINOLOGY_NAME
    original = path.read_text(encoding="utf-8", errors="replace") if path.exists() else "# 专业术语库\n"
    start = f"<!-- terminology-batch-start:{run_date} -->"
    end = f"<!-- terminology-batch-end:{run_date} -->"
    original = re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", original, flags=re.S).rstrip() + "\n"
    existing_names = {name.strip() for name in re.findall(r"^###\s+[A-Z]-\d+｜([^\n（]+)", original, re.M)}
    next_ids = next_term_ids(original)
    additions: list[str] = []
    covered = 0
    merged = 0
    for record in records:
        if record.error:
            continue
        text = record.markdown.read_text(encoding="utf-8", errors="replace")
        for _, category, name, explanation in matched_terms(text):
            covered += 1
            if name in existing_names:
                merged += 1
                continue
            next_ids[category] = next_ids.get(category, 0) + 1
            additions.extend([
                f"### {category}-{next_ids[category]:03d}｜{name}",
                f"- **解释**: {explanation}",
                f"- **来源**: {record.pdf.stem}",
                f"- **入库日期**: {run_date}",
                "",
            ])
            existing_names.add(name)
    block = [start, "", f"## {run_date} 自动术语抽取", "", f"- **覆盖命中**: {covered}", f"- **新增术语**: {len(additions) // 5}", f"- **合并既有术语**: {merged}", ""]
    block.extend(additions or ["本批未发现满足专业术语库收录门槛的新术语。", ""])
    block.extend([end, ""])
    path.write_text(clean_surrogates(original + "\n" + "\n".join(block)), encoding="utf-8")
    return {"term_matches": covered, "term_added": len(additions) // 5, "term_merged": merged}


def normalize_title(value: str) -> str:
    return re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE).lower()


def field_value(block: str, label: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(label)}:\*\*\s*(.+)$", block, re.M)
    return match.group(1).strip() if match else ""


def read_report_entries(report: Path) -> list[dict[str, str]]:
    """Read only explicit full-text cards; never infer an item from a summary table."""
    text = report.read_text(encoding="utf-8", errors="replace")
    entries: list[dict[str, str]] = []
    for match in re.finditer(r"^###\s+(DPDF-\d{8}-\d{3})｜(.+?)\s*$", text, re.M):
        end = re.search(r"^###\s+", text[match.end():], re.M)
        block_end = match.end() + end.start() if end else len(text)
        block = text[match.start():block_end]
        if "**阅读等级:** PDF_TEXT_FULL" not in block and "**全文证据状态:** PDF_TEXT_FULL" not in block:
            continue
        entries.append({
            "paper_id": match.group(1),
            "title": match.group(2).strip(),
            "author": field_value(block, "作者") or "未识别",
            "year": field_value(block, "年份") or "未识别",
            "report": str(report),
        })
    return entries


def update_readlist_from_reports(workflow_root: Path, run_date: str) -> dict[str, int]:
    from rebuild_reading_list import rebuild_reading_list

    stats = rebuild_reading_list(
        workflow_root,
        start_date="2026-05-30",
        end_date=run_date,
    )
    return {
        "report_entries": int(stats["explicit_fulltext_cards"]),
        "readlist_added": int(stats["unique_titles"]),
        "readlist_raw_assets": int(stats["raw_assets"]),
        "readlist_backup_cleaned": bool(stats["backup_cleaned"]),
    }


def validate_daily_assets(workflow_root: Path, run_date: str, records: Iterable[CorpusRecord]) -> dict[str, object]:
    records = list(records)
    missing = [str(record.markdown) for record in records if not record.markdown.exists()]
    failures = [str(record.pdf) for record in records if record.error]
    return {
        "pdf_count": len(records),
        "markdown_count": sum(record.markdown.exists() for record in records),
        "conversion_failures": len(failures),
        "missing_markdown": missing,
        "ok": bool(records) and not failures and not missing,
    }


def enrich_archived_pdfs(workflow_root: Path, run_date: str, *, force: bool = False) -> dict[str, object]:
    records = convert_daily_pdfs(workflow_root, run_date, force=force)
    term_stats = update_terminology(workflow_root, run_date, records)
    readlist_stats = update_readlist_from_reports(workflow_root, run_date)
    validation = validate_daily_assets(workflow_root, run_date, records)
    return {**validation, **term_stats, **readlist_stats}


def main() -> int:
    parser = argparse.ArgumentParser(description="补齐归档 PDF 的 Markdown、术语库与已读清单。")
    parser.add_argument("--date", required=True, help="处理日期，格式 YYYY-MM-DD")
    parser.add_argument("--workflow-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--force", action="store_true", help="重新转换已有 Markdown")
    args = parser.parse_args()
    print(json.dumps(enrich_archived_pdfs(args.workflow_root, args.date, force=args.force), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
