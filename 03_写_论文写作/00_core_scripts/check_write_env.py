#!/usr/bin/env python3
"""check_write_env.py — Write 系统环境检查

用法:
  python check_write_env.py --root <LOCAL_PATH>
  python check_write_env.py --root <LOCAL_PATH> --output env_report.md
"""
from __future__ import annotations

import argparse
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


KEY_FILES = [
    "03_写_论文写作/README.md",
    "03_写_论文写作/SKILL.md",
    "03_写_论文写作/config/project_integration_matrix.csv",
    "03_写_论文写作/config/capability_map.json",
    "03_写_论文写作/config/license_risk_register.md",
    "03_写_论文写作/prompts/00_master_write_router.md",
    "03_写_论文写作/prompts/01_chinese_grammar_check.md",
    "03_写_论文写作/prompts/07_gis_remote_sensing_academic_style.md",
    "03_写_论文写作/prompts/13_整篇论文初稿生成_prompt.md",
    "03_写_论文写作/prompts/14_降AI腔但不造假_prompt.md",
    "03_写_论文写作/prompts/15_AI检测器结果诊断_prompt.md",
    "03_写_论文写作/prompts/16_防学术造假审计_prompt.md",
    "03_写_论文写作/00_core_scripts/check_chinese_grammar.py",
    "03_写_论文写作/00_core_scripts/write_router.py",
    "03_写_论文写作/00_core_scripts/check_reference_placeholders.py",
    "03_写_论文写作/00_core_scripts/inventory_write_system.py",
    "03_写_论文写作/checklists/paper_writing_quality_checklist.md",
    "03_写_论文写作/checklists/ai_assisted_writing_ethics_checklist.md",
    "03_写_论文写作/02_写作模板/paper_section_template.md",
    "03_写_论文写作/tests/sample_bad_chinese_paragraph.md",
    "03_写_论文写作/AI整篇论文写作工作流/README.md",
    "03_写_论文写作/AI整篇论文写作工作流/anti_academic_fraud_checklist.md",
    "03_写_论文写作/AI整篇论文写作工作流/日常使用简版提示词.md",
    "组会/scripts/build_group_meeting_pack.py",
    "组会/prompts/08_group_meeting_outline.md",
    "组会/prompts/09_advisor_question_generator.md",
]


def check_python() -> dict:
    return {
        "version": sys.version,
        "executable": sys.executable,
        "platform": sys.platform,
    }


def check_encoding() -> dict:
    return {
        "default_encoding": sys.getdefaultencoding(),
        "stdout_encoding": getattr(sys.stdout, "encoding", "unknown"),
        "stderr_encoding": getattr(sys.stderr, "encoding", "unknown"),
        "filesystem_encoding": sys.getfilesystemencoding(),
    }


def check_optional_deps() -> list[dict]:
    deps = []
    for name, pip_name, note in [
        ("pycorrector", "pycorrector", "中文文本纠错工具包"),
        ("pptx", "python-pptx", "PPTX 操作"),
        ("docx", "python-docx", "DOCX 生成"),
        ("PIL", "Pillow", "图像处理"),
    ]:
        try:
            __import__(name)
            deps.append({"name": pip_name, "status": "已安装", "note": note})
        except ImportError:
            deps.append({"name": pip_name, "status": "未安装", "note": note})
    return deps


def check_key_files(root: Path) -> list[dict]:
    results = []
    for rel in KEY_FILES:
        full = root / rel
        results.append({
            "file": rel,
            "exists": "是" if full.exists() else "**否**",
        })
    return results


def generate_report(root: Path, output_path: Path | None) -> str:
    py_info = check_python()
    enc_info = check_encoding()
    deps = check_optional_deps()
    files = check_key_files(root)

    lines = [
        "# Write 系统环境检查报告",
        f"## 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"## 根目录: {root}",
        "",
        "## 1. Python 环境",
        f"- Python 版本: {py_info['version'].split()[0]}",
        f"- 完整版本: {py_info['version'].split()[0]}",
        f"- 解释器路径: {py_info['executable']}",
        f"- 平台: {py_info['platform']}",
        f"- 默认编码: {enc_info['default_encoding']}",
        f"- stdout 编码: {enc_info['stdout_encoding']}",
        f"- stderr 编码: {enc_info['stderr_encoding']}",
        f"- 文件系统编码: {enc_info['filesystem_encoding']}",
        "",
        "## 2. 可选依赖",
        "| 依赖 | 状态 | 说明 |",
        "|---|---|---|",
    ]
    for d in deps:
        lines.append(f"| {d['name']} | {d['status']} | {d['note']} |")

    lines.extend([
        "",
        "## 3. 关键文件",
        "| 文件 | 是否存在 |",
        "|---|---|",
    ])
    for f in files:
        lines.append(f"| {f['file']} | {f['exists']} |")

    missing = [f['file'] for f in files if f['exists'] == '**否**']
    lines.extend([
        "",
        "## 4. 建议",
    ])
    if missing:
        lines.append(f"**缺失文件 ({len(missing)}个):**")
        for m in missing:
            lines.append(f"- {m}")
    else:
        lines.append("- 所有关键文件均存在。")

    not_installed = [d for d in deps if d['status'] == '未安装']
    if not_installed:
        lines.append("- 建议安装以下可选依赖增强功能:")
        for d in not_installed:
            lines.append(f"  - `pip install {d['name']}` ({d['note']})")

    if enc_info['stdout_encoding'] and 'utf' not in str(enc_info['stdout_encoding']).lower():
        lines.append("- 控制台编码非 UTF-8，中文输出可能乱码。建议输出到文件或执行 `chcp 65001`。")

    report = "\n".join(lines)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    return report


def main() -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="Write 系统环境检查")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent.parent)
    parser.add_argument("--output", type=Path, help="输出 Markdown 报告路径")
    args = parser.parse_args()

    report = generate_report(args.root, args.output)
    print(report)
    if args.output:
        print(f"\n报告已保存: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
