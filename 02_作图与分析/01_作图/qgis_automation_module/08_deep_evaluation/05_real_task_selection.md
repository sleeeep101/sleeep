# 05 真实测试任务选择

## 数据扫描结果

**扫描结论: 本地 academic-workflow 中无真实 GIS 数据文件。**

| 文件类型 | 搜索结果 |
|---------|---------|
| .shp | 0 个 |
| .gpkg | 0 个 |
| .geojson | 0 个 |
| .tif / .tiff | 0 个 |
| .asc | 0 个 |
| .qml | 0 个 |
| .qgz / .qgs | 0 个 |
| .csv (含经纬度) | 0 个 — 只有 metadata csv 和 config csv |

仅有的 CSV 文件:
- `paper_source_index.csv` — 论文元数据索引
- `github_top300_qgis_repos.csv` — GitHub 仓库列表
- `demo_line.csv` (217 bytes) — Origin 作图 demo，非 GIS
- `project_integration_matrix.csv` — 项目集成配置

## 决策

**真实测试数据缺失。** 按照测评规则第四优先：不伪造数据、不联网下载、不创建假数据。

## 替代方案

生成 Codex 额度恢复后可执行的测试任务模板。

## 建议测试任务（数据就绪后）

**任务名称:** "论文研究区 DEM 地形 + 行政区边界自动制图与导出"

**需要的数据（后续获取）:**
- DEM: SRTM/ASTER 30m GeoTIFF（公开免费下载）
- 行政区边界: 中国省级/市级 shapefile（公开免费）
- 河流线: OSM 提取或公开数据

**预期处理流程:**
1. 加载 DEM → 生成山影 → 加载矢量边界 → 裁剪 DEM → 创建布局 → 导出 PNG/PDF
2. 覆盖的操作: #1,4,5,6,15,18,19,20,21,22,24,25,26,27,29

**当前状态:** 等待 GIS 数据就绪 + Codex 额度可用
