#!/usr/bin/env python3
"""check_chinese_grammar.py — 中文论文草稿质量检查

用法:
  python check_chinese_grammar.py --input draft.md --output report.md
  python check_chinese_grammar.py --input draft.md --output report.md --engine pycorrector
  python check_chinese_grammar.py --input draft.md --output report.md --engine rules --show-engine
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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


# ── 默认规则库（可被 grammar_rules.json 覆盖） ─────────────────

_DEFAULT_RULES = {
    "vague_words": [
        "重要", "显著", "一定程度", "较好", "较大", "比较", "很多",
        "一些", "不少", "可能", "大概", "似乎", "相当", "非常",
        "极其", "十分", "特别", "尤其", "更加", "更为", "较为",
    ],
    "template_patterns": [
        ["随着.{1,30}的发展", "模板化句式：'随着……的发展'"],
        ["在.{1,30}的背景下", "模板化句式：'在……背景下'"],
        ["具有重要的意义", "空泛表述：'具有重要意义'（建议具体说明什么意义）"],
        ["一定程度上", "空泛限定：'一定程度上'（建议给出具体程度或删除）"],
        ["诸多研究表明", "虚假引用嫌疑：'诸多研究表明'（建议引用具体文献）"],
        ["学术界普遍认为", "虚假引用嫌疑：'学术界普遍认为'（建议引用具体学者）"],
        ["不仅.{1,50}而且", "模板句式：'不仅……而且……'（确认是否有实质对立）"],
    ],
    "colloquial_words": [
        "搞", "弄", "整", "啥", "咋", "嘛", "吧", "呗",
        "得了", "算了", "行了", "对了",
    ],
    "max_sentence_length": 80,
    "severe_sentence_length": 120,
    "de_di_de_patterns": [
        ["的(?=地|得)", "疑似'的/地/得'混用（该用'地'或'得'的地方写了'的'）"],
        ["(?<=[^\\x00-\\x7f])地(?=的|得)", "疑似'的/地/得'混用"],
        ["得(?=的|地$)", "疑似'的/地/得'混用"],
    ],
}

# Runtime rule storage
VAGUE_WORDS: list[str] = []
TEMPLATE_PATTERNS: list[tuple] = []
COLLOQUIAL_WORDS: list[str] = []
DE_DI_DE_PATTERNS: list[tuple] = []
MAX_SENTENCE_LENGTH = 80
SEVERE_SENTENCE_LENGTH = 120


def load_rules_config(config_path: Path | None) -> bool:
    """Load grammar rules from JSON config file. Returns True on success."""
    global VAGUE_WORDS, TEMPLATE_PATTERNS, COLLOQUIAL_WORDS
    global DE_DI_DE_PATTERNS, MAX_SENTENCE_LENGTH, SEVERE_SENTENCE_LENGTH

    if config_path is None or not config_path.exists():
        _apply_defaults()
        return False

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: 配置文件解析失败 ({e})，使用内置默认规则。", file=sys.stderr)
        _apply_defaults()
        return False

    VAGUE_WORDS = data.get("vague_words", _DEFAULT_RULES["vague_words"])
    COLLOQUIAL_WORDS = data.get("colloquial_words", _DEFAULT_RULES["colloquial_words"])
    MAX_SENTENCE_LENGTH = data.get("max_sentence_length", _DEFAULT_RULES["max_sentence_length"])
    SEVERE_SENTENCE_LENGTH = data.get("severe_sentence_length", _DEFAULT_RULES["severe_sentence_length"])

    tp = data.get("template_patterns", _DEFAULT_RULES["template_patterns"])
    TEMPLATE_PATTERNS = []
    for item in tp:
        if isinstance(item, dict):
            TEMPLATE_PATTERNS.append((item["pattern"], item["desc"]))
        elif isinstance(item, list) and len(item) >= 2:
            TEMPLATE_PATTERNS.append((item[0], item[1]))

    ddp = data.get("de_di_de_patterns", _DEFAULT_RULES["de_di_de_patterns"])
    DE_DI_DE_PATTERNS = []
    for item in ddp:
        if isinstance(item, dict):
            DE_DI_DE_PATTERNS.append((item["pattern"], item["desc"]))
        elif isinstance(item, list) and len(item) >= 2:
            DE_DI_DE_PATTERNS.append((item[0], item[1]))

    return True


def _apply_defaults() -> None:
    global VAGUE_WORDS, TEMPLATE_PATTERNS, COLLOQUIAL_WORDS
    global DE_DI_DE_PATTERNS, MAX_SENTENCE_LENGTH, SEVERE_SENTENCE_LENGTH
    VAGUE_WORDS = _DEFAULT_RULES["vague_words"]
    COLLOQUIAL_WORDS = _DEFAULT_RULES["colloquial_words"]
    MAX_SENTENCE_LENGTH = _DEFAULT_RULES["max_sentence_length"]
    SEVERE_SENTENCE_LENGTH = _DEFAULT_RULES["severe_sentence_length"]
    TEMPLATE_PATTERNS = [(item[0], item[1]) for item in _DEFAULT_RULES["template_patterns"]]
    DE_DI_DE_PATTERNS = [(item[0], item[1]) for item in _DEFAULT_RULES["de_di_de_patterns"]]

# Load defaults at import time
_apply_defaults()

PUNCTUATION_PATTERNS = [
    (r"[a-zA-Z0-9][，。；：、！？]", "中英文标点混用（英文后接中文标点）"),
    (r"[一-鿿][,.!?;:]", "中英文标点混用（中文后接英文标点）"),
]


def check_long_sentences(text: str) -> list[dict]:
    issues = []
    sentences = re.split(r"[。！？\n]", text)
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if not sent:
            continue
        char_count = len(re.sub(r"[a-zA-Z0-9\s]", "", sent)) + len(re.findall(r"[a-zA-Z0-9]+", sent))
        if char_count > SEVERE_SENTENCE_LENGTH:
            issues.append({"type": "严重过长句", "position": f"第{i+1}句", "text": sent[:80] + "...", "count": char_count})
        elif char_count > MAX_SENTENCE_LENGTH:
            issues.append({"type": "过长句", "position": f"第{i+1}句", "text": sent[:80] + "...", "count": char_count})
    return issues


def check_vague_words(text: str) -> list[dict]:
    issues = []
    for word in VAGUE_WORDS:
        for m in re.finditer(re.escape(word), text):
            ctx_start = max(0, m.start() - 15)
            ctx_end = min(len(text), m.end() + 15)
            issues.append({
                "type": "疑似空泛词",
                "position": f"字符{m.start()}",
                "text": text[ctx_start:ctx_end],
                "word": word,
            })
    return issues


def check_templates(text: str) -> list[dict]:
    issues = []
    for pattern, desc in TEMPLATE_PATTERNS:
        for m in re.finditer(pattern, text):
            issues.append({
                "type": "模板化/空泛表达",
                "position": f"字符{m.start()}",
                "text": m.group(),
                "desc": desc,
            })
    return issues


def check_spoken(text: str) -> list[dict]:
    issues = []
    for word in COLLOQUIAL_WORDS:
        for m in re.finditer(re.escape(word), text):
            ctx_start = max(0, m.start() - 10)
            ctx_end = min(len(text), m.end() + 10)
            issues.append({
                "type": "口语化表达",
                "position": f"字符{m.start()}",
                "text": text[ctx_start:ctx_end],
                "word": word,
            })
    return issues


def run_pycorrector_check(text: str) -> tuple[list[dict], str | None, str]:
    """Run pycorrector and return (issues, corrected_text, status).

    Returns:
        issues: standardized issue list
        corrected_text: full corrected text (or None if unavailable)
        status: "ok" | "no_results" | "error: <message>" | "unrecognized_format"
    """
    try:
        import pycorrector
    except ImportError:
        return [], None, "error: pycorrector not installed"

    try:
        raw = pycorrector.correct(text)
    except Exception as e:
        return [], None, f"error: pycorrector.correct() 调用失败: {type(e).__name__}: {e}"

    # ── Format detection ──
    corrected_text = None
    details = None

    if isinstance(raw, tuple):
        # Format A: (corrected_text, details)
        if len(raw) >= 2:
            corrected_text = str(raw[0]) if raw[0] is not None else None
            details = raw[1]
        elif len(raw) == 1:
            corrected_text = str(raw[0])
    elif isinstance(raw, str):
        corrected_text = raw
    elif isinstance(raw, dict):
        corrected_text = raw.get("corrected_text", raw.get("target", raw.get("result", str(raw))))
        details = raw.get("details", raw.get("errors", raw.get("items")))
    elif isinstance(raw, list):
        # Assume list of corrections
        details = raw
    else:
        return [], str(raw)[:500], "unrecognized_format"

    # ── Build issues ──
    issues = []

    # If we have corrected_text, compare with original
    if corrected_text and corrected_text != text:
        issues.append({
            "type": "pycorrector纠错",
            "position": "全文",
            "text": f"原文({len(text)}字) → 修正({len(corrected_text)}字)",
            "word": f"修正后: {corrected_text[:100]}{'...' if len(corrected_text) > 100 else ''}",
            "desc": "pycorrector 全句修正",
        })

    # If we have details list
    if details is not None and isinstance(details, (list, tuple)):
        for item in details:
            try:
                if isinstance(item, dict):
                    issues.append({
                        "type": "pycorrector纠错",
                        "position": str(item.get("position", item.get("start", item.get("pos", "?")))),
                        "text": str(item.get("wrong", item.get("src", item.get("source", item.get("原句", ""))))),
                        "word": str(item.get("correct", item.get("tgt", item.get("target", item.get("建议", ""))))),
                        "desc": str(item.get("message", item.get("info", item.get("msg", "")))),
                    })
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    issues.append({
                        "type": "pycorrector纠错",
                        "position": "?",
                        "text": str(item[0]),
                        "word": str(item[1]),
                        "desc": "",
                    })
            except Exception:
                pass

    if not issues and corrected_text is None:
        return [], None, "unrecognized_format"

    status = "ok" if issues else "no_results"
    return issues, corrected_text, status


def generate_report(text: str, output_path: Path, engine: str, input_path: Path) -> str:
    all_issues = []
    pycorrector_issues = []
    engine_used = "rules"

    pycorrector_status = ""
    if engine in ("auto", "pycorrector"):
        pycorrector_issues, corrected, pyc_status = run_pycorrector_check(text)
        pycorrector_status = pyc_status
        if pycorrector_issues:
            engine_used = "pycorrector"
            all_issues.extend(pycorrector_issues)
        if corrected and not pycorrector_issues:
            # pycorrector ran but returned no structured issues — still mark as pycorrector
            engine_used = "pycorrector (corrected only)"

    if engine == "pycorrector" and not pycorrector_issues and pycorrector_status.startswith("error"):
        lines.append(f"**pycorrector 错误**: {pycorrector_status}")
        lines.append("已回退到规则检查。")
        engine_used = "rules"
    elif engine_used == "rules" or (engine == "auto" and not pycorrector_issues):
        all_issues.extend(check_long_sentences(text))
        all_issues.extend(check_vague_words(text))
        all_issues.extend(check_templates(text))
        all_issues.extend(check_spoken(text))
        engine_used = "rules"

    lines = [
        "# 中文论文草稿质量检查报告",
        "",
        f"- 输入文件: {input_path}",
        f"- 输出文件: {output_path}",
        f"- 实际检查引擎: {engine_used}",
        f"- 是否需要人工复核: 是",
        "- 注意: AI/规则辅助检查不能替代人工判断，不得伪造数据、引用或结果。",
        "",
    ]

    if pycorrector_issues:
        lines.extend([
            "## pycorrector 检查结果",
            "",
            "| 序号 | 原文 | 建议修改 | 位置/置信信息 |",
            "|---:|------|---------|--------|",
        ])
        for i, issue in enumerate(pycorrector_issues, 1):
            lines.append(f"| {i} | {issue.get('text', '')} | {issue.get('word', '')} | {issue.get('desc', issue.get('position', ''))} |")
        lines.append("")

    lines.extend([
        f"## 总体评估",
        f"- 检查字数: {len(text)}",
        f"- 发现问题总数: {len(all_issues)}",
        f"- 总体风险: {'高' if len(all_issues) > 30 else '中' if len(all_issues) > 10 else '低'}",
        "",
        "## 问题清单（规则检查）" if engine_used == "pycorrector" else "## 问题清单",
        "",
        "| 序号 | 类型 | 位置 | 原文片段 | 说明 |",
        "|------|------|------|---------|------|",
    ])
    rule_issues = [i for i in all_issues if i.get("type") != "pycorrector纠错"]
    if not rule_issues and engine_used == "pycorrector":
        lines.append("| - | - | - | 规则检查未运行（pycorrector 已处理） | - |")
    for i, issue in enumerate(rule_issues, 1):
        lines.append(f"| {i} | {issue['type']} | {issue['position']} | {issue.get('text', issue.get('word', ''))} | {issue.get('desc', issue.get('word', ''))} |")

    lines.extend([
        "",
        "## 建议",
        "- 所有问题需人工复核，机器检查可能误判",
        "- 术语、公式、代码块中的\"问题\"可忽略",
    ])
    if engine_used == "rules":
        lines.append("- 建议安装 pycorrector 获得更精准的检查: `pip install pycorrector`")

    lines.extend([
        "",
        "> AI 辅助草稿，需人工复核",
    ])

    report = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return report


def main() -> int:
    ensure_utf8_console()

    parser = argparse.ArgumentParser(description="中文论文草稿质量检查")
    parser.add_argument("--input", required=True, type=Path, help="输入 .md 或 .txt 文件")
    parser.add_argument("--output", required=True, type=Path, help="输出 Markdown 报告")
    parser.add_argument("--engine", choices=["auto", "pycorrector", "rules"], default="auto",
                        help="检查引擎: auto(自动), pycorrector(强制), rules(规则)")
    parser.add_argument("--show-engine", action="store_true", help="在报告顶部显示实际使用的引擎")
    parser.add_argument("--use-pycorrector", action="store_true", help="(已弃用) 请使用 --engine pycorrector")
    parser.add_argument("--rules-config", type=Path,
                        default=Path(__file__).resolve().parent.parent / "config" / "grammar_rules.json",
                        help="规则配置文件路径 (默认: write/config/grammar_rules.json)")
    args = parser.parse_args()

    # Load rules
    if not load_rules_config(args.rules_config):
        if args.rules_config and args.rules_config.exists():
            print(f"Warning: 配置文件加载失败，使用内置默认规则: {args.rules_config}", file=sys.stderr)

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    # Backward compat
    if args.use_pycorrector:
        args.engine = "pycorrector"

    text = args.input.read_text(encoding="utf-8")

    # Check pycorrector availability for forced mode
    if args.engine == "pycorrector":
        try:
            import pycorrector  # noqa: F401
        except ImportError:
            print("你指定了 --engine pycorrector，但当前环境未安装 pycorrector。")
            print("请运行：pip install pycorrector")
            print("或改用：--engine rules")
            return 2

    if args.engine == "auto":
        try:
            import pycorrector  # noqa: F401
        except ImportError:
            pass  # Will fall back to rules

    report = generate_report(text, args.output, args.engine, args.input)
    print(f"Report saved: {args.output}")
    if args.show_engine:
        engine_actual = "pycorrector" if any("pycorrector" in line for line in report.split("\n")[:15]) else "rules"
        print(f"Actual engine: {engine_actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
