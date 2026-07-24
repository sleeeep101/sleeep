#!/usr/bin/env python3
"""check_reference_placeholders.py — 检查论文草稿中的引用占位符问题

用法:
  python check_reference_placeholders.py --input draft.md --output report.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def ensure_utf8_console() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PATTERNS = [
    (r"\[待引用\]", "引用占位符: [待引用]"),
    (r"\[TODO.*citation.*\]", "引用占位符: TODO citation"),
    (r"\(作者.*年份\?\)", "引用占位符: (作者, 年份?)"),
    (r"已有研究表明(?!.*\d{4})", "疑似无来源: '已有研究表明'无具体引用"),
    (r"诸多研究表明(?!.*\d{4})", "疑似无来源: '诸多研究表明'无具体引用"),
    (r"学术界普遍认为(?!.*\d{4})", "疑似无来源: '学术界普遍认为'无具体引用"),
    (r"文献表明(?!.*\d{4})", "疑似无来源: '文献表明'无具体引用"),
]


def check(text: str, output_path: Path) -> str:
    issues = []
    for pattern, desc in PATTERNS:
        for m in re.finditer(pattern, text):
            ctx_start = max(0, m.start() - 30)
            ctx_end = min(len(text), m.end() + 30)
            issues.append({
                "type": desc,
                "text": text[ctx_start:ctx_end].replace("\n", " "),
            })

    lines = [
        "# 引用占位符检查报告",
        f"## 发现 {len(issues)} 个问题",
    ]
    for i, issue in enumerate(issues, 1):
        lines.append(f"{i}. **{issue['type']}**: ...{issue['text']}...")

    lines.append("\n> 所有引用需人工确认。不确定的标注'需查证原文'。")

    report = "\n\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="引用占位符检查")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        return 1

    text = args.input.read_text(encoding="utf-8")
    report = check(text, args.output)
    print(f"Saved: {args.output}")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
