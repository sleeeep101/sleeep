# PyQGIS Templates — QGIS Python 脚本模板

> 所有模板使用占位路径，不写死用户隐私路径。
> 兼容 QGIS Python 控制台或 QGIS 内置 Python 环境。
> 每个脚本顶部写清用途，输出前检查输入是否存在。

## 模板清单

| 模板 | 用途 | 输入 | 输出 |
|------|------|------|------|
| `load_vector_layer.py` | 加载矢量图层到项目 | shp/gpkg/geojson | QGIS 图层 |
| `load_raster_layer.py` | 加载栅格图层到项目 | tif/img | QGIS 图层 |
| `apply_style_qml.py` | 应用 QML 样式 | layer + qml 文件 | 样式化图层 |
| `create_layout_export_png_pdf.py` | 创建 Print Layout + 导出 | QGIS 项目 + 图层 | PNG/PDF |
| `batch_export_maps.py` | 按字段批量导出地图 | 矢量图层 + 字段 | 多张 PNG/PDF |
| `vector_clip_buffer_intersect.py` | 矢量裁剪/缓冲区/相交 | 矢量文件 | 处理结果 |
| `raster_clip_reproject.py` | 栅格裁剪/重投影/山影/坡度 | 栅格文件 | 处理结果 |
| `project_save_and_package.py` | 保存并打包项目 | QGIS 项目 | qgz/zip |
| `attribute_filter_and_field_calc.py` | 属性筛选+字段计算 | 矢量文件 | GeoPackage |
| `add_north_arrow_and_log.py` | 指北针添加+JSON日志 | Print Layout | 指北针+log文件 |

## 使用方式

1. 在 QGIS Python 控制台中粘贴运行
2. 或在 QGIS 自带 Python 中: `python script.py`
3. Codex 通过 Computer Use 复制粘贴到 QGIS 控制台

## 注意

- 不自动删除原始数据
- 不联网
- 输出前检查输入是否存在
- 对 CRS、加载失败、导出失败给出明确报错
