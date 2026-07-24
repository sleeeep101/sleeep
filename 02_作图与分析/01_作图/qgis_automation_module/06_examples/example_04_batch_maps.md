# Example 04: 按区域批量导出地图

## 输入
- 全国省界: province.shp (字段: NAME)
- DEM: dem_china.tif

## 目标
按省份逐个导出 DEM + 省界叠加地图，共 34 张 PNG

## Claude 指令
```
【任务目标】按省份 NAME 字段逐个导出省域 DEM 地图

【输入数据】/path/to/province.shp (字段:NAME) | /path/to/dem_china.tif

【输出要求】/path/to/output/batch_maps/ (34张PNG)

【操作方式】使用 batch_export_maps.py 模板

【验收标准】34张PNG全部存在，每张清晰可见省界+DEM
```

## Codex/Claude 执行步骤
1. 修改 `batch_export_maps.py` 中的路径和字段名
2. 在 QGIS Python 控制台运行脚本
3. 或方案 E: 先导出一个省确认效果，再批量
4. 完成后检查输出目录文件数 = 34

## PyQGIS 脚本
`batch_export_maps.py` (已适配)

## 验收标准
- [ ] 34 张 PNG 文件
- [ ] 每张标题显示省份名
- [ ] DEM 正确渲染

## Codex 额度耗尽时

- 本示例暂停执行
- 不生成手动操作替代方案
- 只保存待执行信息: 输入路径 / 输出目录 / 字段名 NAME / 批量参数 / 验收标准
