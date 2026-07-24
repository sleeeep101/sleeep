# Codex 待执行任务包 — QGIS 真实作图测试

## 暂停原因
- Codex 不可用 (Claude 无法调用 Codex computer use)
- 无真实 GIS 数据 (shp/gpkg/geojson/tif 均不存在)
- 策略: 暂停作图，等条件满足后执行

## 需要的真实 GIS 数据（后续获取）

1. **DEM GeoTIFF** — SRTM/ASTER 30m，可从 USGS EarthExplorer 免费下载
2. **行政区边界 Shapefile** — 可从 GADM (gadm.org) 免费下载中国省/市级边界
3. **可选: 河流线** — 可从 OpenStreetMap 通过 QuickOSM 获取

## 测试任务

加载 DEM + 矢量边界 → 生成山影 → 裁剪到研究区 → 创建布局 → 导出 PNG/PDF/QGZ

## 验收标准
- 原始文件 SHA256 不变
- 输出 hillshade.tif + slope.tif + map.png + map.pdf + project.qgz
- 前后对比文件有明确处理关系
