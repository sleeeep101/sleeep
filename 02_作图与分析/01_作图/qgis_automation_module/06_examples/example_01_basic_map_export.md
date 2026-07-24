# Example 01: 基础行政区矢量图导出

## 输入
- 矢量文件: 省/市/县边界 shp
- 字段: 行政区名称 (NAME)

## 目标图
带标题、图例、比例尺、指北针的行政区划图，PNG 300dpi 导出

## Claude 指令
```
【任务目标】加载行政区划矢量数据，按 NAME 字段分类着色，导出 A4 地图

【输入数据】/path/to/admin_boundary.shp

【输出要求】/path/to/output/admin_map.png (PNG 300dpi)

【地图元素】标题:"行政区划图" | 图例:是 | 比例尺:是 | 指北针:是 | CRS:EPSG:4326
```

## Codex 执行步骤
1. 打开 QGIS
2. 拖拽 admin_boundary.shp 到地图窗口
3. 右键图层 → Properties → Symbology → Categorized → 选 NAME 字段 → Classify → OK
4. Project → New Print Layout → 命名为 "AdminMap"
5. Add Map (拖满整页)
6. Add Legend (右下角)
7. Add Scale Bar (左下角)
8. Add Label "行政区划图" (顶部居中)
9. Layout → Export as Image → 300dpi → admin_map.png
10. 截图确认

## PyQGIS 脚本
参考 `create_layout_export_png_pdf.py` 模板，设置标题和图例

## 验收标准
- [ ] admin_map.png 文件存在
- [ ] 图层正确加载，分类着色可见
- [ ] 图例显示 NAME 字段值
- [ ] 标题"行政区划图"出现在图上方
- [ ] 图片清晰可读 (300dpi)

## Codex 额度耗尽时

- 本示例暂停执行
- 不生成手动操作替代方案
- 不让用户手动粘贴代码
- 只保存以下待执行信息:
  - 输入数据路径
  - 输出路径: /path/to/output/admin_map.png
  - 地图标题: "行政区划图"
  - CRS: EPSG:4326
  - 图层顺序: admin_boundary.shp
  - 样式要求: 按 NAME 字段分类着色
  - 导出格式: PNG 300dpi
  - 验收标准: 见上方
