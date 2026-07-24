# QGIS 矢量处理工作流

## 完整工作流

```
加载矢量 → 检查CRS → 属性筛选 → 空间处理 → 样式 → 标注 → 导出
```

## 常用空间处理链

### 1. 裁剪+缓冲区+相交
```python
# 裁剪到研究区
clip = processing.run("native:clip", {"INPUT": roads, "OVERLAY": boundary, "OUTPUT": "..."})
# 创建缓冲区
buf = processing.run("native:buffer", {"INPUT": clip["OUTPUT"], "DISTANCE": 500, "OUTPUT": "..."})
# 与土地利用相交
inter = processing.run("native:intersection", {"INPUT": buf["OUTPUT"], "OVERLAY": landuse, "OUTPUT": "..."})
```

### 2. 属性筛选+导出
```python
layer.setSubsetString('"category" = \'forest\'')
# 或 attribute_filter_and_field_calc.py
```

### 3. 字段计算
```python
# 新建面积字段
layer.startEditing()
layer.dataProvider().addAttributes([QgsField("area_km2", QVariant.Double)])
layer.updateFields()
for f in layer.getFeatures():
    layer.changeAttributeValue(f.id(), idx, f.geometry().area() / 1e6)
layer.commitChanges()
```

## 模板
- `vector_clip_buffer_intersect.py` — 裁剪/缓冲/相交
- `attribute_filter_and_field_calc.py` — 属性筛选+字段计算
