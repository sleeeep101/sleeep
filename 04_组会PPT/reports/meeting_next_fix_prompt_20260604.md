# 组会系统后续修复提示词

> 生成日期: 2026-06-04 | 基于: meeting_rehome_report

## 约束
- 只允许修改 `组会/`、`write/`、`scripts/__pycache__/`
- 不改 daily_paper_curator.py / 长期知识库.md / ETF
- 修改前备份到 `backup_library/meeting_fix_YYYYMMDD_HHMMSS/`

---

## 修复项 1：build_group_meeting_pack.py 增加 --dry-run

**问题**: 脚本无 dry-run 模式，无法预览将要生成的内容
**影响**: 首次使用可能不确定输出格式
**修改文件**: `组会/scripts/build_group_meeting_pack.py`
**备份位置**: `backup_library/meeting_fix_YYYYMMDD_HHMMSS/`
**验证命令**: `python 组会/scripts/build_group_meeting_pack.py --daily-dir reports/daily --dry-run`
**回滚方式**: 从备份恢复

---

## 修复项 2：实现 weekly_digest_builder.py 轻量版

**问题**: 日报→组会周摘要目前纯手动
**影响**: 每周需要手动翻日报提取论文
**修改文件**: 新建 `组会/scripts/weekly_digest_builder.py`
**内容**: 扫描 reports/daily/ 本周日报，提取论文标题列表，输出 Markdown 片段
**备份位置**: N/A (新建)
**验证命令**: `python 组会/scripts/weekly_digest_builder.py --daily-dir ../reports/daily --output 组会/outputs/weekly_digest/test_weekly.md`
**回滚方式**: 删除新建文件

---

## 不在此次修复范围
- 自动生成 PPTX: 依赖重，ppt-speech-writer 已覆盖讲稿部分
- 组会成果自动写入长期知识库: 需用户确认方案
- 组会调度自动化: 9月前手动运行即可
