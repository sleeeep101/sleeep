# QGIS 常见自动操作任务手册

> 每项任务含: Claude指令模板 → Codex执行步骤 → PyQGIS代码模板 → 常见错误 → 失败处理

---

## 1. 打开/创建 QGIS 项目

- **适用场景:** 任何 QGIS 操作的起点
- **Claude 指令:** "创建新 QGIS 项目，保存到 `<project_path>`"
- **Codex 执行:** 打开 QGIS → Ctrl+N 新建项目 → 设置 Project CRS → 保存
- **PyQGIS 模板:**
```python
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
project.write("/path/to/project.qgz")
```
- **常见错误:** CRS 未设置、项目路径无写入权限
- **失败处理:** Codex 手动通过 GUI 重新操作

## 2. 加载矢量图层

- **适用场景:** 加载 shp/gpkg/geojson 数据
- **Claude 指令:** "加载矢量文件 `<path>` 到 QGIS，确认图层名称和要素数量"
- **PyQGIS 模板:**
```python
from qgis.core import QgsVectorLayer
layer = QgsVectorLayer("/path/to/data.shp", "LayerName", "ogr")
if not layer.isValid():
    raise Exception(f"Layer failed to load: {layer.error().message()}")
QgsProject.instance().addMapLayer(layer)
print(f"Loaded: {layer.name()}, Features: {layer.featureCount()}")
```
- **输入要求:** 文件路径存在，格式为 shp/gpkg/geojson
- **常见错误:** 文件不存在、编码问题(中文字段名)、权限不足

## 3. 加载栅格图层

- **适用场景:** 加载 tif/img 等栅格数据
- **PyQGIS 模板:**
```python
from qgis.core import QgsRasterLayer
raster = QgsRasterLayer("/path/to/dem.tif", "DEM")
if not raster.isValid():
    raise Exception(f"Raster failed to load")
QgsProject.instance().addMapLayer(raster)
print(f"Loaded: {raster.name()}, Size: {raster.width()}x{raster.height()}")
```

## 4. 设置 CRS / EPSG

- **适用场景:** 确保图层和项目使用正确投影
- **Claude 指令:** "设置项目 CRS 为 EPSG:xxxx"
- **PyQGIS 模板:**
```python
from qgis.core import QgsCoordinateReferenceSystem, QgsProject
crs = QgsCoordinateReferenceSystem("EPSG:3857")
QgsProject.instance().setCrs(crs)
# 图层重投影
layer.setCrs(crs)
```

## 5. 图层样式应用

- **Claude 指令:** "对图层 `<layer>` 应用分类/渐变样式，字段为 `<field>`，配色为 `<scheme>`"
- **PyQGIS 模板:**
```python
from qgis.core import QgsGraduatedSymbolRenderer, QgsRendererRange, QgsSymbol
# 分级渲染
ranges = []
symbol = QgsSymbol.defaultSymbol(layer.geometryType())
ranges.append(QgsRendererRange(0, 100, symbol, "Low"))
ranges.append(QgsRendererRange(100, 200, symbol, "High"))
renderer = QgsGraduatedSymbolRenderer("field_name", ranges)
layer.setRenderer(renderer)
layer.triggerRepaint()
```

## 6. QML 样式加载

- **PyQGIS 模板:**
```python
layer.loadNamedStyle("/path/to/style.qml")
layer.triggerRepaint()
```

## 7. 矢量裁剪

- **PyQGIS 模板:**
```python
import processing
result = processing.run("native:clip", {
    "INPUT": "/path/to/input.shp",
    "OVERLAY": "/path/to/clip_boundary.shp",
    "OUTPUT": "/path/to/output.shp"
})
print(f"Clipped: {result['OUTPUT']}")
```

## 8. 缓冲区

- **PyQGIS 模板:**
```python
result = processing.run("native:buffer", {
    "INPUT": "/path/to/input.shp",
    "DISTANCE": 1000,
    "OUTPUT": "/path/to/buffer.shp"
})
```

## 9. 相交分析

- **PyQGIS 模板:**
```python
result = processing.run("native:intersection", {
    "INPUT": "/path/to/layer_a.shp",
    "OVERLAY": "/path/to/layer_b.shp",
    "OUTPUT": "/path/to/intersection.shp"
})
```

## 10. 栅格裁剪

- **PyQGIS 模板:**
```python
result = processing.run("gdal:cliprasterbymasklayer", {
    "INPUT": "/path/to/raster.tif",
    "MASK": "/path/to/boundary.shp",
    "OUTPUT": "/path/to/clipped.tif"
})
```

## 11. 栅格重投影

- **PyQGIS 模板:**
```python
result = processing.run("gdal:warpreproject", {
    "INPUT": "/path/to/input.tif",
    "SOURCE_CRS": "EPSG:4326",
    "TARGET_CRS": "EPSG:3857",
    "OUTPUT": "/path/to/reprojected.tif"
})
```

