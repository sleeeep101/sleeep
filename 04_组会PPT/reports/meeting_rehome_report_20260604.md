# 组会内容统一归属迁移报告

> 日期: 2026-06-04 | 执行方式: 只读审查 → 最小迁移 → 引用修复 → 验证

## 1. 执行结论
**已完成。** 组会相关内容已全部归入 `组会/`，write/ 无组会实质内容残留，路径引用已修复。

## 2. 备份位置
`<LOCAL_PATH>` (148 files)

## 3. 从 write 迁移到 组会 的内容

| 原路径 | 新路径 | 动作 | 备注 |
|--------|--------|------|------|
| `write/outputs/group_meeting_test_report_2026-06-04.md` | `组会/reports/group_meeting_test_report_2026-06-04.md` | 复制 | 已在write保留原文件 |

## 4. 已在组会中确认归位的内容

| 路径 | 类型 | 备注 |
|------|------|------|
| 组会/prompts/08_group_meeting_outline.md | Prompt | ✅ 前次迁移 |
| 组会/prompts/09_advisor_question_generator.md | Prompt | ✅ 前次迁移 |
| 组会/prompts/README.md | 索引 | **本次新建** |
| 组会/skills/group-meeting-writing/SKILL.md | Skill | ✅ 前次迁移 |
| 组会/scripts/build_group_meeting_pack.py | 脚本 | ✅ 前次迁移 |
| 组会/scripts/README.md | 索引 | **本次新建** |
| 组会/checklists/ (5 files) | 检查清单 | ✅ 全部已归位 |
| 组会/templates/ (7 files) | 模板 | ✅ 全部已归位 |
| 组会/reports/ | 报告目录 | **本次新建** |
| 组会/outputs/group_meeting_packs/ | 输出目录 | **本次新建** |

## 5. 未迁移内容

| 路径 | 原因 |
|------|------|
| write/prompts/08_group_meeting_outline.md | 已不存在（前次迁移已删除源文件） |
| write/prompts/09_advisor_question_generator.md | 已不存在（前次迁移已删除源文件） |
| write/skills/group-meeting-writing/ | 已不存在（前次迁移已删除源目录） |
| write/scripts/build_group_meeting_pack.py | 已不存在（前次迁移已删除源文件） |

> 所有组会实质内容在前序任务中已完成迁移。本次只做收尾工作。

## 6. 修改的引用

| 文件 | 修改内容 |
|------|---------|
| `write/scripts/write_router.py` | 路径解析：组会路径指向 `root/组会/`，非组会路径指向 `root/write/` |
| `write/prompts/00_master_write_router.md` | 增加"组会相关内容已统一归入 ../组会/"说明 |
| `write/scripts/inventory_write_system.py` | 增加 `--include-meeting` 参数 |
| `组会/CLAUDE.md` | 增加"统一归属说明"+ 更新目录结构表 + 新增 prompts/scripts/reports/tests |
| `组会/prompts/README.md` | **新建** |
| `组会/scripts/README.md` | **新建** |
| `组会/templates/advisor_email_template.md` | 重命名为 `.from_write_20260604.md`（与已有24h版不同，保留差异） |

## 7. Write 中保留的非组会内容检查

| 类别 | 状态 |
|------|------|
| prompts (11 files) | ✅ 全部非组会（01-07, 10-12） |
| skills (4) | ✅ 全部非组会 |
| scripts (7) | ✅ 全部非组会 |
| checklists (4) | ✅ 全部非组会（组会版在组会） |
| templates (3) | ✅ 全部非组会（组会版在组会） |
| tests (3) | ✅ 全部非组会 |

## 8. 测试结果

| 命令 | 结果 | 备注 |
|------|------|------|
| `write_router.py --task group_meeting` | ✅ | 正确指向 组会/prompts/ |
| `write_router.py --task advisor_questions` | ✅ | 正确指向 组会/prompts/ |
| `inventory_write_system.py --include-meeting` | ✅ | 显示 write + 组会文件数 |
| `build_group_meeting_pack.py --help` | ✅ | 参数正常 |

## 9. 仍存在的问题

| 优先级 | 问题 | 影响 | 建议 |
|--------|------|------|------|
| P3 | build_group_meeting_pack.py 不支持 --dry-run | 无法预览输出 | 按需增加 |
| P3 | weekly_digest_builder.py 未实现 | 日报→周摘要手动 | 按需实现轻量版 |

## 10. 下一步建议
1. 用真实日报路径测试 `build_group_meeting_pack.py` 的完整流程
2. 按需实现 `weekly_digest_builder.py` 轻量桥接脚本
3. 9月正式组会前用实际流程（日报→周摘要→PPT大纲→讲稿）完整跑通一次
