#!/usr/bin/env python3
"""write_router.py — 写作任务路由

用法:
  python write_router.py --task grammar
  python write_router.py --task polish
  python write_router.py --task literature_review
  python write_router.py --task group_meeting
  python write_router.py --task advisor_questions
  python write_router.py --task gis_style
"""
from __future__ import annotations

import argparse
import sys

def ensure_utf8_console() -> None:
    """Best-effort UTF-8 console setup for Windows terminals."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import sys
from pathlib import Path

ROUTES = {
    "grammar": {
        "prompt": "01_chinese_grammar_check.md",
        "description": "中文论文语病检查（错别字/语法/标点/的地得/空泛词/过长句）",
        "input_format": "Markdown 或 TXT 文件（论文草稿）",
        "output_format": "Markdown 检查报告",
        "script": "check_chinese_grammar.py",
    },
    "polish": {
        "prompt": "02_academic_polish_chinese.md",
        "description": "中文学术润色（不改变原意，提升学术表达质量）",
        "input_format": "论文段落（Markdown/TXT）",
        "output_format": "润色报告 + 修改后版本",
        "script": None,
    },
    "logic": {
        "prompt": "03_logic_and_argument_check.md",
        "description": "逻辑论证检查（概念/因果/证据链/推理）",
        "input_format": "论文段落",
        "output_format": "逻辑问题清单",
        "script": None,
    },
    "reduce_template": {
        "prompt": "04_reduce_template_style.md",
        "description": "减少模板化/空泛/机械表达",
        "input_format": "论文段落",
        "output_format": "模板化表达清单 + 修改后版本",
        "script": None,
    },
    "literature_review": {
        "prompt": "05_literature_review_builder.md",
        "description": "文献综述辅助（多篇论文卡片→综述草稿）",
        "input_format": "论文卡片目录或 Markdown 文件",
        "output_format": "文献综述准备包",
        "script": "build_literature_review_pack.py",
    },
    "paper_section": {
        "prompt": "06_abstract_intro_method_result_discussion.md",
        "description": "论文各章节写作辅助（摘要/引言/方法/结果/讨论）",
        "input_format": "论文草稿或章节主题",
        "output_format": "章节写作建议",
        "script": None,
    },
    "gis_style": {
        "prompt": "07_gis_remote_sensing_academic_style.md",
        "description": "GIS/遥感/空间分析学术表达",
        "input_format": "GIS/遥感方向论文草稿",
        "output_format": "GIS方向表达建议",
        "script": None,
    },
    "group_meeting": {
        "prompt": "组会/prompts/08_group_meeting_outline.md",
        "description": "组会汇报提纲生成（12页PPT大纲+导师追问+讨论问题）",
        "input_format": "论文列表或 weekly digest",
        "output_format": "组会材料准备包",
        "script": "组会/scripts/build_group_meeting_pack.py",
    },
    "advisor_questions": {
        "prompt": "组会/prompts/09_advisor_question_generator.md",
        "description": "导师可能追问生成",
        "input_format": "PPT大纲或论文摘要",
        "output_format": "导师追问清单 + 可回答版本",
        "script": None,
    },
    "citation": {
        "prompt": "10_reference_and_citation_check.md",
        "description": "参考文献与引用检查",
        "input_format": "论文草稿",
        "output_format": "引用问题清单",
        "script": "check_reference_placeholders.py",
    },
    "format": {
        "prompt": "11_markdown_to_docx_pdf_check.md",
        "description": "输出格式检查（Markdown→DOCX/PDF）",
        "input_format": "Markdown 草稿",
        "output_format": "格式检查清单",
        "script": None,
    },
    "writing_card": {
        "prompt": "12_writing_learning_card.md",
        "description": "写作学习卡片提取",
        "input_format": "论文段落或优秀表达",
        "output_format": "写作学习卡片",
        "script": "extract_writing_cards.py",
    },
    "full_paper": {
        "prompt": "13_整篇论文初稿生成_prompt.md",
        "description": "整篇论文初稿生成（基于真实材料，缺失处标记【需补充】）",
        "input_format": "研究题目/问题/数据/方法/图表/文献笔记/结论",
        "output_format": "完整论文初稿 + 缺失材料清单 + 人工确认项",
        "script": "check_material_completeness.py",
    },
    "deai": {
        "prompt": "14_降AI腔但不造假_prompt.md",
        "description": "降低AI腔（不改事实/数据/引用，只改善写作质量）",
        "input_format": "论文段落（可含AI检测器结果）",
        "output_format": "诊断报告 + 修改稿 + 修改说明",
        "script": "scan_ai_patterns.py",
    },
    "aidetect": {
        "prompt": "15_AI检测器结果诊断_prompt.md",
        "description": "AI检测器结果诊断（区分真问题与误判）",
        "input_format": "论文段落 + AI检测器反馈结果",
        "output_format": "逐段诊断 + 修改建议 + 误判说明",
        "script": None,
    },
    "fraud_audit": {
        "prompt": "16_防学术造假审计_prompt.md",
        "description": "防学术造假审计（文献/数据/图表/方法/结论全面核查）",
        "input_format": "论文全文或部分章节",
        "output_format": "8项审计报告 + 红旗清单 + 修正建议",
        "script": None,
    },
}


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="写作任务路由")
    parser.add_argument("--task", required=True, choices=list(ROUTES.keys()), help="任务类型")
    args = parser.parse_args()

    route = ROUTES[args.task]
    # Root is academic-workflow directory
    root = Path(__file__).resolve().parent.parent.parent
    write_prompts = root / "03_写_论文写作" / "prompts"
    zuhui_prompts = root / "组会" / "prompts"
    write_scripts = root / "03_写_论文写作" / "00_core_scripts"
    zuhui_scripts = root / "组会" / "scripts"

    # Resolve prompt path — check if it's a write or 组会 path
    prompt_rel = route["prompt"]
    if "组会" in prompt_rel or "zuHui" in prompt_rel:
        prompt_path = root / prompt_rel if not Path(prompt_rel).is_absolute() else Path(prompt_rel)
    else:
        prompt_path = write_prompts / prompt_rel

    # Resolve script path
    script_rel = route.get("script")
    script_path = None
    if script_rel:
        if "组会" in script_rel or "zuHui" in script_rel:
            script_path = root / script_rel if not Path(script_rel).is_absolute() else Path(script_rel)
        else:
            script_path = write_scripts / script_rel
    print(f"# 写作任务路由: {args.task}")
    print(f"## 任务说明")
    print(f"- 描述: {route['description']}")
    print(f"- 输入格式: {route['input_format']}")
    print(f"- 输出格式: {route['output_format']}")
    print(f"- Prompt 文件: {prompt_path}")
    if script_path:
        print(f"- 辅助脚本: {script_path}")
        print(f"- 运行: python {script_path} --help")
    print()
    print(f"## 使用方法")
    print(f"将 Prompt 文件内容复制给 AI，附上你的论文草稿或需求。")
    print(f"Prompt 文件路径: {prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