## 12. 栅格渲染 (DEM/坡度/山影)

- **PyQGIS 模板 (山影):**
```python
result = processing.run("native:hillshade", {
    "INPUT": "/path/to/dem.tif",
    "Z_FACTOR": 1.0,
    "AZIMUTH": 315,
    "V_ANGLE": 45,
    "OUTPUT": "/path/to/hillshade.tif"
})
# 坡度
result = processing.run("native:slope", {
    "INPUT": "/path/to/dem.tif",
    "OUTPUT": "/path/to/slope.tif"
})
```

## 13. 标注设置

- **PyQGIS 模板:**
```python
from qgis.core import QgsPalLayerSettings
settings = QgsPalLayerSettings()
settings.fieldName = "name_field"
settings.enabled = True
layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
layer.triggerRepaint()
```

## 14-17. 图例/比例尺/指北针/标题

> 这些通过 Print Layout 设置 (见 19)

## 19. Print Layout 自动创建

- **PyQGIS 模板:**
```python
from qgis.core import QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend, QgsLayoutItemScaleBar
from qgis.PyQt.QtCore import QRectF

project = QgsProject.instance()
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName("MapExport")

# 添加地图
map_item = QgsLayoutItemMap(layout)
map_item.setRect(QRectF(0, 0, 200, 150))
map_item.setExtent(project.mapLayers().values().__iter__().__next__().extent())
layout.addLayoutItem(map_item)

# 添加图例
legend = QgsLayoutItemLegend(layout)
layout.addLayoutItem(legend)
```

## 20-21. 导出 PNG / PDF

- **PyQGIS 模板:**
```python
from qgis.core import QgsLayoutExporter
exporter = QgsLayoutExporter(layout)
# PNG
exporter.exportToImage("/path/to/output.png", QgsLayoutExporter.ImageExportSettings())
# PDF
exporter.exportToPdf("/path/to/output.pdf", QgsLayoutExporter.PdfExportSettings())
```

## 22. 批量导出地图

- **Claude 指令:** "对 `<layer>` 按 `<field>` 分组，每组导出一张地图到 `<output_dir>`"
- **PyQGIS 模板:** 参见 `03_pyqgis_templates/batch_export_maps.py`

## 23. 项目保存

```python
project.write("/path/to/project.qgz")
```

## 24. 打包项目

```python
import shutil
shutil.make_archive("/path/to/package", "zip", "/path/to/project_dir")
```

## 13b. 属性筛选

- **PyQGIS 模板:**
```python
layer.setSubsetString('"field_name" = \'value\'')
# 或使用 attribute_filter_and_field_calc.py: filter_by_expression()
```
- **输入要求:** 矢量图层已加载
- **常见错误:** 字段名包含空格需用双引号;字符串值需用单引号

## 14b. 字段计算

- **PyQGIS 模板:**
```python
layer.startEditing()
layer.dataProvider().addAttributes([QgsField("new_field", QVariant.Double)])
layer.updateFields()
idx = layer.fields().indexOf("new_field")
for f in layer.getFeatures():
    layer.changeAttributeValue(f.id(), idx, f.geometry().area() / 1e6)
layer.commitChanges()
```
- **模板:** attribute_filter_and_field_calc.py: add_field()
- **常见错误:** 未调用 startEditing/commitChanges;字段类型不匹配

## 23b. 指北针添加

- **PyQGIS 模板:**
```python
# add_north_arrow_and_log.py: add_north_arrow()
# 优先使用QGIS内置SVG，回退到文本"N ▲"
```
- **输入要求:** Print Layout 已创建
- **常见错误:** QGIS内置SVG路径不可用(回退到文本)

## 32b. 执行日志记录

- **PyQGIS 模板:**
```python
from add_north_arrow_and_log import ExecutionLogger
logger = ExecutionLogger("output/qgis_log.json")
logger.log_step(1, "load_vector", "success", "Loaded study_area.shp", input_path="...", output_path="...")
logger.save()
```
- **输出:** JSON格式日志，含时间戳/步骤/状态/输入/输出/错误
- **不覆盖旧日志:** 自动添加时间戳后缀

## 25. 常见报错恢复

| 错误 | 原因 | 解决 |
|------|------|------|
| `Layer is not valid` | 文件路径不存在或格式不支持 | 检查路径、用 `ogr` provider |
| `ImportError: No module named qgis.core` | 不在 QGIS Python 环境 | 用 QGIS 自带 Python 或设置 PYTHONPATH |
| `processing module not found` | 未初始化 QGIS | `from qgis.core import QgsApplication; QgsApplication([], False).initQgis()` |
| CRS 不匹配 | 图层之间投影不同 | 先统一重投影 |
| 中文乱码 | Shapefile 编码 | 加载时指定 encoding="UTF-8" |

> 详细错误恢复: qgis_error_recovery.md
