#!/usr/bin/env python3
"""weekly_digest_builder.py — 从日报轻量提取本周论文清单生成周组会摘要准备材料

用法:
  python weekly_digest_builder.py --daily-dir ../reports/daily/
  python weekly_digest_builder.py --daily-dir ../reports/daily/ --start-date 2026-06-01 --end-date 2026-06-04
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def ensure_utf8_console() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def parse_date_from_filename(name: str) -> datetime | None:
    """Try to extract YYYY-MM-DD from filename."""
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if match:
        try:
            return datetime(int(match[1]), int(match[2]), int(match[3]))
        except ValueError:
            pass
    return None


def list_daily_files(daily_dir: Path, start_date: datetime, end_date: datetime) -> list[Path]:
    """List daily report MD files within date range."""
    files = []
    for md_file in sorted(daily_dir.glob("*.md")):
        file_date = parse_date_from_filename(md_file.name)
        if file_date is None:
            file_date = datetime.fromtimestamp(md_file.stat().st_mtime)
        if start_date <= file_date <= end_date:
            files.append(md_file)
    return files


def extract_paper_info(text: str) -> list[dict]:
    """Extract structured paper info from daily report text.

    Handles both older ('候选论文列表' table) and newer ('全文精读卡片' sections) formats.
    """
    papers = []

    # ── Format 1: Full-text cards (newer format, 2026-06-02+) ──
    # Sections start with "### Paper_ID:" and contain "- **标题:**", "- **一句话总结**"
    card_blocks = re.split(r"\n(?=### Paper_ID:)", text)
    for block in card_blocks:
        if not block.strip():
            continue
        paper = {"titles": [], "summaries": [], "methods": [], "gis_points": [], "trust": ""}
        # Extract fields with **key:** value pattern
        for match in re.finditer(r"-\s*\*\*(.+?):\*\*\s*(.+)", block):
            key = match.group(1).strip()
            val = match.group(2).strip()
            if key in ("标题",):
                paper.setdefault("titles", []).append(val)
            elif key in ("一句话总结", "中文一句话总结"):
                paper.setdefault("summaries", []).append(val)
            elif key in ("方法流程", "方法"):
                paper.setdefault("methods", []).append(val)
            elif key in ("可迁移到 GIS/遥感/空间分析的点", "可迁移"):
                paper.setdefault("gis_points", []).append(val)
            elif key in ("阅读等级", "可信度"):
                paper["trust"] = val
        if paper["titles"]:
            papers.append(paper)

    # ── Format 2: Candidate table (older format, 2026-06-01 and before) ──
    if not papers:
        # Table: | # | 标题 | 一作 | 年 | ...
        for match in re.finditer(r"\|\s*\d+\s*\|\s*(.{10,80}?)\s*\|", text):
            title = match.group(1).strip()
            if title and not title.startswith(("标题", "---", "#", "论文标题")):
                papers.append({
                    "titles": [title],
                    "summaries": [],
                    "methods": [],
                    "gis_points": [],
                    "trust": "仅摘要(候选表)",
                })

    # ── Supplement: 今日可加入长期知识库 table ──
    kb_section = re.search(r"## \d+\. 今日可加入长期知识库的论文\n\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
    if kb_section:
        for match in re.finditer(r"\|\s*\d+\s*\|\s*(.{10,80}?)\s*\|", kb_section.group(1)):
            title = match.group(1).strip()
            if title and not title.startswith(("标题", "---")):
                # Check if already present
                existing = [p for p in papers if any(t[:30] in title[:30] or title[:30] in t[:30] for t in p["titles"])]
                if not existing:
                    papers.append({
                        "titles": [title],
                        "summaries": [],
                        "methods": [],
                        "gis_points": [],
                        "trust": "全文精读(知识库推荐)",
                    })

    return papers


def build_digest(daily_dir: Path, start_date: datetime, end_date: datetime, max_files: int) -> str:
    files = list_daily_files(daily_dir, start_date, end_date)
    files = files[:max_files]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 周组会摘要准备材料",
        "",
        f"> 生成时间: {now}",
        f"> 输入目录: {daily_dir}",
        f"> 日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
        "> 注意：本文件由脚本从日报中轻量提取，需人工复核后再用于组会。",
        "",
        "## 1. 本周论文清单",
        "",
        "| 序号 | 日期 | 论文标题 | 来源文件 | 识别状态 |",
        "|---:|------|---------|---------|---------|",
    ]

    all_papers = []
    for md_file in files:
        file_date = parse_date_from_filename(md_file.name)
        date_str = file_date.strftime("%Y-%m-%d") if file_date else "未知日期"
        text = md_file.read_text(encoding="utf-8")
        papers_info = extract_paper_info(text)

        if papers_info:
            for pi in papers_info[:10]:  # Max 10 papers per daily file
                title = pi["titles"][0] if pi["titles"] else "未识别标题"
                summary = pi["summaries"][0] if pi["summaries"] else ""
                method = pi["methods"][0] if pi["methods"] else ""
                gis_pt = pi["gis_points"][0] if pi["gis_points"] else ""
                trust = pi.get("trust", "")

                all_papers.append({
                    "date": date_str,
                    "title": title[:100],
                    "source": md_file.name,
                    "summary": summary,
                    "method": method,
                    "gis_point": gis_pt,
                    "trust": trust,
                })
                status = trust if trust else ("已识别" if summary else "仅标题")
                lines.append(f"| {len(all_papers)} | {date_str} | {title[:70]} | {md_file.name} | {status} |")
        else:
            lines.append(f"| - | {date_str} | 未识别标题 | {md_file.name} | 需人工 |")

    if not files:
        lines.append("| - | - | 未找到日报文件 | - | - |")

    # Topic clustering
    lines.extend([
        "",
        "## 2. 候选汇报主线",
        "",
        "按主题粗分：",
        "| 主题 | 论文数 | 论文",
        "|------|--------|------|",
    ])
    gis_papers = [p for p in all_papers if any(kw in p["title"].lower() for kw in ["gis", "遥感", "空间", "dem", "地图", "地理", "卫星", "sentinel", "landsat"])]
    rs_papers = [p for p in all_papers if any(kw in p["title"].lower() for kw in ["遥感", "卫星", "影像", "sentinel", "landsat", "ndvi"])]
    method_papers = [p for p in all_papers if any(kw in p["title"].lower() for kw in ["方法", "模型", "算法", "model", "learning", "深度学习", "machine"])]
    other_papers = [p for p in all_papers if p not in gis_papers + rs_papers + method_papers]

    for topic, papers, keyword in [("GIS/空间分析", gis_papers, "gis"), ("遥感", rs_papers, "遥感"), ("方法工具", method_papers, "方法"), ("其他", other_papers, "其他")]:
        if papers:
            lines.append(f"| {topic} | {len(papers)} | {', '.join(p['title'][:40] for p in papers[:3])} |")

    # Per-paper details
    lines.extend([
        "",
        "## 3. 每篇论文的可用信息",
        "",
    ])
    for i, p in enumerate(all_papers[:10], 1):
        lines.append(f"### 论文 {i}：{p['title'][:80]}")
        lines.append(f"- 日期: {p['date']}")
        lines.append(f"- 来源文件: {p['source']}")
        lines.append(f"- 一句话总结: {p.get('summary', '未提取')[:120]}")
        lines.append(f"- 方法: {p.get('method', '未提取')[:120]}")
        lines.append(f"- 可迁移到GIS/遥感/空间分析的点: {p.get('gis_point', '未提取')[:120]}")
        lines.append(f"- 可信度: {p.get('trust', '需人工复核')}")
        lines.append("")

    # Suggested PPT material
    lines.extend([
        "## 4. 建议进入组会 PPT 的材料",
        "",
        "| 优先级 | 论文 | 推荐理由 | 需要补充 |",
        "|---|---|---|---|",
    ])
    for p in all_papers[:5]:
        gis_rel = "GIS相关" if any(kw in p["title"].lower() for kw in ["gis", "遥感", "空间", "dem"]) else "方法可借鉴"
        lines.append(f"| 待定 | {p['title'][:50]} | {gis_rel} | 需人工确认 |")

    lines.extend([
        "",
        "## 5. 待人工确认的问题",
        "",
        "- 哪篇论文最适合主讲？",
        "- 哪些内容需要回看原文？",
        "- 哪些结论不能直接用于汇报？",
        "- 提取的信息是否准确？（标题/摘要/方法/GIS关联）",
        "",
        f"---",
        f"*生成时间: {now}。本文件由 weekly_digest_builder.py 轻量提取，仅供人工复核。*",
    ])

    return "\n".join(lines)


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="从日报轻量提取本周论文清单生成周组会摘要准备材料")
    parser.add_argument("--daily-dir", type=Path, required=True, help="日报目录路径")
    parser.add_argument("--output", type=Path, help="输出文件路径")
    parser.add_argument("--start-date", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="只预览不写入文件")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出文件")
    parser.add_argument("--max-files", type=int, default=20, help="最大扫描文件数")
    args = parser.parse_args()

    if not args.daily_dir.exists():
        print(f"Error: 日报目录不存在: {args.daily_dir}", file=sys.stderr)
        return 1

    # Date range
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else datetime.now()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else end_date - timedelta(days=7)
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = end_date.replace(hour=23, minute=59, second=59)

    # Output path
    output_dir = Path(__file__).resolve().parent.parent / "outputs" / "weekly_digest"
    today = datetime.now().strftime("%Y%m%d")
    output_path = args.output or (output_dir / f"weekly_digest_{today}.md")

    if args.dry_run:
        files = list_daily_files(args.daily_dir, start_date, end_date)
        print(f"[DRY-RUN] Daily dir: {args.daily_dir}")
        print(f"[DRY-RUN] Date range: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        print(f"[DRY-RUN] Found {len(files)} daily files to scan")
        print(f"[DRY-RUN] Max files: {args.max_files}")
        print(f"[DRY-RUN] Output path: {output_path}")
        print("[DRY-RUN] No files created.")
        return 0

    if not args.dry_run and output_path.exists() and not args.overwrite:
        print(f"输出文件已存在: {output_path}")
        print("如需覆盖，请使用 --overwrite")
        return 0

    content = build_digest(args.daily_dir, start_date, end_date, args.max_files)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
