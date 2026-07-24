# 本地 QGIS Skills 审计

> 扫描范围: academic-workflow (排除 99_归档备份)
> 扫描日期: 2026-06-06

## 扫描结果

| 路径 | 类型 | 内容摘要 | 与QGIS相关 | 可复用程度 | 建议整合位置 |
|------|------|---------|-----------|-----------|------------|
| `00_项目总览与导航/references/11_external_skill_patterns.md` | 规则文件 | QGIS Agent (LLM→QGIS)、geospatial-data-studio (NL→QGIS数据加载)、LandTalk.AI (QGIS截图分析)、TerraStackAI (微调→QGIS管道) | ✅ 高 | 高 — 已评分 | 思路整合到 02_operation_manuals |
| `00_项目总览与导航/references/12_gis_remote_sensing_workflow.md` | 规则文件 | GIS/遥感工作流框架，含 QGIS Processing、GDAL、WhiteboxTools 工具链 | ✅ 中 | 中 — 工具选择指南 | 工具链引用到操作手册 |
| `00_项目总览与导航/references/16_done_definition.md` | 规则文件 | ArcGIS/QGIS/GEE 学习完成标准 | ⚠️ 低 | 低 — 学习标准 | 不整合 |
| `03_写/skills/gis-rs-writing-assistant/SKILL.md` | Skill | GIS/遥感写作辅助，提及 ArcGIS/QGIS 工具链 | ⚠️ 低 | 低 — 写作Skill | 不整合 |
| `04_组会PPT/02_PPT文件/2026-06-W23_ppt_outline_simulation.md` | PPT大纲 | 提及 QGIS 实操任务 (DEM+土地利用+加权叠加) | ⚠️ 低 | 低 — 组会材料 | 不整合 |
| `01_读/01_每日论文/12本书适配报告_2026-06-03.md` | 报告 | QGIS 学习路径 (Python+QGIS 批处理) | ⚠️ 低 | 低 — 读书笔记 | 不整合 |

## 关键发现

1. **`11_external_skill_patterns.md` 已有 QGIS AI Agent 调研** — 包含 4 个高价值项目 (QGIS Agent, geospatial-data-studio, LandTalk.AI, TerraStackAI)，评分和风险评估已完成
2. **`12_gis_remote_sensing_workflow.md` 有完整工具链** — QGIS Processing + GDAL + WhiteboxTools 的流程模板
3. **没有本地 QGIS skill 定义文件** — 需要从头构建操作模块
4. **所有提到 QGIS 的地方都是"提及"**，没有可直接复用的 PyQGIS 脚本或操作模板

## 结论

本地无现成 QGIS skill 可复用。需要从 GitHub 调研 + PyQGIS 官方文档构建全新模块。
