# 组会 Scripts

组会相关脚本统一放在此目录。

| 文件 | 用途 |
|------|------|
| build_group_meeting_pack.py | 从日报/论文卡片生成组会材料准备包。支持 --dry-run、--overwrite |
| weekly_digest_builder.py | 从 reports/daily 轻量提取论文清单，生成周摘要准备材料。支持 --dry-run、--overwrite、日期范围 |

## 运行方式

```bash
# 生成组会材料包（预览模式）
python 组会/scripts/build_group_meeting_pack.py --daily-dir ../reports/daily/ --dry-run

# 生成组会材料包（正式运行）
python 组会/scripts/build_group_meeting_pack.py --daily-dir ../reports/daily/ --output 组会/outputs/group_meeting_packs/pack.md

# 从日报提取周摘要
python 组会/scripts/weekly_digest_builder.py --daily-dir ../reports/daily/ --dry-run
python 组会/scripts/weekly_digest_builder.py --daily-dir ../reports/daily/ --start-date 2026-06-01 --end-date 2026-06-04 --output 组会/outputs/weekly_digest/digest.md
```

## 归属说明

组会脚本统一放在此目录。write/ 中的 write_router.py 通过绝对路径指向本目录的脚本。
