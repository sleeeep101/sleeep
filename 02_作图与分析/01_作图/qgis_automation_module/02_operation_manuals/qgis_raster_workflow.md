# QGIS 栅格处理工作流

## 完整工作流

```
加载栅格 → 检查CRS/分辨率 → 重投影 → 裁剪 → 分析(山影/坡度) → 渲染 → 导出
```

## DEM处理链

```python
# 1. 重投影
processing.run("gdal:warpreproject", {"INPUT": dem, "TARGET_CRS": "EPSG:3857", "OUTPUT": "..."})
# 2. 裁剪
processing.run("gdal:cliprasterbymasklayer", {"INPUT": dem_3857, "MASK": boundary, "OUTPUT": "..."})
# 3. 山影
processing.run("native:hillshade", {"INPUT": dem_clipped, "AZIMUTH": 315, "V_ANGLE": 45, "OUTPUT": "..."})
# 4. 坡度
processing.run("native:slope", {"INPUT": dem_clipped, "OUTPUT": "..."})
```

## 栅格渲染

- **单波段灰度**: 适合DEM/山影
- **单波段伪彩色**: 适合坡度/NDVI/分类图
- **多波段RGB**: 适合遥感影像

```python
# 伪彩色渲染
renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
layer.setRenderer(renderer)
```

## 模板
- `raster_clip_reproject.py` — 裁剪/重投影/山影/坡度
