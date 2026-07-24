# 组会系统后续修复提示词（weekly_digest 之后）

> 生成日期: 2026-06-04 | 基于: dryrun_weeklydigest_fix_report

## 约束
- 只允许修改 `组会/`
- 不改 daily_paper_curator.py / 长期知识库.md / ETF / write
- 修改前备份

---

## 修复项 1：build_group_meeting_pack 增加 --input-weekly-digest

**问题**: 当前只能从 --daily-dir 直接读日报，无法从已有的 weekly_digest 文件生成组会包
**影响**: 需要两次运行（weekly_digest_builder → 再 build_group_meeting_pack with --daily-dir）
**修改文件**: `组会/scripts/build_group_meeting_pack.py`
**备份位置**: `backup_library/meeting_fix_YYYYMMDD_HHMMSS/`
**验证命令**:
```bash
python 组会/scripts/weekly_digest_builder.py --daily-dir reports/daily --output 组会/outputs/weekly_digest/test.md --overwrite
python 组会/scripts/build_group_meeting_pack.py --input-weekly-digest 组会/outputs/weekly_digest/test.md --output 组会/outputs/group_meeting_packs/test_pack.md --dry-run
```
**回滚方式**: 从备份恢复

---

## 不在此次修复范围
- 自动写长期知识库
- 自动生成 PPTX
- 大型调度系统
- Web UI
- 修改 daily_paper_curator.py
- 修改 ETF
