#!/usr/bin/env python3
"""Register the completed writing-technique review, validate daily outputs, then delete only verified temporary backups."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import date as dt_date
from datetime import datetime
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent


def iso_date(value: str) -> str:
    try:
        return dt_date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期必须是 YYYY-MM-DD") from exc


def atomic_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    if hashlib.sha256(temporary.read_bytes()).digest() != hashlib.sha256(content.encode("utf-8")).digest():
        raise RuntimeError(f"写入校验失败：{path}")
    temporary.replace(path)


def register_writing_technique_batch(path: Path, run_date: str, covered: int, added: int, merged: int) -> None:
    if covered < 0 or added < 0 or merged < 0:
        raise ValueError("覆盖、新增和合并数量均不得为负数。")
    if not path.exists():
        raise FileNotFoundError(f"找不到写作技法库：{path}")
    start = f"<!-- writing-technique-batch:{run_date} -->"
    end = f"<!-- writing-technique-batch-end:{run_date} -->"
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.S).rstrip() + "\n"
    block = (
        f"\n{start}\n"
        f"- **{run_date} 写作技法批次核验**: 已逐篇完成当日 A/B 级（以 `PDF_TEXT_FULL` 入库批次为准）写作技法提取与去重。"
        f"- **覆盖论文数**: {covered}\n"
        f"- **新增技法数**: {added}\n"
        f"- **合并既有技法数**: {merged}\n"
        f"- **核验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{end}\n"
    )
    atomic_write(path, text + block)


def validate_outputs(root: Path, run_date: str) -> dict[str, object]:
    base = root / "01_读_论文阅读与复盘"
    library = base / "02_论文阅读库"
    report = base / "01_每日论文" / f"{run_date}_论文阅读日报.md"
    kb = base / "04_长期知识库" / "长期知识库.md"
    techniques = base / "04_长期知识库" / "学术写作技法库.md"
    terminology = base / "04_长期知识库" / "专业术语库.md"
    readlist = library / "已读论文清单.md"
    md_dir = library / "md" / run_date
    source_dir = library / "fulltext_papers" / run_date
    required = [report, kb, techniques, terminology, readlist]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return {"ok": False, "missing": missing, "reason": "缺少必要产物"}
    report_text = report.read_text(encoding="utf-8", errors="replace")
    kb_text = kb.read_text(encoding="utf-8", errors="replace")
    tech_text = techniques.read_text(encoding="utf-8", errors="replace")
    term_text = terminology.read_text(encoding="utf-8", errors="replace")
    readlist_text = readlist.read_text(encoding="utf-8", errors="replace")
    dated_markers_ok = all([
        f"<!-- desktop-pdf-full-process-start:{run_date} -->" in report_text,
        f"<!-- desktop-pdf-full-process-end:{run_date} -->" in report_text,
        f"<!-- desktop-pdf-kb-start:{run_date} -->" in kb_text,
        f"<!-- desktop-pdf-kb-end:{run_date} -->" in kb_text,
        f"<!-- writing-technique-batch:{run_date} -->" in tech_text,
        f"<!-- writing-technique-batch-end:{run_date} -->" in tech_text,
        f"<!-- terminology-batch-start:{run_date} -->" in term_text,
        f"<!-- terminology-batch-end:{run_date} -->" in term_text,
        f"最后更新：{run_date}" in readlist_text,
    ])
    pdfs = sorted(source_dir.rglob("*.pdf")) if source_dir.exists() else []
    markdown = sorted(md_dir.glob("*.md")) if md_dir.exists() else []
    corrupt_markdown = [str(path) for path in markdown if "\ufffd" in path.read_text(encoding="utf-8", errors="replace")]
    source_hashes = set(re.findall(r"^\s*source_sha256:\s*([0-9a-f]{64})\s*$", "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in markdown), re.M))
    pdf_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in pdfs}
    markdown_ok = len(markdown) == len(pdfs) and not corrupt_markdown and source_hashes == pdf_hashes
    ok = bool(dated_markers_ok and markdown_ok)
    return {
        "ok": ok,
        "missing": [],
        "dated_markers_ok": dated_markers_ok,
        "pdf_count": len(pdfs),
        "markdown_count": len(markdown),
        "corrupt_markdown": corrupt_markdown,
        "markdown_hashes_match": source_hashes == pdf_hashes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="核验每日论文四项产物后，才删除该批临时备份。")
    parser.add_argument("--date", type=iso_date, default=dt_date.today().isoformat())
    parser.add_argument("--workflow-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--covered-paper-count", type=int, required=True, help="已完成写作技法提取的当日 A/B 级论文数。")
    parser.add_argument("--new-techniques", type=int, required=True)
    parser.add_argument("--merged-techniques", type=int, required=True)
    args = parser.parse_args()
    root = args.workflow_root
    technique_path = root / "01_读_论文阅读与复盘/04_长期知识库/学术写作技法库.md"
    register_writing_technique_batch(technique_path, args.date, args.covered_paper_count, args.new_techniques, args.merged_techniques)
    validation = validate_outputs(root, args.date)
    library = root / "01_读_论文阅读与复盘/02_论文阅读库"
    backups = sorted(path for path in library.glob(f"backup_{args.date}_*") if path.is_dir())
    removed: list[str] = []
    if validation["ok"]:
        for backup in backups:
            shutil.rmtree(backup)
            removed.append(str(backup))
    result = {"date": args.date, "validation": validation, "backup_candidates": [str(path) for path in backups], "backup_removed": removed, "backup_cleaned": bool(validation["ok"])}
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # ── 知识图谱自动更新 ──
    if validation["ok"]:
        try:
            from knowledge_graph.kg_hook import update_kg_if_changed
            kg_updated = update_kg_if_changed()
            result["kg_updated"] = kg_updated
        except Exception as exc:
            result["kg_update_error"] = str(exc)

    return 0 if validation["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
