# 后续修复提示词 — academic-workflow 系统测试复盘

> 生成日期: 2026-06-04
> 基于: full_system_test_report + group_meeting_test_report + write_test_report
> 目标: 最小修复，不重构，不新增大依赖

## 约束
- 只允许修改 `write/` 和 `scripts/__pycache__/`
- 不改 daily_paper_curator.py / 长期知识库.md / 组会/ / ETF
- 修改前备份到 `backup_library/write_fix_YYYYMMDD_HHMMSS/`
- 不做规避检测 / 论文代写 / 绕过查重

---

## 修复项 1：补全 write/prompts 中缺失的 Prompt 文件引用

**问题**: write_router.py 中 `group_meeting` 和 `advisor_questions` 任务指向 `组会/prompts/`，但 `00_master_write_router.md` 表格中部分引用路径为相对路径。

**影响**: 用户按路由表直接打开文件时可能找不到

**修改文件**: `write/prompts/00_master_write_router.md`

**备份位置**: `backup_library/write_fix_YYYYMMDD_HHMMSS/`

**修改内容**: 确认路由表中组会和追问两行的文件路径与实际文件位置一致

**验证命令**:
```bash
python write/scripts/write_router.py --task group_meeting
python write/scripts/write_router.py --task advisor_questions
```

**回滚方式**: 从备份恢复

---

## 修复项 2：确认 inventory_write_system.py 可遍历 write/ 和 组会/scripts/

**问题**: inventory 只盘点 write/ 目录，不显示已移至组会的组会脚本

**影响**: 需要手动检查组会/scripts 状态

**修改文件**: `write/scripts/inventory_write_system.py`

**备份位置**: 同上

**修改内容**: 增加可选参数 `--include-meeting`，启用时同时盘点 `../组会/scripts/` 和 `../组会/prompts/`

**验证命令**:
```bash
python write/scripts/inventory_write_system.py --root write --include-meeting
```

**回滚方式**: 从备份恢复

---

## 修复项 3：validate grammar_rules.json 加载失败信息

**问题**: 当 grammar_rules.json 格式错误时，提示信息可能不够明确

**影响**: 用户无法快速定位 JSON 语法错误

**修改文件**: `write/scripts/check_chinese_grammar.py`

**备份位置**: 同上

**修改内容**: 在 load_rules_config() 的 JSON 解析异常处理中，增加具体行号和错误位置提示（使用 json.JSONDecodeError 的属性）

**验证命令**:
```bash
# 故意创建格式错误的 rules 文件
echo "{" > write/config/test_bad_rules.json
python write/scripts/check_chinese_grammar.py --input write/tests/sample_bad_chinese_paragraph.md --output write/outputs/grammar_reports/test_bad_config.md --rules-config write/config/test_bad_rules.json --engine rules 2>&1
```

**回滚方式**: 从备份恢复

---

## 不在此次修复范围的已知问题

1. pycorrector 未安装 — 用户自行决定安装时机
2. 日报→周摘要自动提取 — 属于新增功能，非bug修复
3. 组会→长期知识库自动沉淀 — 属于新增功能
4. Windows 下 LibreOffice 渲染 — 属于 ppt-speech-writer 的环境依赖问题
5. 组会/ 和 write/ 的组会脚本跨目录 — 是用户明确指令的结果
