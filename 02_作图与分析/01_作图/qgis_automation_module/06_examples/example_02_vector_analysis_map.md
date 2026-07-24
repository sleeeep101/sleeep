# Example 02: 矢量分析制图 (裁剪+缓冲区+相交)

## 输入
- 研究区边界: study_area.shp
- 道路线: roads.shp
- 土地利用: landuse.shp

## 目标图
研究区内道路缓冲区与土地利用相交分析结果图

## Claude 指令
```
【任务目标】裁剪道路和土地利用到研究区范围 → 道路做500m缓冲区 → 与土地利用相交 → 制图

【输入数据】
| /path/to/study_area.shp | 矢量(面) | 研究区边界 |
| /path/to/roads.shp | 矢量(线) | 道路 |
| /path/to/landuse.shp | 矢量(面) | 土地利用 |

【输出要求】/path/to/output/vector_analysis.png

【地图元素】标题:"道路缓冲区与土地利用相交分析" | 图例:是 | CRS:EPSG:3857
```

## Codex 执行步骤
1. 加载3个图层
2. Processing → Clip (roads by study_area)
3. Processing → Clip (landuse by study_area)
4. Processing → Buffer (clipped_roads, 500m)
5. Processing → Intersection (buffer × landuse)
6. 对相交结果按土地利用类型分类着色
7. 创建 Print Layout → 添加地图 + 图例 → 导出

## PyQGIS 脚本
使用 `vector_clip_buffer_intersect.py` 模板

## 验收标准
- [ ] 输出 PNG 存在
- [ ] 研究区边界裁剪正确
- [ ] 缓冲区 500m 可见
- [ ] 图例区分不同土地利用类型

## Codex 额度耗尽时

- 本示例暂停执行
- 不生成手动操作替代方案
- 只保存待执行信息: 输入路径 / 输出路径 / CRS EPSG:3857 / 分析步骤 / 验收标准
