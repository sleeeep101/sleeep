# 01_读 / 00_core_scripts — 核心脚本位置

> daily_paper_curator.py 及相关脚本当前仍保留在 `scripts/` 原路径，
> 因为定时任务和硬编码路径依赖。后续稳定后可迁移。

## 当前脚本路径

| 脚本 | 原路径 |
|------|--------|
| daily_paper_curator.py | `scripts/daily_paper_curator.py` |
| fulltext_utils.py | `scripts/fulltext_utils.py` |
| paper_source_utils.py | `scripts/paper_source_utils.py` |
| backfill_paper_sources.py | `scripts/backfill_paper_sources.py` |
| audit_knowledge_base_reading_level.py | `scripts/audit_knowledge_base_reading_level.py` |
| run_paper_curator.bat | `scripts/run_paper_curator.bat` |

## 迁移条件
满足以下条件后可迁移：
1. 定时任务稳定运行 ≥ 2 周
2. 所有相对路径引用已检查并更新
3. 测试脚本在新位置能正常生成日报
