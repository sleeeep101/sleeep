#!/usr/bin/env python3
"""scan_ai_patterns.py — AI写作模式扫描（降AI腔诊断前处理）

用法:
  python scan_ai_patterns.py --input paper.md
  python scan_ai_patterns.py --input paper.md --output report.md --threshold 3
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def ensure_utf8_console() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# AI写作模式特征 — 从 anti_ai_tone_quality_checklist.md 提取
PATTERNS = {
    "template_connectors": {
        "label": "模板化连接词",
        "patterns": [
            r"首先.*其次.*最后",
            r"此外.*同时.*另一方面",
            r"综上所述",
            r"总而言之",
            r"值得注意的是",
            r"不难看出",
            r"由此可见",
        ],
        "advice": "减少机械连接词，用段落逻辑代替。每篇文章此类连接词不宜超过段数的30%。",
    },
    "empty_significance": {
        "label": "空泛意义表达",
        "patterns": [
            r"具有重要的.*意义",
            r"广阔的应用前景",
            r"为相关研究提供.*参考",
            r"具有.*的理论.*和实践.*价值",
            r"为.*提供了科学依据",
            r"具有.*重要.*价值",
            r"具有.*参考.*意义",
        ],
        "advice": "替换为具体说明：对谁有意义？什么意义？用于什么场景？",
    },
    "placeholder_evidence": {
        "label": "证据缺失表达",
        "patterns": [
            r"已有研究表明[^\[\(]*$",
            r"前人研究[^\[\(]*$",
        ],
        "advice": "每个'研究表明'后必须有具体引用。使用多行模式检查。",
    },
    "homogeneous_structure": {
        "label": "同质化段落结构",
        "patterns": [
            r"(^#{1,3} .+\n)(首先[^\n]+\n)(其次[^\n]+\n)(最后[^\n]+\n)",  # 多行
        ],
        "advice": "连续3段以上使用'首先-其次-最后'结构需要打破。",
        "multiline": True,
    },
    "weak_conclusion": {
        "label": "弱结论表达",
        "patterns": [
            r"表现出.*优势",
            r"效果良好",
            r"取得了较好的.*效果",
            r"具有一定的.*价值",
        ],
        "advice": "替换为定量指标：在XX指标上相比YY方法提升了ZZ%。",
    },
    "overly_smooth_causality": {
        "label": "过度平滑因果关系",
        "patterns": [
            r"从而.*进而.*最终",
            r"由于.*因此.*所以.*导致",
        ],
        "advice": "GIS研究中因果关系往往不完全线性，标注不确定性来源。",
    },
    "vague_terrain": {
        "label": "GIS/地形描述空泛（专项检查）",
        "patterns": [
            r"地形.*复杂[^，。]*[,，。]",
            r"地形.*多样[^，。]*[,，。]",
            r"呈现.*空间分异[^，。]*[,，。]",
            r"空间分布.*不均匀[^，。]*[,，。]",
        ],
        "advice": "补充定量描述：高程范围XX-XX m，平均坡度XX°，地形起伏度XX m。",
    },
}


def scan_text(text: str) -> list[dict]:
    findings = []
    for pattern_key, pattern_info in PATTERNS.items():
        for pat in pattern_info["patterns"]:
            flags = re.IGNORECASE
            if pattern_info.get("multiline"):
                flags |= re.MULTILINE | re.DOTALL
            for m in re.finditer(pat, text, flags):
                line_num = text[:m.start()].count("\n") + 1
                matched = m.group()[:120].replace("\n", "\\n")
                findings.append({
                    "line": line_num,
                    "category": pattern_info["label"],
                    "matched": matched,
                    "advice": pattern_info["advice"],
                })
    return findings


def generate_report(findings: list[dict], input_path: Path, threshold: int) -> str:
    by_category = Counter(f["category"] for f in findings)
    total = len(findings)

    lines = [
        "# AI写作模式扫描报告",
        f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"输入文件: {input_path}",
        f"总命中数: {total}",
        "",
        "## 类别分布",
        "| 类别 | 命中数 |",
        "|------|--------|",
    ]
    for cat, count in by_category.most_common():
        lines.append(f"| {cat} | {count} |")

    lines.extend([
        "",
        "## 逐条命中（按行号排序）",
        "| 行号 | 类别 | 命中文本 | 修改建议 |",
        "|------|------|---------|---------|",
    ])
    for f in sorted(findings, key=lambda x: x["line"]):
        if len(findings) > 50 and f["line"] > 50:
            # 截断：仅显示前50行命中的前50条
            break
        matched_short = f["matched"][:60] + ("..." if len(f["matched"]) > 60 else "")
        lines.append(f"| {f['line']} | {f['category']} | {matched_short} | {f['advice'][:50]}... |")

    if total == 0:
        lines.extend(["", "✅ 未检测到常见AI写作模式。但这不代表文字质量完美——仍需人工审查。"])

    lines.extend([
        "",
        "## 下一步",
        "1. 用提示词 `14_降AI腔但不造假_prompt.md` 对高命中段落做诊断和修改",
        "2. 参照 `AI整篇论文写作工作流/anti_ai_tone_quality_checklist.md` 逐项检查",
        "3. 重点修复: 空泛意义表达 > 模板化连接词 > GIS空泛描述",
        "",
        "> 本扫描仅作为写作质量辅助参考，不改变原文。所有修改需人工审核。",
    ])
    return "\n".join(lines)


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="AI写作模式扫描")
    parser.add_argument("--input", type=Path, required=True, help="论文 Markdown 文件")
    parser.add_argument("--output", type=Path, help="输出报告路径（可选）")
    parser.add_argument("--threshold", type=int, default=3, help="单类别命中阈值（默认3）")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: 文件不存在: {args.input}", file=sys.stderr)
        return 1

    text = args.input.read_text(encoding="utf-8")
    findings = scan_text(text)
    report = generate_report(findings, args.input, args.threshold)

    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"\n报告已保存: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
