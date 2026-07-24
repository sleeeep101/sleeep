"""
import_manual_claude.py — 导入 Claude 手动阅读产出。

当 PDF 无法自动解析时（扫描件/编码损坏/依赖失败），
将 Claude 手工阅读/分析笔记导入为结构化数据。

用法:
  from pdf_ingest import import_claude_reading
  result = import_claude_reading("my_reading.md", "path/to/original.pdf")

输入格式:
  Claude 阅读笔记 (.md)，需包含论文分析内容。
  支持以下字段检测:
    - 标题 / 作者 / 来源
    - 一句话总结
    - 研究问题
    - 方法流程
    - 主要结论
    - 局限
    - 可迁移的点

输出:
  data/pdf_library/manual_claude_processed/<name>/
    paper.md              # 阅读全文 (含免责声明)
    metadata.json         # 元信息 (manual_claude 引擎)
    chunks.jsonl          # 分块
    extraction_report.md  # 质量报告
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════════════

def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent

PROJECT_ROOT = _get_project_root()
DEFAULT_INPUT = PROJECT_ROOT / "data" / "pdf_library" / "manual_claude_input"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "pdf_library" / "manual_claude_processed"


# ═══════════════════════════════════════════════════════════════════
# 字段解析
# ═══════════════════════════════════════════════════════════════════

_FIELD_PATTERNS = [
    ("title",       [r"(?i)^#+\s*(标题|论文标题|题目)\s*[:：]", r"(?i)^\*\*?(标题|论文标题|题目)\*\*?\s*[:：]"]),
    ("authors",     [r"(?i)^#+\s*(作者|作者列表)\s*[:：]", r"(?i)^\*\*?(作者|作者列表)\*\*?\s*[:：]"]),
    ("year",        [r"(?i)^#+\s*(年份|发表年份)\s*[:：]", r"(?i)^\*\*?(年份|发表年份)\*\*?\s*[:：]"]),
    ("source",      [r"(?i)^#+\s*(来源|期刊|会议|DOI|arXiv)\s*[:：]", r"(?i)^\*\*?(来源|期刊|会议|DOI|arXiv)\*\*?\s*[:：]"]),
    ("summary",     [r"(?i)^#+\s*(一句话总结|总结|核心观点|TL;DR)\s*[:：]", r"(?i)^\*\*?(一句话总结|总结|核心观点|TL;DR)\*\*?\s*[:：]"]),
    ("question",    [r"(?i)^#+\s*(研究问题|研究目标|问题)\s*[:：]", r"(?i)^\*\*?(研究问题|研究目标|问题)\*\*?\s*[:：]"]),
    ("data_source", [r"(?i)^#+\s*(数据来源|数据|数据源)\s*[:：]", r"(?i)^\*\*?(数据来源|数据|数据源)\*\*?\s*[:：]"]),
    ("method",      [r"(?i)^#+\s*(方法|方法流程|研究方法|核心方法)\s*[:：]", r"(?i)^\*\*?(方法|方法流程|研究方法|核心方法)\*\*?\s*[:：]"]),
    ("innovation",  [r"(?i)^#+\s*(创新点|创新|贡献)\s*[:：]", r"(?i)^\*\*?(创新点|创新|贡献)\*\*?\s*[:：]"]),
    ("results",     [r"(?i)^#+\s*(结果|主要结果|结论|主要结论)\s*[:：]", r"(?i)^\*\*?(结果|主要结果|结论|主要结论)\*\*?\s*[:：]"]),
    ("limitations", [r"(?i)^#+\s*(局限|局限性|不足|问题)\s*[:：]", r"(?i)^\*\*?(局限|局限性|不足|问题)\*\*?\s*[:：]"]),
    ("transfer",    [r"(?i)^#+\s*(可迁移|迁移|迁移到|可迁移到)\s*[:：]", r"(?i)^\*\*?(可迁移|迁移|迁移到|可迁移到)\*\*?\s*[:：]"]),
    ("keywords",    [r"(?i)^#+\s*(关键词|关键字)\s*[:：]", r"(?i)^\*\*?(关键词|关键字)\*\*?\s*[:：]"]),
]


def _parse_claude_output(text: str) -> Dict[str, str]:
    """从 Claude 阅读输出中解析结构化字段。"""
    fields: Dict[str, str] = {}
    for field_name, patterns in _FIELD_PATTERNS:
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                # 获取匹配行之后的内容，直到下一个 ## 或空行分隔符
                start = m.end()
                # 尝试取到下一个 ## 标题
                next_section = re.search(r"\n(?=##|\*\*?(?:标题|作者|年份|来源|总结|研究|数据|方法|创新|结果|局限|迁移|关键词))", text[start:])
                if next_section:
                    content = text[start:start + next_section.start()].strip()
                else:
                    # 取到文本末尾，但最多 5000 字符
                    content = text[start:start + 5000].strip()
                fields[field_name] = content
                break

    # 如果没有匹配到结构化字段，把全文作为 body
    if not fields:
        fields["body"] = text.strip()

    return fields


# ═══════════════════════════════════════════════════════════════════
# 文本分块
# ═══════════════════════════════════════════════════════════════════

def _chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ═══════════════════════════════════════════════════════════════════
# 质量评分
# ═══════════════════════════════════════════════════════════════════

def _assess_reading_quality(fields: Dict[str, str], text: str) -> Tuple[str, str]:
    """评估 Claude 阅读产出的质量。

    Returns:
        (quality_level, reason)
    """
    text_len = len(text)

    # 检查关键字段
    key_fields = ["summary", "method", "results"]
    filled = sum(1 for f in key_fields if f in fields and len(fields[f]) > 20)

    has_full_text = text_len > 10000 and filled >= 2
    has_summary = text_len > 1000 and filled >= 1
    is_minimal = text_len < 500 or filled == 0

    if has_full_text:
        return "high", f"内容完整 ({text_len}字符), {filled}/{len(key_fields)} 关键字段"
    elif has_summary:
        return "medium", f"摘要级内容 ({text_len}字符), {filled}/{len(key_fields)} 关键字段"
    elif is_minimal:
        return "low", f"内容过少 ({text_len}字符), 仅 {filled}/{len(key_fields)} 关键字段"
    else:
        return "medium", f"部分内容 ({text_len}字符), {filled}/{len(key_fields)} 关键字段"


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

def import_claude_reading(
    source_path: str | Path,
    pdf_path: str = "",
    *,
    output_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """导入 Claude 手动阅读产出。

    Args:
        source_path: Claude 阅读笔记 .md 文件路径
        pdf_path: 原始 PDF 文件路径 (可选)
        output_dir: 输出目录 (默认: data/pdf_library/manual_claude_processed/)

    Returns:
        dict with status, output_dir, char_count, chunks, has_full_text, has_summary
    """
    source = Path(source_path)
    if not source.exists():
        return {"status": "failed", "error": f"文件不存在: {source_path}"}

    # 读取 Claude 输出
    try:
        raw_text = source.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"status": "failed", "error": f"读取失败: {exc}"}

    if not raw_text.strip():
        return {"status": "failed", "error": "输入文件为空"}

    # 解析字段
    fields = _parse_claude_output(raw_text)

    # 质量评估
    quality, quality_reason = _assess_reading_quality(fields, raw_text)

    # 输出目录
    if output_dir:
        out_root = Path(output_dir)
    else:
        out_root = DEFAULT_OUTPUT

    out_name = source.stem
    out_dir = out_root / out_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # 分块
    chunks = _chunk_text(raw_text)

    # ── 写入 paper.md (含免责声明) ──
    md_header = "<!--\n"
    md_header += f"  source: {source}\n"
    if pdf_path:
        md_header += f"  original_pdf: {pdf_path}\n"
    md_header += f"  method: manual_claude\n"
    md_header += f"  extraction_mode: manual_claude\n"
    md_header += f"  confidence: {quality}\n"
    md_header += f"  manual_claude_used: true\n"
    md_header += "  disclaimer: |\n"
    md_header += "    本文由 Claude 手动阅读生成。\n"
    md_header += "    内容可能不完整、存在理解偏差或遗漏关键细节。\n"
    md_header += "    仅供参考，不应视为论文原文的完整准确复现。\n"
    md_header += "    重要结论请以论文原文为准。\n"
    md_header += "-->\n\n"
    md_header += raw_text
    (out_dir / "paper.md").write_text(md_header, encoding="utf-8")

    # ── metadata.json ──
    metadata = {
        "source_file": str(source),
        "original_pdf": pdf_path or "",
        "engine_used": "manual_claude",
        "extraction_mode": "manual_claude",
        "confidence": quality,
        "quality_reason": quality_reason,
        "char_count": len(raw_text),
        "detected_fields": list(fields.keys()),
        "manual_claude_used": True,
        "ocr_required": False,
        "imported_at": datetime.now().isoformat(),
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ── chunks.jsonl ──
    if chunks:
        with open(out_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                f.write(json.dumps({"index": i, "text": chunk}, ensure_ascii=False) + "\n")

    # ── extraction_report.md ──
    report = [
        "# Claude Manual Reading Import Report\n",
        f"- **Source:** `{source}`",
        f"- **Original PDF:** `{pdf_path or 'N/A'}`",
        f"- **Method:** manual_claude",
        f"- **Confidence:** {quality}",
        f"- **Characters:** {len(raw_text)}",
        f"- **Chunks:** {len(chunks)}",
        f"- **Detected Fields:** {', '.join(fields.keys()) or 'none'}",
    ]
    if quality_reason:
        report.append(f"- **Quality Note:** {quality_reason}")
    report.append("\n> ⚠️ 本文由 Claude 手动阅读生成，仅供参考。重要结论请以论文原文为准。")
    (out_dir / "extraction_report.md").write_text("\n".join(report), encoding="utf-8")

    return {
        "status": "success",
        "output_dir": str(out_dir),
        "char_count": len(raw_text),
        "chunks": len(chunks),
        "has_full_text": quality == "high",
        "has_summary": quality in ("high", "medium"),
        "confidence": quality,
        "quality_reason": quality_reason,
        "detected_fields": list(fields.keys()),
    }


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Import Claude Manual Paper Reading")
    parser.add_argument("--source", required=True, help="Claude 阅读输出 .md 文件路径")
    parser.add_argument("--pdf", default="", help="原始 PDF 路径 (可选)")
    parser.add_argument("--output", help="自定义输出目录")
    args = parser.parse_args()

    result = import_claude_reading(args.source, args.pdf, output_dir=args.output)

    print(f"\nResult: {result['status']}")
    if result["status"] == "success":
        print(f"  Output: {result['output_dir']}")
        print(f"  Chars: {result['char_count']}")
        print(f"  Chunks: {result['chunks']}")
        print(f"  Full text: {result['has_full_text']}")
        print(f"  Has summary: {result['has_summary']}")
        print(f"  Confidence: {result.get('confidence', '?')}")
        if result.get("detected_fields"):
            print(f"  Fields: {', '.join(result['detected_fields'])}")
    else:
        print(f"  Error: {result.get('error', '?')}")

    sys.exit(0 if result["status"] == "success" else 1)
