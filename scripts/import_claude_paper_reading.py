#!/usr/bin/env python3
"""import_claude_paper_reading.py — 导入 Claude 手动阅读产出 (委托至统一 pdf_ingest 模块)

用法:
  python scripts/import_claude_paper_reading.py --source "path/to/claude_output.md" --pdf "path/to/original.pdf"
"""

import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdf_ingest import import_claude_reading


def main():
    parser = argparse.ArgumentParser(description="Import Claude Manual Paper Reading")
    parser.add_argument("--source", required=True, help="Path to Claude output .md file")
    parser.add_argument("--pdf", default="", help="Path to original PDF (optional)")
    parser.add_argument("--output", help="Custom output directory")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"ERROR: Source file not found: {args.source}")
        sys.exit(1)

    print(f"Importing Claude reading: {source.name}")
    result = import_claude_reading(args.source, args.pdf, output_dir=args.output)

    print(f"\nResult: {result['status']}")
    if result["status"] == "success":
        print(f"  Output: {result['output_dir']}")
        print(f"  Chars: {result['char_count']}")
        print(f"  Chunks: {result['chunks']}")
        print(f"  Full text: {result.get('has_full_text', False)}")
        print(f"  Has summary: {result.get('has_summary', False)}")
        print(f"  Confidence: {result.get('confidence', '?')}")
    else:
        print(f"  Error: {result.get('error', '?')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
