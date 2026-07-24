#!/usr/bin/env python3
"""build_group_meeting_pack.py — 从日报/论文卡片生成组会材料准备包

用法:
  python build_group_meeting_pack.py --daily-dir ../reports/daily/
  python build_group_meeting_pack.py --weekly-digest digest.md
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


def extract_papers_from_daily(daily_dir: Path, days_back: int = 7) -> list[dict]:
    """Extract paper titles from daily report MD files."""
    papers = []
    cutoff = datetime.now() - timedelta(days=days_back)
    for md_file in sorted(daily_dir.glob("*.md")):
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
        if mtime < cutoff:
            continue
        text = md_file.read_text(encoding="utf-8")
        # Extract paper titles (## headers with paper-like content)
        for match in re.finditer(r"^#{1,3}\s+(.+)", text, re.MULTILINE):
            title = match.group(1).strip()
            if len(title) > 20 and not title.startswith(("#", ">", "-", "|")):
                papers.append({
                    "title": title,
                    "source": md_file.name,
                    "date": mtime.strftime("%Y-%m-%d"),
                })
    return papers


def extract_papers_from_digest(digest_path: Path) -> list[dict]:
    """Extract paper titles from a weekly digest MD file."""
    papers = []
    text = digest_path.read_text(encoding="utf-8")
    # Match table rows: | 1 | 2026-06-04 | Title | source | status |
    for match in re.finditer(r"\|\s*\d+\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|", text):
        date_str = match.group(1)
        title = match.group(2).strip()
        if len(title) > 10 and not title.startswith(("#", "论文标题", "---")):
            papers.append({
                "title": title[:100],
                "source": digest_path.name,
                "date": date_str,
            })
    # Also match per-paper detail sections
    for match in re.finditer(r"### 论文 \d+：(.+)", text):
        title = match.group(1).strip()
        if len(title) > 10 and title not in [p["title"] for p in papers]:
            papers.append({
                "title": title[:100],
                "source": digest_path.name,
                "date": "",
            })
    return papers


def generate_pack(papers: list[dict], output_path: Path) -> str:
    """Generate a group meeting preparation pack."""
    today = datetime.now().strftime("%Y-%m-%d")
    week_num = datetime.now().isocalendar()[1]

    lines = [
        f"# 组会材料准备包 | {today} (W{week_num})",
        "",
        "> 本文件为 AI 辅助生成的组会材料草稿，需人工复核。",
        "> 不确定的内容标注'未确认'。不编造论文内容或数据。",
        "",
        "---",
        "",
        "## 1. 本周论文清单",
        "",
    ]

    if papers:
        lines.append("| # | 标题 | 来源 | 日期 |")
        lines.append("|---|------|------|------|")
        for i, p in enumerate(papers[:10], 1):
            lines.append(f"| {i} | {p['title'][:80]} | {p['source']} | {p['date']} |")
    else:
        lines.append("（未提取到论文，请手动填写）")

    lines.extend([
        "",
        "## 2. 推荐汇报主线",
        "（请根据实际阅读内容提炼，一句话概括本周汇报的核心方向性主题）",
        "",
        "## 3. PPT 大纲（12页建议）",
        "",
        "| 页码 | 页面主题 | 核心观点 | 材料来源 | 状态 |",
        "|------|---------|---------|---------|------|",
        "| 1 | 标题页 | 本周汇报主题 + 方向关键词 | — | 待填写 |",
        "| 2 | 本周关注的问题 | 我想解决什么问题 | — | 待填写 |",
        "| 3 | 本周读了什么 | X篇论文，核心围绕Y方向 | §1 | 待填写 |",
        "| 4 | 前沿动态1 | （结论式标题） | — | 待填写 |",
        "| 5 | 前沿动态2 | （结论式标题） | — | 待填写 |",
        "| 6 | 可迁移方法1 | （方法→原场景→目标场景） | — | 待填写 |",
        "| 7 | 可迁移方法2 | （方法→原场景→目标场景） | — | 待填写 |",
        "| 8 | 本周实际进展 | 完成了什么 | — | 待填写 |",
        "| 9 | 关键发现或认知变化 | 我原来以为X，这周发现是Y | — | 待填写 |",
        "| 10 | 遇到的问题 | 卡在哪里、试过什么 | — | 待填写 |",
        "| 11 | 已尝试的方案 | 试过A/B/C，效果/结果是？ | — | 待填写 |",
        "| 12 | 需要讨论 + 下周计划 | 2-3个具体问题 + 3项下周任务 | — | 待填写 |",
        "",
        "## 4. 导师可能追问（至少准备5个）",
        "",
        "| # | 方向 | 可能追问 | 我能回答吗 | 还缺什么 |",
        "|---|------|---------|----------|---------|",
        "| 1 | 研究问题 | 你的研究问题定义够清晰吗？ | 待填写 | 待填写 |",
        "| 2 | 方法 | 你选择的方法为什么可靠？ | 待填写 | 待填写 |",
        "| 3 | 数据 | 数据够吗？来源可靠吗？ | 待填写 | 待填写 |",
        "| 4 | 对比 | 和已有研究比，差异在哪？ | 待填写 | 待填写 |",
        "| 5 | 下一步 | 下一步验证怎么做？优先级？ | 待填写 | 待填写 |",
        "",
        "## 5. 讨论问题（2-3个）",
        "",
        "1. **问题**: （具体、有上下文）",
        "   - 为什么需要讨论: ",
        "   - 希望获得什么指导: ",
        "",
        "## 6. 下周计划（不超过3项）",
        "",
        "| # | 任务 | 预计时间 | 最小完成标准 |",
        "|---|------|---------|------------|",
        "| 1 | | | |",
        "| 2 | | | |",
        "| 3 | | | |",
        "",
        "---",
        f"*生成时间: {today}。AI 辅助草稿，需人工复核。*",
    ])

    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="生成组会材料准备包")
    parser.add_argument("--daily-dir", type=Path, help="日报目录路径")
    parser.add_argument("--weekly-digest", type=Path, help="周摘要文件路径（使用已生成的周摘要作为输入）")
    parser.add_argument("--input-weekly-digest", type=Path, help="从已有的周摘要文件读取论文（等同于 --weekly-digest）")
    parser.add_argument("--output", type=Path, help="输出路径（默认自动生成）")
    parser.add_argument("--days-back", type=int, default=7, help="回溯天数")
    parser.add_argument("--dry-run", action="store_true", help="只预览不写入文件")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出文件")
    args = parser.parse_args()

    # Normalize --input-weekly-digest → --weekly-digest
    if args.input_weekly_digest:
        args.weekly_digest = args.input_weekly_digest

    if not args.daily_dir and not args.weekly_digest:
        print("Error: 需要 --daily-dir、--weekly-digest 或 --input-weekly-digest", file=sys.stderr)
        return 1

    output_dir = Path(__file__).resolve().parent.parent / "outputs" / "group_meeting_packs"
    today = datetime.now().strftime("%Y%m%d")
    output_path = args.output or (output_dir / f"{today}_group_meeting_pack.md")

    if args.dry_run:
        source = f"daily-dir: {args.daily_dir}" if args.daily_dir else f"weekly-digest: {args.weekly_digest}"
        print(f"[DRY-RUN] Input source: {source}")
        print(f"[DRY-RUN] Days back: {args.days_back}")
        print(f"[DRY-RUN] Output path: {output_path}")
        print(f"[DRY-RUN] Expected sections: 1.论文清单 2.汇报主线 3.PPT大纲 4.导师追问 5.讨论问题 6.下周计划")
        if args.daily_dir and args.daily_dir.exists():
            papers = extract_papers_from_daily(args.daily_dir, args.days_back)
            print(f"[DRY-RUN] Would extract ~{len(papers)} papers from daily reports")
        if args.weekly_digest and args.weekly_digest.exists():
            papers = extract_papers_from_digest(args.weekly_digest)
            print(f"[DRY-RUN] Would extract ~{len(papers)} papers from weekly digest")
        print("[DRY-RUN] No files created.")
        return 0

    if output_path.exists() and not args.overwrite:
        print(f"输出文件已存在: {output_path}")
        print("如需覆盖，请使用 --overwrite")
        return 0

    if args.overwrite and output_path.exists():
        print(f"覆盖已有文件: {output_path}")

    papers = []
    if args.weekly_digest and args.weekly_digest.exists():
        papers = extract_papers_from_digest(args.weekly_digest)
        print(f"Extracted {len(papers)} papers from weekly digest: {args.weekly_digest}")
    elif args.daily_dir and args.daily_dir.exists():
        papers = extract_papers_from_daily(args.daily_dir, args.days_back)
        print(f"Extracted {len(papers)} papers from daily reports")

    report = generate_pack(papers, output_path)
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
