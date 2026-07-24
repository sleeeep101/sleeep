# Codex 待执行任务包 — QGIS 自动作图真实测试

## 1. 任务状态

- **Codex 额度状态:** 不可用
- **当前策略:** 暂停作图，等待额度恢复 + GIS 数据就绪
- **是否允许用户手动执行:** 否

## 2. 作图目标

"论文研究区 DEM 地形 + 行政区边界自动制图与导出测试"

基于真实 DEM 栅格 + 矢量边界，完成完整 QGIS 自动作图流程并导出成果。

## 3. 输入数据（待获取）

| 数据 | 路径（占位） | 类型 | 已确认 |
|------|------------|------|:----:|
| DEM 30m | `<data_dir>/dem_30m.tif` | 栅格 GeoTIFF | ❌ |
| 研究区边界 | `<data_dir>/study_area.shp` | 矢量面 | ❌ |

## 4. 输出要求

| 输出文件 | 路径 | 格式 |
|---------|------|------|
| 地形分析图 | `test_outputs/real_task_20260606/dem_hillshade_map.png` | PNG 300dpi |
| 地形分析图 | `test_outputs/real_task_20260606/dem_hillshade_map.pdf` | PDF |
| QGIS 项目 | `test_outputs/real_task_20260606/project.qgz` | QGS |
| 执行日志 | `test_outputs/real_task_20260606/execution_log.md` | MD |

## 5. 地图设计参数

- **标题:** 研究区地形分析图
- **CRS:** EPSG:4326
- **图层顺序（下→上）:** DEM山影 → 研究区边界（半透明填充+黑色轮廓）
- **样式:** DEM 灰度山影渲染；边界黑色轮廓半透明填充
- **图例:** 是
- **比例尺:** 是
- **指北针:** 是
- **导出尺寸:** A4

## 6. Codex 执行步骤摘要

1. 打开 QGIS → 新建项目 → 设置 CRS EPSG:4326
2. 加载 dem_30m.tif → 使用 raster_clip_reproject.py hillshade 生成山影
3. 加载 study_area.shp → 设置样式（半透明+轮廓）
4. 创建 Print Layout "TerrainAnalysis"
5. 添加地图、标题、图例、比例尺、指北针
6. 导出 PNG (300dpi) + PDF
7. 保存项目 project.qgz
8. 截图确认

## 7. 验收标准

- [ ] DEM 山影图成功生成
- [ ] 矢量边界正确叠加
- [ ] PNG 文件存在且清晰可读
- [ ] PDF 文件存在且可打开
- [ ] QGIS 项目可重新打开
- [ ] 原始文件未被修改（SHA256 不变）

## 8. 暂停记录

- **暂停原因:** Claude 无 Codex computer use 调用能力 + 本地无 GIS 数据
- **恢复条件:** 1) Codex 额度可用 2) 获取 DEM+矢量边界数据
- **当前不生成地图成果**
