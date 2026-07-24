# Quick Start — Write 写作系统

## 5 分钟上手

### 1. 检查一段中文论文草稿
```bash
python write/scripts/check_chinese_grammar.py --input your_draft.md --output report.md
```

### 2. 查询某个任务对应的 Prompt
```bash
python write/scripts/write_router.py --task grammar
python write/scripts/write_router.py --task polish
python write/scripts/write_router.py --task gis_style
```

### 3. 生成组会材料准备包
```bash
python 组会/scripts/build_group_meeting_pack.py --daily-dir ../reports/daily/
```

### 4. 检查环境
```bash
python write/scripts/check_write_env.py --root .
```

### 5. 盘点系统生成了什么
```bash
python write/scripts/inventory_write_system.py --root write/
```

## 核心概念

- **Prompt** = 可以直接复制给 AI 用的提示词 → `write/prompts/`
- **Skill** = Claude Code/Codex 可调用的技能 → `write/skills/`
- **Script** = 可以命令行运行的脚本 → `write/scripts/`
- **Checklist** = 人工检查清单 → `write/checklists/`
- **Template** = 填写模板 → `write/templates/`

## Windows 中文乱码处理

如果控制台中文乱码，优先使用输出到文件的方式：

```bash
python write\scripts\check_chinese_grammar.py --input draft.md --output report.md
```

如果仍需在控制台查看中文，PowerShell 可尝试：

```powershell
$env:PYTHONUTF8=1
```

## pycorrector 可选增强

基础规则检查不需要额外依赖。如需增强中文纠错：

```bash
pip install pycorrector
```

安装前后探测：

```bash
# 安装前
python write/scripts/probe_pycorrector.py

# 安装后验证返回结构
python write/scripts/probe_pycorrector.py --output write/outputs/grammar_reports/pycorrector_probe_report.md
```

指定检查引擎：

```bash
python write/scripts/check_chinese_grammar.py --input draft.md --output report.md --engine rules
python write/scripts/check_chinese_grammar.py --input draft.md --output report.md --engine auto
python write/scripts/check_chinese_grammar.py --input draft.md --output report.md --engine pycorrector
```

## 规则库调整

规则文件：`write/config/grammar_rules.json`

```bash
# 使用自定义规则
python write/scripts/check_chinese_grammar.py --input draft.md --output report.md --rules-config custom_rules.json
```

误报较多时优先调整 `vague_words`、`template_patterns`、`colloquial_words`。

## 与 AI 协作

将 `write/prompts/` 中的文件内容复制给 AI（Claude/Codex/ChatGPT），附上你的论文草稿。
AI 会按 Prompt 要求输出检查报告或修改建议。
