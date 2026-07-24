#!/usr/bin/env python3
"""ingest_pdf.py — PDF 摄入 CLI (委托至统一 pdf_ingest 模块)

用法:
  python scripts/ingest_pdf.py --pdf "path/to/file.pdf"
  python scripts/ingest_pdf.py --dir "path/to/pdf_folder"
  python scripts/ingest_pdf.py --engine auto
  python scripts/ingest_pdf.py --engine pymupdf4llm
  python scripts/ingest_pdf.py --force
  python scripts/ingest_pdf.py --list-engines
"""

import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pdf_ingest import ingest_pdf as _ingest_pdf, ingest_dir as _ingest_dir, list_available


def main():
    parser = argparse.ArgumentParser(description="PDF Ingestion Pipeline")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pdf", help="Single PDF file path")
    group.add_argument("--dir", help="Directory containing PDFs")
    parser.add_argument("--engine", default="auto",
                       choices=["auto", "pymupdf4llm", "fallback_text", "manual_claude"])
    parser.add_argument("--output", help="Custom output directory")
    parser.add_argument("--force", action="store_true", help="Force reprocess even if already done")
    parser.add_argument("--list-engines", action="store_true", help="List available engines and exit")
    args = parser.parse_args()

    if args.list_engines:
        available = list_available()
        print("Available engines:", ", ".join(available))
        return

    if not args.pdf and not args.dir:
        parser.error("one of --pdf or --dir is required")

    if args.pdf:
        print(f"Ingesting: {args.pdf}")
        print(f"Engine: {args.engine}")
        result = _ingest_pdf(args.pdf, engine=args.engine, output_dir=args.output, force=args.force)
        print(f"\nResult: {result['status']}")
        if result["status"] in ("success", "low_quality"):
            print(f"  Output: {result['output_dir']}")
            print(f"  Method: {result.get('method', '?')}")
            print(f"  Chars: {result.get('char_count', 0)}")
            print(f"  Chunks: {result.get('chunks', 0)}")
            print(f"  Confidence: {result.get('confidence', '?')}")
            print(f"  Reading Level: {result.get('reading_level', '?')}")
        else:
            print(f"  Error: {result.get('error', result.get('reason', '?'))}")

    elif args.dir:
        results = _ingest_dir(args.dir, engine=args.engine, output_dir=args.output, force=args.force)
        success = sum(1 for r in results if r["status"] in ("success", "low_quality"))
        skipped = sum(1 for r in results if r["status"] == "skipped")
        failed = sum(1 for r in results if r["status"] == "failed")
        print(f"\nDone: {success} success, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
