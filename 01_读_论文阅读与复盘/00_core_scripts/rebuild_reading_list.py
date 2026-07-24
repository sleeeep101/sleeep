#!/usr/bin/env python3
"""Rebuild the de-duplicated reading list from daily-report-linked full-text assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent
READING_RELATIVE = Path("01_读_论文阅读与复盘")
READLIST_NAME = "已读论文清单.md"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class ReadingRecord:
    read_date: str
    title: str
    evidence: str
    asset: Path
    report: Path
    author: str = ""
    year: str = ""
    paper_id: str = ""
    priority: int = 0


def normalize_title(value: str) -> str:
    value = re.sub(r"^[0-9a-f]{12}_", "", value.strip(), flags=re.I)
    return re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE).lower()


def clean_title(value: str) -> str:
    value = value.strip().strip("#").strip()
    value = re.sub(r"^[0-9a-f]{12}_", "", value, flags=re.I)
    parts = value.split("_")
    if len(parts) > 1 and re.fullmatch(r"[\u4e00-\u9fff·]{2,5}", parts[-1]):
        value = "_".join(parts[:-1])
    return value.replace("_", " ").strip() or "未识别题名"


def is_in_range(value: str, start_date: str, end_date: str) -> bool:
    return bool(DATE_PATTERN.fullmatch(value)) and start_date <= value <= end_date


def report_path(reading_root: Path, run_date: str) -> Path:
    return reading_root / "01_每日论文" / f"{run_date}_论文阅读日报.md"


def extract_markdown_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")[:6000]
    source = re.search(r"(?m)^\s*source(?:_pdf)?:\s*(.+?)\s*$", text)
    if source:
        source_path = Path(source.group(1).strip().strip("`"))
        if source_path.stem and source_path.stem.lower() != "paper":
            return clean_title(source_path.stem)
    heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if heading:
        return clean_title(heading.group(1))
    return clean_title(path.parent.name if path.name.lower() == "paper.md" else path.stem)


def json_text(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            value = "、".join(str(item) for item in value if str(item).strip())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def extract_source_metadata(path: Path) -> tuple[str, str, str]:
    metadata = path / "metadata.json"
    if metadata.exists():
        try:
            data = json.loads(metadata.read_text(encoding="utf-8", errors="replace"))
            title = json_text(data, "title", "paper_title", "name")
            author = json_text(data, "authors", "author")
            year = json_text(data, "year", "published_year", "publication_year")
            if title:
                return clean_title(title), author, year
        except (OSError, json.JSONDecodeError):
            pass
    note = path / "note.md"
    if note.exists():
        text = note.read_text(encoding="utf-8", errors="replace")[:2000]
        heading = re.search(r"(?m)^#\s+(.+?)\s*$", text)
        if heading:
            return clean_title(heading.group(1)), "", ""
    return clean_title(path.name), "", ""


def field_value(block: str, label: str) -> str:
    match = re.search(rf"(?m)^-\s+\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", block)
    return match.group(1).strip() if match else ""


def explicit_fulltext_cards(report: Path) -> dict[str, ReadingRecord]:
    """Read only cards that explicitly state PDF_TEXT_FULL."""
    if not report.exists():
        return {}
    text = report.read_text(encoding="utf-8", errors="replace")
    records: dict[str, ReadingRecord] = {}
    pattern = re.compile(r"(?ms)^#{3,6}\s+(.+?)\s*$\n(.*?)(?=^#{3,6}\s+|\Z)")
    for match in pattern.finditer(text):
        heading, body = match.group(1).strip(), match.group(2)
        if "PDF_TEXT_FULL" not in body:
            continue
        full = f"{heading}\n{body}"
        paper_id_match = re.search(r"DPDF-\d{8}-\d{3}", full)
        if paper_id_match:
            paper_id = paper_id_match.group(0)
        else:
            paper_id_match = re.search(r"Paper_ID:\s*([^\s|*]+)", full)
            paper_id = paper_id_match.group(1) if paper_id_match else ""
        title_match = re.match(r"DPDF-\d{8}-\d{3}[｜|](.+)", heading)
        title = clean_title(title_match.group(1)) if title_match else field_value(body, "标题")
        if not title:
            continue
        record = ReadingRecord(
            read_date=report.name[:10],
            title=title,
            evidence="PDF_TEXT_FULL（日报明确全文卡）",
            asset=report,
            report=report,
            author=field_value(body, "作者"),
            year=field_value(body, "年份"),
            paper_id=paper_id,
            priority=3,
        )
        records.setdefault(normalize_title(title), record)
    return records


def asset_records(reading_root: Path, start_date: str, end_date: str) -> list[ReadingRecord]:
    library = reading_root / "02_论文阅读库"
    records: list[ReadingRecord] = []
    md_root = library / "md"
    if md_root.exists():
        for day_dir in sorted(path for path in md_root.iterdir() if path.is_dir() and is_in_range(path.name, start_date, end_date)):
            report = report_path(reading_root, day_dir.name)
            for path in sorted(day_dir.rglob("*.md")):
                records.append(ReadingRecord(
                    read_date=day_dir.name,
                    title=extract_markdown_title(path),
                    evidence="日报关联全文（本地 Markdown）",
                    asset=path,
                    report=report,
                    priority=2,
                ))
    source_root = library / "paper_sources"
    if source_root.exists():
        for day_dir in sorted(path for path in source_root.iterdir() if path.is_dir() and is_in_range(path.name, start_date, end_date)):
            report = report_path(reading_root, day_dir.name)
            for path in sorted(child for child in day_dir.iterdir() if child.is_dir()):
                if not ((path / "metadata.json").exists() or (path / "source.pdf").exists()):
                    continue
                title, author, year = extract_source_metadata(path)
                asset = path / "source.pdf" if (path / "source.pdf").exists() else path / "metadata.json"
                records.append(ReadingRecord(
                    read_date=day_dir.name,
                    title=title,
                    evidence="日报关联全文（已归档来源）",
                    asset=asset,
                    report=report,
                    author=author,
                    year=year,
                    priority=1,
                ))
    return records


def choose_records(records: Iterable[ReadingRecord], explicit: dict[str, ReadingRecord]) -> list[ReadingRecord]:
    chosen: dict[str, ReadingRecord] = {}
    for record in records:
        key = normalize_title(record.title)
        if not key or key in {"paper", "note"}:
            continue
        candidate = explicit.get(key, record)
        current = chosen.get(key)
        if current is None or (candidate.priority, candidate.read_date) > (current.priority, current.read_date):
            chosen[key] = candidate
    return sorted(chosen.values(), key=lambda item: (item.read_date, normalize_title(item.title)), reverse=True)


def md_escape(value: str) -> str:
    return value.replace("|", "｜").replace("\n", " ").strip()


def render_readlist(records: list[ReadingRecord], start_date: str, end_date: str, raw_count: int) -> str:
    explicit_count = sum(record.evidence.startswith("PDF_TEXT_FULL") for record in records)
    lines = [
        "# 已读论文去重清单",
        "",
        f"> 最后更新：{end_date}",
        f"> 统计范围：{start_date} 至 {end_date} 的每日日报关联全文资产。",
        f"> 原始资产 {raw_count} 份，按标题标准化去重后 {len(records)} 篇；其中日报明确全文精读卡 {explicit_count} 篇。",
        "> 证据边界：`PDF_TEXT_FULL` 为日报明确全文卡；其余“日报关联全文”表示已归档/已转换全文，不等同于人工精读结论。",
        "",
        "| 序号 | 阅读日期 | 标题 | 作者 | 年份 | 证据层级 | 本地资产 | 日报来源 |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for index, record in enumerate(records, 1):
        report = f"`{record.report}`" if record.report.exists() else "日报文件缺失"
        lines.append(
            f"| {index} | {record.read_date} | {md_escape(record.title)} | {md_escape(record.author) or '—'} | "
            f"{md_escape(record.year) or '—'} | {record.evidence} | `{record.asset}` | {report} |"
        )
    lines.append("")
    return "\n".join(lines)


def table_row_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\|\s*\d+\s*\|", line))


def rebuild_reading_list(workflow_root: Path, *, start_date: str = "2026-05-30", end_date: str | None = None, dry_run: bool = False) -> dict[str, object]:
    reading_root = workflow_root / READING_RELATIVE
    end_date = end_date or date.today().isoformat()
    all_assets = asset_records(reading_root, start_date, end_date)
    reports = [report_path(reading_root, day) for day in sorted({record.read_date for record in all_assets})]
    explicit: dict[str, ReadingRecord] = {}
    for report in reports:
        for key, record in explicit_fulltext_cards(report).items():
            existing = explicit.get(key)
            if existing is None or record.read_date >= existing.read_date:
                explicit[key] = record
    records = choose_records(all_assets, explicit)
    payload = render_readlist(records, start_date, end_date, len(all_assets))
    checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    summary = {
        "raw_assets": len(all_assets),
        "unique_titles": len(records),
        "explicit_fulltext_cards": sum(record.evidence.startswith("PDF_TEXT_FULL") for record in records),
        "checksum": checksum,
        "backup_cleaned": False,
    }
    if dry_run:
        return summary

    target = reading_root / "02_论文阅读库" / READLIST_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_name(f"{target.stem}.backup-{datetime.now():%Y%m%d%H%M%S}{target.suffix}")
    if target.exists():
        shutil.copy2(target, backup)
    temp = target.with_name(f"{target.name}.tmp")
    temp.write_text(payload, encoding="utf-8")
    temp.replace(target)
    written = target.read_text(encoding="utf-8", errors="replace")
    if table_row_count(written) != len(records) or hashlib.sha256(written.encode("utf-8")).hexdigest() != checksum:
        if backup.exists():
            shutil.copy2(backup, target)
        raise RuntimeError("已读论文清单核验失败，已恢复备份。")
    if backup.exists():
        backup.unlink()
        summary["backup_cleaned"] = True
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="从日报关联全文资产重建已读论文去重清单。")
    parser.add_argument("--workflow-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--start-date", default="2026-05-30")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(
        rebuild_reading_list(args.workflow_root, start_date=args.start_date, end_date=args.end_date, dry_run=args.dry_run),
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
