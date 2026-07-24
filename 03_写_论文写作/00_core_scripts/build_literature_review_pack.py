#!/usr/bin/env python3
"""build_literature_review_pack.py — 多篇论文卡片合并为文献综述准备包

用法:
  python build_literature_review_pack.py --input cards.md --output pack.md
  python build_literature_review_pack.py --input-dir paper_cards/ --output pack.md
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


def ensure_utf8_console() -> None:
    """Best-effort UTF-8 console setup for Windows terminals."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def extract_papers_from_md(text: str) -> list[dict]:
    """Extract paper info from markdown with ## headers."""
    papers = []
    sections = re.split(r"\n(?=## )", text)
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split("\n")
        title = lines[0].lstrip("#").strip()
        papers.append({"title": title, "content": section.strip()})
    return papers


def generate_review_pack(papers: list[dict], output_path: Path) -> str:
    today = datetime.now().strftime("%Y%m%d")
    lines = [
        f"# 文献综述准备包 | {today}",
        "",
        "> AI 辅助草稿，需人工复核。不伪造引用。不确定的标注'需查证原文'。",
        "",
        "## 1. 论文清单",
        f"共 {len(papers)} 篇论文：",
        "",
    ]
    for i, p in enumerate(papers, 1):
        lines.append(f"{i}. {p['title']}")
    lines.extend([
        "",
        "## 2. 研究主题聚类",
        "（请根据论文内容手动归类）",
        "",
        "## 3. 方法比较",
        "| 论文 | 方法 | 数据 | 优点 | 局限 |",
        "|------|------|------|------|------|",
        "",
        "## 4. 研究空白",
        "1. **方法空白**:",
        "2. **数据空白**:",
        "3. **场景空白**:",
        "",
        "## 5. 可迁移到 GIS/遥感/空间分析的点",
        "| 论文 | 可迁移方法 | 迁移场景 | 可行性 |",
        "|------|----------|---------|--------|",
        "",
        "## 6. 文献综述段落草稿提示",
        "将以上信息提供给 AI 时，附上 Prompt: `03_写_论文写作/prompts/05_literature_review_builder.md`",
        "",
        "---",
        f"*生成: {today}。每个结论需标注来源论文。*",
    ])
    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="文献综述准备包生成")
    parser.add_argument("--input", type=Path, help="输入 Markdown 文件")
    parser.add_argument("--input-dir", type=Path, help="输入目录（多个 .md）")
    parser.add_argument("--output", type=Path, help="输出路径")
    args = parser.parse_args()

    if not args.input and not args.input_dir:
        print("Error: 需要 --input 或 --input-dir", file=sys.stderr)
        return 1

    papers = []
    if args.input and args.input.exists():
        text = args.input.read_text(encoding="utf-8")
        papers = extract_papers_from_md(text)
    if args.input_dir and args.input_dir.exists():
        for md_file in sorted(args.input_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            papers.extend(extract_papers_from_md(text))

    print(f"Extracted {len(papers)} papers")

    output_dir = Path(__file__).resolve().parent.parent / "outputs" / "literature_review_packs"
    today = datetime.now().strftime("%Y%m%d")
    output_path = args.output or (output_dir / f"{today}_literature_review_pack.md")

    report = generate_review_pack(papers, output_path)
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
