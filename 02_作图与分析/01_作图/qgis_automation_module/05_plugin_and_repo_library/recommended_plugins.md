# 推荐 QGIS 插件

> 基于 GitHub 调研 + 官方生态评估。只推荐已验证有价值的插件，不要求立即安装。

| 插件 | 用途 | 适合任务 | 是否必须 | 安装风险 | 可用PyQGIS替代 | 推荐级别 |
|------|------|---------|---------|---------|---------------|---------|
| QuickOSM | 从 OSM 下载数据 | 获取 OpenStreetMap 矢量数据 | 否 | 低 (官方插件库) | 部分 (Overpass API) | ★★★ |
| DataPlotly | D3 风格图表 | 统计图嵌入 QGIS | 否 | 低 | 是 (matplotlib) | ★★ |
| qgis2web | 项目导出为 Web 地图 | Web 展示 | 否 | 低 | 部分 | ★★ |
| QuickMapServices | 一键添加底图 | 快速添加 Google/OSM 底图 | 推荐 | 低 | 是 (XYZ Tiles) | ★★★ |
| Geo-SAM | Segment Anything 分割 | AI 辅助地物提取 | 否 | 中 (需GPU) | 是 (SAM Python) | ★★ |
| Deepness | 深度学习遥感推理 | 地物分类/目标检测 | 否 | 中 (需模型) | 是 | ★★ |
| latlontools | 坐标捕获和转换 | 坐标格式转换 | 否 | 低 | 是 | ★★ |
| TimeManager | 时序数据动画 | 时空数据可视化 | 否 | 低 | 是 | ★★ |
| Qgis2threejs | 3D 地图可视化 | 地形3D展示 | 否 | 低 | 部分 | ★★ |

## 安装方式

- **官方插件库:** Plugins → Manage and Install Plugins → 搜索 → Install
- **ZIP 安装:** Plugins → Manage and Install → Install from ZIP
- **手动安装:** 复制插件文件夹到 `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
