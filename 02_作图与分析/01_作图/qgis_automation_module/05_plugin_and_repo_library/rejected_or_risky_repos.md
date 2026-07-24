# 不建议使用或高风险仓库

| 仓库 | 原因 | 风险等级 |
|------|------|---------|
| TangSY/echarts-map-demo | 主要是 ECharts 前端地图，非 QGIS | 无关 |
| maptiler/tileserver-php | PHP 瓦片服务器，非 QGIS 自动化 | 无关 |
| kartoza/docker-osm | Docker OSM 数据库，非直接 QGIS | 间接相关 |
| sldeditor/sldeditor | Java 桌面应用，非 QGIS 插件 | 无关 |
| lovebetterworld/gis-spicy-hot-pot | GIS 笔记合集，非可执行工具 | 文档集 |
| MerginMaps/mobile | 移动端应用，非桌面自动化 | 无关 |
| roam-qgis/Roam | 野外数据采集，非制图 | 无关 |
| inasafe/inasafe | 自然灾害(已停止活跃开发) | 过时 |
| qgis/OLD-QGIS-Website | 旧网站代码 | 无关 |
| GIS4WRF/gis4wrf | WRF 天气模型专用，与科研主线无关 | 无关 |
| SpaceGroupUCL/qgisSpaceSyntaxToolkit | 空间句法，特定领域 | 可参考 |
| jagodki/Offline-MapMatching | HMM 轨迹匹配，特定领域 | 可参考 |

## 谨慎安装的插件

| 插件 | 风险 |
|------|------|
| 任何非官方仓库的插件 | 未审计代码 |
| 需要管理员权限的插件 | 可能修改系统配置 |
| 依赖特定 QGIS 版本的插件 | 版本升级后可能不可用 |
| 最后更新 >2 年的插件 | 可能不兼容新版本 QGIS |
