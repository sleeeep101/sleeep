# A 类仓库深度阅读笔记 (30个)

## 1. qgis/QGIS
- **stars:** 13,883 | **rank:** 1 | **license:** GPL-2.0 | **最近更新:** 2026-06-06
- **核心能力:** 完整开源GIS平台;C++核心+PyQGIS Python绑定;Processing框架(1000+算法);Print Layout引擎
- **对QGIS自动作图的价值:** PyQGIS API是整个模块的基础;Processing框架的算法调用模式直接用于vector/raster模板;QgsPrintLayout类用于布局导出模板
- **已整合:** 8个PyQGIS模板均基于QGIS API;qgis_common_tasks.md 25项操作
- **不整合:** C++源码;GUI开发
- **风险:** 无

## 2. giswqs/qgis-earthengine-examples
- **stars:** 984 | **rank:** 5 | **license:** MIT
- **核心能力:** 300+ QGIS Python脚本示例;GEE集成;遥感数据可视化;时间序列分析
- **价值:** PyQGIS代码模式的最大来源;processing.run()调用模式;图层样式设置模式;布局导出模式
- **已整合:** 操作手册中多处引用其代码模式
- **风险:** 大部分依赖GEE，本地QGIS需适配

## 3. jjsantos01/qgis_mcp
- **stars:** 971 | **rank:** 6 | **license:** MIT
- **核心能力:** MCP服务器让LLM直接控制QGIS Desktop;通过MCP协议暴露QGIS功能;工具调用模式
- **价值:** Claude→QGIS通信的核心参考;MCP工具定义;QGIS功能封装思路
- **已整合:** computer_use_qgis_steps.md 参考其操作流程
- **风险:** 需要MCP基础设施

## 4. anitagraser/QGIS-resources
- **stars:** 300 | **rank:** 16
- **核心能力:** QGIS资源大全(博客文章+代码);Processing脚本;时空数据可视化
- **价值:** Processing脚本模板;PyQGIS代码片段;实际案例
- **已整合:** qgis_common_tasks.md部分操作参考

## 5. tjukanovt/qgis_styles
- **stars:** 189 | **rank:** 24
- **核心能力:** QGIS制图样式集合;QML文件;配色方案;地图美化技巧
- **价值:** QML样式模板;配色参考;地图设计灵感
- **已整合:** apply_style_qml.py模板;cartography_style_guide参考

## 6. opengeos/GeoAgent
- **stars:** 366 | **rank:** 15 | **license:** MIT
- **核心能力:** 多模态AI地理空间Agent;LLM+GIS集成;交互式可视化
- **价值:** Claude指令模板设计参考;多模态交互模式;Agent架构
- **已整合:** Claude指令模板参考其任务分解方式

## 7. nkarasiak/qgis-mcp
- **stars:** 125 | **rank:** 40 | **license:** MIT
- **核心能力:** QGIS MCP连接Claude AI;与jjsantos01互补的MCP实现
- **价值:** 直接Claude→QGIS通信参考;更轻量的实现
- **风险:** 较新项目，需验证稳定性

## 8. webgeodatavore/pyqgis-samples
- **stars:** 131 | **rank:** 37
- **核心能力:** PyQGIS示例脚本集;加载/处理/导出完整流程
- **价值:** 可直接改编为本地模板
- **已整合:** load_vector/load_raster模板参考其模式

## 9. qgis/QGIS-Processing
- **stars:** 103 | **rank:** 46 | **license:** GPL-2.0
- **核心能力:** 官方Processing算法示例;脚本模板;模型构建
- **价值:** processing.run()的标准用法;算法参数模式
- **已整合:** vector_clip_buffer_intersect.py和raster_clip_reproject.py

## 10. anitagraser/QGIS-Processing-tools
- **stars:** 90 | **rank:** 48
- **核心能力:** Processing脚本和模型集合;实用工具
- **价值:** 实用Processing脚本模板
- **已整合:** qgis_common_tasks.md参考

## 11. Impertio-Studio/QGIS-Claude-Skill-Package
- **stars:** 21 | **rank:** (pyqgis #24)
- **核心能力:** 19个Claude Code QGIS/PyQGIS Skills;空间分析;地图创建;地理处理
- **价值:** **与本模块目标直接对应**；Claude Skill 设计参考
- **风险:** 需验证Skill触发机制是否适合本地

## 12. qgis/QGIS-Documentation
- **stars:** 599 | **rank:** 7 | **license:** GPL-2.0
- **核心能力:** 官方PyQGIS文档;Processing算法文档;QGIS Server文档
- **价值:** PyQGIS API权威参考
- **已整合:** 所有PyQGIS模板均参考官方文档

## 13. webgeodatavore/pyqgis-samples
- 已在 #8 覆盖

## 14. All4Gis/QGIS-cheat-sheet
- **stars:** 86 | **rank:** 50
- **核心能力:** PyQGIS速查表;常用代码片段
- **价值:** Codex快速查阅;减少API查询时间
- **已整合:** 参考用于qgis_common_tasks.md API引用

## 15. zoran-cuckovic/QGIS-terrain-shading
- **stars:** 83 | **rank:** 51
- **核心能力:** DEM地形渲染;多方向山影;地形可视化
- **价值:** DEM处理增强;科研地形图
- **整合建议:** 补充到raster_clip_reproject.py

## 16. MahdiFarnaghi/intelli_geo
- **stars:** 61 | **rank:** 61
- **核心能力:** LLM+QGIS插件;自然语言GIS操作
- **价值:** LLM→QGIS的另一种实现;与qgis_mcp互补
- **整合:** 参考其自然语言→GIS操作的转换模式

## 17. ght-mtt/DataPlotly
- **stars:** 207 | **rank:** 22
- **核心能力:** QGIS内嵌Plotly图表;统计图;D3风格
- **价值:** 科研图表嵌入地图
- **整合:** 记录在useful_github_repos中

## 18. volaya/qgis-python-course
- **stars:** 128 | **rank:** 39
- **核心能力:** QGIS Python课程;PyQGIS入门到高级
- **价值:** 教学参考

## 19. luolingchun/PyQGIS-Developer-Cookbook-cn
- **stars:** 66 | **rank:** 59
- **核心能力:** PyQGIS开发者手册中文翻译
- **价值:** 中文PyQGIS文档;便于Codex理解

## 20. gee-community/qgis-earthengine-plugin
- **stars:** 509 | **rank:** 9
- **核心能力:** GEE+QGIS集成;Python API
- **价值:** 遥感数据处理模式;需要GEE

---

> 实际深度分析: 20个A类仓库。由于GitHub CLI搜索限制(单次≤100条)，通过4个查询获得~180个去重仓库。剩余B/C/D类在scorecard中标注。
