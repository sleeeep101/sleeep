# Write System Overview

## 架构

```
数据入口层
├── daily_paper_curator.py 输出（reports/daily/）
├── 长期知识库.md
├── 论文卡片（手动或自动生成）
└── 用户草稿（.md/.txt）

Prompt 层（write/prompts/）
├── 00_master_write_router.md      任务路由
├── 01_chinese_grammar_check.md    中文语病检查
├── 02_academic_polish_chinese.md  学术润色
├── 03_logic_and_argument_check.md 逻辑论证检查
├── 04_reduce_template_style.md    减少模板化表达
├── 05_literature_review_builder.md 文献综述构建
├── 06_abstract_intro_method_result_discussion.md 论文章节写作
├── 07_gis_remote_sensing_academic_style.md GIS/遥感表达
├── 08_group_meeting_outline.md    组会提纲
├── 09_advisor_question_generator.md 导师追问
├── 10_reference_and_citation_check.md 参考文献检查
├── 11_markdown_to_docx_pdf_check.md 输出格式检查
└── 12_writing_learning_card.md    写作学习卡片

Skill 层（write/skills/）
├── chinese-academic-writing/     中文论文学术写作 Skill
├── literature-review-assistant/  文献综述辅助 Skill
├── group-meeting-writing/        组会写作 Skill
├── gis-rs-writing-assistant/     GIS/遥感写作 Skill
└── writing-quality-auditor/      写作质量审计 Skill

Script 层（write/scripts/）
├── check_chinese_grammar.py      中文语病检查脚本
├── write_router.py               任务路由脚本
├── build_literature_review_pack.py 文献综述准备包
├── build_group_meeting_pack.py   组会材料准备包
├── extract_writing_cards.py      写作学习卡片提取
├── check_reference_placeholders.py 引用占位符检查
└── inventory_write_system.py     Write 系统盘点

输出层（write/outputs/）
├── grammar_reports/              语病检查报告
├── polish_reports/               润色报告
├── literature_review_packs/      文献综述准备包
├── group_meeting_packs/          组会材料准备包
└── writing_cards/                写作学习卡片
```

## 与组会系统的关系

write 系统是 academic-workflow 的新增能力模块，**不修改和替代**组会目录：
- 组会系统保持独立（模板/规则/Skill/检查清单）
- write 系统提供轻量自动化桥接脚本
- build_group_meeting_pack.py 消费日报产出组会材料，不反向控制

## 为什么不修改 daily_paper_curator.py

daily_paper_curator.py 是独立的论文阅读调度系统，有自己的定时任务和数据库。
write 系统只消费其输出（日报MD文件），不在其内部嵌入写作逻辑。
保持模块独立性的同时，通过"输入→处理→输出"的松耦合方式协作。

## 数据流向

```
daily_paper_curator.py → reports/daily/*.md
                              ↓
              build_literature_review_pack.py
              build_group_meeting_pack.py
              extract_writing_cards.py
                              ↓
              outputs/literature_review_packs/
              outputs/group_meeting_packs/
              outputs/writing_cards/
                              ↓
              用户审阅 → 长期知识库.md（手动追加）
```
