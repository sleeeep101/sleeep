#!/usr/bin/env python3
"""check_material_completeness.py — 论文生成前材料完整性检查

用法:
  python check_material_completeness.py --input materials.md
  python check_material_completeness.py --input materials.md --output report.md
"""
from __future__ import annotations

import argparse
import re
import sys
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


REQUIRED_FIELDS = {
    "research_question": {
        "label": "研究问题/目标",
        "patterns": [r"研究问题", r"研究目标", r"研究目的", r"research question", r"research objective"],
        "min_chars": 30,
        "severity": "critical",
    },
    "study_area": {
        "label": "研究区信息",
        "patterns": [r"研究区", r"研究区域", r"study area", r"经纬度", r"地理位置", r"坐标"],
        "min_chars": 20,
        "severity": "critical",
    },
    "data_sources": {
        "label": "数据来源",
        "patterns": [r"数据来源", r"数据获取", r"数据源", r"DEM.*分辨", r"遥感.*分辨", r"data source", r"分辨率"],
        "min_chars": 30,
        "severity": "critical",
    },
    "methods": {
        "label": "研究方法",
        "patterns": [r"研究方法", r"技术路线", r"方法流程", r"method", r"算法", r"分析.*步骤"],
        "min_chars": 50,
        "severity": "critical",
    },
    "figures_tables": {
        "label": "图表说明",
        "patterns": [r"Fig\.\d|图\d|Tab\.\d|表\d|图 \d|表 \d|Figure \d|Table \d"],
        "min_matches": 1,
        "severity": "high",
    },
    "literature": {
        "label": "文献笔记",
        "patterns": [r"DOI", r"doi", r"arXiv", r"文献", r"\[\d+\]", r"\(\w+.*\d{4}\)", r"et al"],
        "min_matches": 3,
        "severity": "high",
    },
    "claim_evidence": {
        "label": "主张—证据矩阵",
        "patterns": [r"主张.*证据", r"证据矩阵", r"claim.*evidence", r"evidence.*claim"],
        "min_matches": 1,
        "severity": "critical",
    },
    "findings": {
        "label": "初步结论/发现",
        "patterns": [r"结论", r"发现", r"结果表明", r"finding", r"conclusion", r"主要贡献"],
        "min_chars": 20,
        "severity": "high",
    },
    "title": {
        "label": "研究题目",
        "patterns": [r"题目", r"标题", r"title", r"论文题目", r"基于.*研究"],
        "min_chars": 5,
        "severity": "critical",
    },
}


def check_materials(text: str) -> dict:
    results = {}
    for key, field in REQUIRED_FIELDS.items():
        found = False
        evidence = []
        for pat in field["patterns"]:
            matches = list(re.finditer(pat, text, re.IGNORECASE))
            if matches:
                if "min_matches" in field:
                    if len(matches) >= field["min_matches"]:
                        found = True
                else:
                    # Check surrounding context char count
                    for m in matches:
                        start = max(0, m.start() - 50)
                        end = min(len(text), m.end() + 200)
                        context = text[start:end]
                        if len(context) >= field["min_chars"]:
                            found = True
                            evidence.append(context[:100].strip())
                            break
        results[key] = {
            "label": field["label"],
            "found": found or bool(evidence),
            "severity": field["severity"],
            "evidence": evidence[:2],
        }
    return results


def generate_report(results: dict, input_path: Path) -> str:
    critical_missing = [v for v in results.values() if v["severity"] == "critical" and not v["found"]]
    high_missing = [v for v in results.values() if v["severity"] == "high" and not v["found"]]
    total = len(results)
    found = sum(1 for v in results.values() if v["found"])
    score = int(found / total * 100)

    lines = [
        "# 材料完整性检查报告",
        f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"输入文件: {input_path.name} (local path redacted)",
        f"完整性评分: {score}/100",
        "",
        f"## 总览",
        f"| 状态 | 数量 |",
        f"|------|------|",
        f"| ✅ 材料充足 | {found} |",
        f"| 🔴 关键缺失 | {len(critical_missing)} |",
        f"| 🟡 建议补充 | {len(high_missing)} |",
        "",
        "## 逐项检查",
        "| 材料 | 状态 | 严重度 | 证据 |",
        "|------|------|--------|------|",
    ]
    for key, r in results.items():
        status = "✅" if r["found"] else ("🔴" if r["severity"] == "critical" else "🟡")
        ev = r["evidence"][0][:60] + "..." if r["evidence"] else "—"
        lines.append(f"| {r['label']} | {status} | {r['severity']} | {ev} |")

    if critical_missing:
        lines.append("")
        lines.append("## 🔴 生成前必须补充")
        for v in critical_missing:
            lines.append(f"- [ ] **{v['label']}** — 缺失此项将导致论文关键部分无法生成")

    if high_missing:
        lines.append("")
        lines.append("## 🟡 建议补充")
        for v in high_missing:
            lines.append(f"- [ ] **{v['label']}** — 可在生成后补充，但可能影响初稿质量")

    if score >= 80:
        lines.append("")
        lines.append("## ✅ 结论: 材料基本充足，可以开始生成")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="论文生成前材料完整性检查")
    parser.add_argument("--input", type=Path, required=True, help="材料 Markdown 文件")
    parser.add_argument("--output", type=Path, help="输出报告路径（可选）")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Error: 文件不存在: {args.input}", file=sys.stderr)
        return 1

    text = args.input.read_text(encoding="utf-8")
    results = check_materials(text)
    report = generate_report(results, args.input)

    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"\n报告已保存: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
