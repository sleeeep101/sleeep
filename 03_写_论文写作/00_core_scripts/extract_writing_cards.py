#!/usr/bin/env python3
"""extract_writing_cards.py — 从论文段落提取写作学习卡片

用法:
  python extract_writing_cards.py --input paragraph.md --output cards.md
"""
from __future__ import annotations

import argparse
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


def generate_card(text: str, source: str, output_path: Path) -> str:
    today = datetime.now().strftime("%Y%m%d")
    content = f"""# 写作学习卡片 | {today}

## 来源
{source}

## 原文
{text[:500]}

## 写作功能
（这段话在论文中的作用：引出gap/解释方法选择/过渡/总结/对比/...）

## 句式结构
（可学习的句式模板 — 填空式，不照抄）

## GIS/遥感可迁移表达
（能否用在GIS/遥感论文中？如何改？）

## 不建议照抄的部分
（术语/语境/学科特定的部分）

## 我的替代表达
（用自己的话改写）
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return content


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="写作学习卡片提取")
    parser.add_argument("--input", type=Path, help="输入文本文件")
    parser.add_argument("--source", default="未标注", help="来源（论文标题等）")
    parser.add_argument("--output", type=Path, help="输出路径")
    args = parser.parse_args()

    if not args.input or not args.input.exists():
        print("Error: 需要 --input", file=sys.stderr)
        return 1

    text = args.input.read_text(encoding="utf-8")
    output_dir = Path(__file__).resolve().parent.parent / "outputs" / "writing_cards"
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or (output_dir / f"{today}_writing_card.md")

    card = generate_card(text, args.source, output_path)
    print(card)
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
