---
name: academic-workflow
version: 3.0.0
description: 个人学术工作流总控。桌面PDF批量精读→知识卡片→长期知识库。使用已安装的13个本地Skill + Claude Sub-Agent并行。触发场景：论文阅读、桌面PDF处理、每日论文雷达、知识库、方法迁移、GIS/遥感科研、PPT汇报。
license: 个人自用
---

# Academic Workflow

> **主入口**: `<LOCAL_PATH>`
> 本文件是 `00_项目总览与导航\` 下的简短索引，完整规则见主 SKILL.md。

## 当前模式（v3.0, 2026-07-13）

- 用户下载论文至桌面 → `/pdf-image-text-extractor` 提取 → Claude + Sub-Agent 并行精读 → 日报 → 长期知识库
- 12:00 定时在线检索已搁置
- 质量基线：2026-07-13 日报标准（全量覆盖/≥15行卡片/≥60分入库/禁用表达清零）

## 使用的 Skill

| Skill | 用途 |
|-------|------|
| `pdf-image-text-extractor` | PDF文本提取 |
| `group-meeting-ppt` | 组会PPT |
| `academic-paper-writing` | 学术写作 |
| `scientific-figure` | 科学图表 |
| `dev-discipline` | 代码纪律 |
| `deep-research` | 深度研究（系统内置） |

## 核心脚本

见主 SKILL.md「桌面 PDF 论文处理工具链」章节。
