# 测试样例：论文知识卡片（用于文献综述测试）

## 论文1
- 标题: GIS-based multi-criteria decision analysis for landslide susceptibility
- 方法: AHP + 加权线性组合(WLC)
- 数据: DEM 30m, 地质图 1:50000, 土地利用图
- 主要结果: AUC=0.85, 坡度是最主要的影响因子
- 局限: 未考虑降雨动态变化

## 论文2
- 标题: Deep learning approach for landslide detection using Sentinel-2 imagery
- 方法: U-Net + 数据增强
- 数据: Sentinel-2 10m, 历史滑坡清单
- 主要结果: F1=0.78, 优于随机森林(F1=0.65)
- 局限: 小滑坡检测效果差, 云覆盖区域无法检测

## 论文3
- 标题: Comparison of statistical and machine learning models for landslide susceptibility
- 方法: 逻辑回归 vs. 随机森林 vs. XGBoost
- 数据: 12个环境因子
- 主要结果: XGBoost最优(AUC=0.91), 但可解释性差
- 局限: 样本不平衡问题未充分处理
