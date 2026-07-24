# 组会板块整体测试报告

> 测试日期: 2026-06-04 | 测试方式: 只读 + 帮助命令

## 1. 测试结论
**部分可用** — 模板和规则体系完整，核心脚本可运行，但自动化连接较弱，PPT→讲稿链路需实际 PPTX 文件触发。

## 2. 测试命令

| 命令 | 结果 | 备注 |
|------|------|------|
| `build_group_meeting_pack.py --help` | ✅ | 4个参数正常 |
| 组会目录存在性 | ✅ | 42个文件 |
| rules/ 完整性 | ✅ | 4个规则文件 |
| templates/ 完整性 | ✅ | 7个模板文件 |
| checklists/ 完整性 | ✅ | 5个检查清单 |
| bridge/ 完整性 | ✅ | 5个桥接文件 |
| scripts/ 存在性 | ✅ | build_group_meeting_pack.py |
| speaker/ 完整性 | ✅ | ppt-speech-writer Skill (12 files) |
| outputs/ 存在性 | ✅ | 2个模拟输出 |
| prompts/ 完整性 | ✅ | 08, 09 两个组会prompt |
| skills/group-meeting-writing | ✅ | SKILL.md |

## 3. 功能链路

| 环节 | 是否可用 | 证据 | 问题 |
|------|---------|------|------|
| 日报→论文筛选 | 手动可用 | weekly_digest 模板完整 | 无自动提取脚本 |
| 论文→周摘要 | 手动可用 | bridge/weekly_group_meeting_digest_template.md | 需手动填写 |
| 周摘要→PPT大纲 | 手动可用 | bridge/paper_reading_to_ppt_outline.md | 含15页结构+映射表 |
| PPT大纲→PPT讲稿 | 条件可用 | ppt-speech-writer Skill | 需实际PPTX文件 |
| 导师追问生成 | 手动可用 | prompts/09_advisor_question_generator.md | Prompt已就绪 |
| 会前邮件 | 手动可用 | templates/advisor_email_24h_before.md | 模板可用 |
| 会后复盘 | 手动可用 | checklists/after_meeting_review.md | 检查清单完整 |
| 组会材料准备包 | 脚本可用 | scripts/build_group_meeting_pack.py | 需日报目录输入 |
| 沉淀→长期知识库 | **不可用** | 无自动化 | 需手动追加 |

## 4. 发现的问题

| 优先级 | 问题 | 影响 | 修复建议 |
|--------|------|------|---------|
| P1 | 日报→周摘要无自动提取 | 每周手动翻日报耗时 | 用 weekly_digest_builder 思路做轻量桥接 |
| P1 | PPT大纲→实际PPTX无自动生成 | 组会准备链路在PPTX处中断 | 暂不做（ppt-speech-writer已覆盖讲稿） |
| P2 | 沉淀到长期知识库无自动化 | 组会成果散落 | 手动追加，暂不做自动化 |
| P3 | 输出目录中模拟材料偏少 | 仅有W23两次模拟 | 不影响功能，9月前可补 |

## 5. 不建议现在做的扩建
1. 不要写从0生成PPTX的脚本（依赖重，ppt-speech-writer已足够）
2. 不要构建组会自动化调度系统（9月前手动运行即可）
3. 不要修改组会原模板的7字段结构（已有模拟材料质量高）
4. 不要在组会嵌入 academic-workflow 逻辑（松耦合是优点）
5. 不要引入 Quarto/Marp/LaTeX 替代 PPTX（导师和同学用 PowerPoint）
