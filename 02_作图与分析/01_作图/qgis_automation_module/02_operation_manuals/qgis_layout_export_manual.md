# QGIS Print Layout 与导出操作手册

## 创建布局

**Codex步骤:**
1. Project → New Print Layout → 命名为 "ExportMap"
2. 右键页面 → Page Properties → 设置尺寸 (A4: 210×297mm)

**PyQGIS:**
```python
layout = QgsPrintLayout(QgsProject.instance())
layout.initializeDefaults()
layout.setName("ExportMap")
```

## 添加地图

**PyQGIS:**
```python
from qgis.PyQt.QtCore import QRectF
map_item = QgsLayoutItemMap(layout)
map_item.setRect(QRectF(10, 10, 190, 180))  # x,y,w,h (mm)
map_item.setExtent(layer.extent())
layout.addLayoutItem(map_item)
```

## 添加图例

**PyQGIS:**
```python
legend = QgsLayoutItemLegend(layout)
legend.setRect(QRectF(10, 195, 60, 60))
layout.addLayoutItem(legend)
```

## 添加比例尺

**PyQGIS:**
```python
scalebar = QgsLayoutItemScaleBar(layout)
scalebar.setRect(QRectF(120, 195, 70, 10))
layout.addLayoutItem(scalebar)
```

## 添加标题

**PyQGIS:**
```python
title = QgsLayoutItemLabel(layout)
title.setText("Map Title")
title.setRect(QRectF(10, 5, 190, 15))
layout.addLayoutItem(title)
```

## 导出PNG (300dpi)
```python
exporter = QgsLayoutExporter(layout)
settings = QgsLayoutExporter.ImageExportSettings()
settings.dpi = 300
exporter.exportToImage("/output/map.png", settings)
```

## 导出PDF
```python
settings = QgsLayoutExporter.PdfExportSettings()
exporter.exportToPdf("/output/map.pdf", settings)
```

> 通用模板: create_layout_export_png_pdf.py
