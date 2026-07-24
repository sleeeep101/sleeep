# GitHub 精华 → 本地模块落地映射

| GitHub 来源 | 提炼内容 | 落地文件 | 落地形式 | 状态 |
|------------|---------|---------|---------|:--:|
| qgis/QGIS (13.8k) | PyQGIS API | 全部10个.py模板 | PyQGIS 脚本 | ✅ |
| qgis/QGIS-Documentation | API文档 | 所有模板注释 | API参考 | ✅ |
| qgis/QGIS-Processing | 官方Processing示例 | raster/vector模板 | Processing调用 | ✅ |
| jjsantos01/qgis_mcp (971) | LLM→QGIS MCP | computer_use_qgis_steps.md | 操作步骤 | ✅ |
| nkarasiak/qgis-mcp (125) | Claude MCP连接 | computer_use_qgis_steps.md | 操作步骤 | ✅ |
| giswqs/qgis-earthengine-examples (984) | 300+ PyQGIS代码 | qgis_common_tasks.md | 代码模式 | ✅ |
| anitagraser/QGIS-resources (300) | Processing脚本 | qgis_common_tasks.md | 代码模式 | ✅ |
| anitagraser/QGIS-Processing-tools (90) | Processing工具 | qgis_common_tasks.md | 代码模式 | ✅ |
| tjukanovt/qgis_styles (189) | 制图样式 | cartography_style_guide.md + apply_style_qml.py | 样式+QML | ✅ |
| webgeodatavore/pyqgis-samples (131) | PyQGIS示例 | load_*.py模板 | 脚本模板 | ✅ |
| opengeos/GeoAgent (366) | AI Agent | claude_instruction_template.md | 协议参考 | ✅ |
| Impertio-Studio/QGIS-Claude-Skill-Package (21) | Claude QGIS Skills | 整个模块设计 | 架构参考 | ✅ |
| zoran-cuckovic/QGIS-terrain-shading (83) | DEM渲染 | raster_clip_reproject.py | hillshade增强 | ✅ |
| MahdiFarnaghi/intelli_geo (61) | LLM+QGIS | Claude指令模板 | LLM交互 | ✅ |
| ght-mtt/DataPlotly (207) | Plotly图表 | cartography_style_guide.md | 记录 | ⚠️ 未落地脚本 |
| All4Gis/QGIS-cheat-sheet (86) | PyQGIS速查 | qgis_common_tasks.md | API引用 | ✅ |
| qgis/QGIS-Code-Examples (109) | 官方示例 | 操作手册 | 参考 | ✅ |
| luolingchun/PyQGIS-Developer-Cookbook-cn (66) | 中文PyQGIS | 操作手册 | 中文文档 | ✅ |
| charleyglynn/OSM-Shapefile-QGIS-stylesheets (164) | OSM样式 | cartography_style_guide.md | QML | ✅ |
| yannos/Beautiful_OSM_in_QGIS (79) | OSM美化 | cartography_style_guide.md | 样式 | ✅ |
| PUTvision/qgis-plugin-deepness (186) | DL遥感 | useful_github_repos | 记录 | ✅ 不适合整合 |
| coolzhao/Geo-SAM (408) | SAM分割 | useful_github_repos | 记录 | ✅ 需GPU |
| wonder-sk/qgis-minimal-plugin (116) | 插件骨架 | 插件开发参考 | 记录 | ✅ |
| jonah-sullivan/Qgis-Plugin-Builder (93) | 插件脚手架 | 插件开发参考 | 记录 | ✅ |
| gis-ops/tutorials (184) | GIS教程 | 操作手册参考 | 间接 | ✅ |
| volaya/qgis-python-course (128) | QGIS Python | 操作手册参考 | 间接 | ✅ |
| TangSY/echarts-map-demo (2116) | GeoJSON | — | 不整合 | ❌ 非QGIS核心 |
| maptiler/tileserver-php (592) | 瓦片服务 | — | 不整合 | ❌ PHP;非桌面 |
| MerginMaps/mobile (377) | 移动端 | — | 不整合 | ❌ 移动端 |
| 3liz/lizmap-web-client (328) | WebGIS | — | 不整合 | ❌ Web |
