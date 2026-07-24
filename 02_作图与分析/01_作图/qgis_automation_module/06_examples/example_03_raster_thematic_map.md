# Example 03: 栅格专题图 (DEM + 山影 + 坡度)

## 输入
- DEM 栅格: dem_30m.tif (EPSG:4326)

## 目标图
山影渲染图 + 坡度叠加，PDF 导出

## Claude 指令
```
【任务目标】基于 DEM 生成山影渲染 + 坡度图，组合为专题地图

【输入数据】/path/to/dem_30m.tif

【输出要求】/path/to/output/dem_thematic.pdf

【地图元素】标题:"地形分析图" | 图例:是 | CRS:EPSG:3857
```

## Codex 执行步骤
1. 加载 dem_30m.tif
2. Processing → Toolbox → 搜索 "hillshade" → 设置 azimuth=315, angle=45 → Run
3. Processing → Toolbox → 搜索 "slope" → Run
4. 对山影图层: Properties → Symbology → 选择合适灰度渲染
5. 对坡度图层: Properties → Symbology → 选择分级色彩
6. 创建 Print Layout → 添加3个子图 (DEM原图 + 山影 + 坡度)
7. 添加标题、图例
8. Export PDF

## PyQGIS 脚本
使用 `raster_clip_reproject.py` 的 hillshade 和 slope 函数

## 验收标准
- [ ] dem_thematic.pdf 存在
- [ ] 3个子图可见 (DEM原图/山影/坡度)
- [ ] 山影显示地形起伏
- [ ] 坡度分级色彩正确

## Codex 额度耗尽时

- 本示例暂停执行
- 不生成手动操作替代方案
- 只保存待执行信息: 输入路径 / 输出路径 / CRS EPSG:3857 / 地图标题 / 验收标准
