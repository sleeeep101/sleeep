# QGIS 制图样式指南

## 配色方案

| 主题 | 配色 | QGIS实现 |
|------|------|---------|
| DEM地形 | 黄绿→棕→白 | SingleBandPseudoColor, Viridis/Terrain |
| 坡度 | 绿→黄→红 | Graduated, 5-10类 |
| 土地利用 | 分类色 | Categorized, 每类一色 |
| 行政区划 | 淡色填充+黑边 | Simple Fill: transparent 50% + black outline |
| 热力图 | 蓝→青→黄→红 | Heatmap renderer |

## QML样式加载

```python
layer.loadNamedStyle("/path/to/style.qml")
layer.triggerRepaint()
```

## 标注

- 字段选择: 优先短字段名
- 字体: 8-12pt
- 位置: 居中/偏移
- 避让: 开启

## 地图元素标准

- **标题**: 14-18pt, 顶部居中
- **图例**: 右下角, 2-4列
- **比例尺**: 左下角, 数字+分段线
- **指北针**: 右上角或左上角

## 参考
- `tjukanovt/qgis_styles` — 制图样式合集
- `apply_style_qml.py` — QML应用模板
- `add_north_arrow_and_log.py` — 指北针+日志
