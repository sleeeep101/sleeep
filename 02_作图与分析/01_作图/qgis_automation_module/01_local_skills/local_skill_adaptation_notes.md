# GitHub 调研 → 本地技能适配说明

## 适配原则

1. GitHub 仓库代码为"通用参考"→ 本地化为"可执行模板"
2. PyQGIS 示例 → 提取核心调用模式 → 写成本地 .py 模板
3. 插件功能 → 评估可否用 PyQGIS 替代 → 替代则写模板;不替代则记录插件
4. 制图样式 → 提取配色/QML → 写入 cartography_style_guide
5. LLM/Agent项目 → 提取交互协议 → 写入 Claude-Codex 协议

## 主要适配案例

### qgis/QGIS → 10个本地模板
- GitHub: C++ QGIS核心 + Python绑定
- 本地化: 提取 PyQGIS API 调用模式 → 10个独立 .py 脚本
- 关键选择: 用 `processing.run()` 而非 QGIS C++ API

### qgis_mcp → computer_use_qgis_steps.md
- GitHub: MCP 服务器暴露 QGIS 功能给 LLM
- 本地化: 提取 MCP 工具定义逻辑 → 写成 Codex 可执行的 GUI 操作步骤
- 关键选择: 不用 MCP 协议（需要额外基础设施），改用 Computer Use

### qgis-earthengine-examples → qgis_common_tasks.md
- GitHub: 300+ GEE+QGIS Python 脚本
- 本地化: 提取纯 QGIS 部分（加载/处理/布局/导出）→ 25+ 操作项
- 关键选择: 去掉 GEE 依赖，只保留本地 QGIS 部分

### tjukanovt/qgis_styles → cartography_style_guide.md
- GitHub: QML 样式文件集合
- 本地化: 提取配色方案 → 写入制图指南;QML 加载模板
- 关键选择: 不复制 QML 文件（版本依赖），而是写通用配色规则

### Impertio-Studio/QGIS-Claude-Skill-Package → 模块设计
- GitHub: 19个 Claude Code QGIS Skills
- 本地化: 作为整个 qgis_automation_module 的设计参考
- 关键选择: 不直接安装该Skill包，而是参考其Skill分解方式

## 不整合的类型

| 仓库类型 | 代表 | 不整合理由 |
|---------|------|-----------|
| WebGIS | qwc2, lizmap | 当前目标是桌面QGIS自动作图 |
| 移动端 | QField, MerginMaps | 野外采集;非桌面 |
| R语言 | qgisprocess, RQGIS | 当前PyQGIS为主 |
| C++ | QGIS-Code-Examples | 当前Python模板为主 |
| 特定领域 | WRF, SWAT, 空间句法 | 与GIS/遥感主方向无关 |
| 商业数据 | Maxar, Sentinel-Hub | 需要商业授权 |
| 过时/归档 | RQGIS, inasafe | 不再活跃维护 |
