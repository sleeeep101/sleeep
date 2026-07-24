# QGIS 错误恢复手册

> 面向 Claude → Codex 自动作图流程。Codex 执行中遇到错误时的标准恢复流程。

## 错误分类

### 1. 文件类错误
| 错误 | 现象 | 恢复操作 | 是否继续 |
|------|------|---------|:------:|
| 输入文件不存在 | `FileNotFoundError` | 检查路径拼写;确认文件未移动;报告Claude | 停止 |
| 输出目录不存在 | `FileNotFoundError` | `Path.mkdir(parents=True)` 自动创建 | 继续 |
| 文件被占用 | `PermissionError` | 关闭其他程序;换输出路径 | 停止 |

### 2. 图层类错误
| 错误 | 现象 | 恢复操作 |
|------|------|---------|
| 矢量图层无效 | `layer.isValid()=False` | 检查文件格式;尝试指定provider("ogr"/"GPKG") |
| 栅格图层无效 | `raster.isValid()=False` | 检查tif完整性;检查波段数 |
| CRS未定义 | `layer.crs().authid()=''` | 手动设置 `layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))` |

### 3. Processing类错误
| 错误 | 现象 | 恢复操作 |
|------|------|---------|
| 算法不存在 | `Algorithm not found` | 检查算法名(native:xxx / gdal:xxx);检查QGIS版本 |
| 参数错误 | `Unable to execute algorithm` | 检查INPUT路径;检查OUTPUT路径父目录存在 |
| 内存不足 | 卡住/超时 | 减小处理范围;降低分辨率 |

### 4. 布局导出类错误
| 错误 | 现象 | 恢复操作 |
|------|------|---------|
| 布局为空 | `No map items` | Add Map item before export |
| 导出路径无效 | `Export failed` | 确保输出目录存在且有写入权限 |
| DPI设置异常 | 导出文件异常大或模糊 | 默认300dpi;范围72-600 |

## 通用恢复流程

```
错误发生 → 记录完整错误信息 → 判断是否可自动修复
  ├─ 可自动修复 → 执行修复 → 验证 → 继续
  └─ 不可自动修复 → 记录到日志 → 报告Claude → 停止当前步骤
```

## Codex额度耗尽时

错误恢复暂停。不提供用户手动修复步骤。等待额度恢复后继续。
