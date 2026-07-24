# 01 问题陈述

## 目标

Claude 生成 QGIS 作图指令 → Codex 使用 Computer Use 操作 QGIS → 输出地图成果

## 失败点

1. Claude 无法直接调用 Codex（两者是不同公司的独立产品）
2. 之前测试中出现 `Computer Use native pipe path is unavailable`
3. QGIS 真实作图测试未通过 Codex Computer Use 链路完成

## 不可接受方案

- Claude 直接作图（PyQGIS headless 替代）
- 用户手动作图
- 用户粘贴 PyQGIS
- qgis_process 替代
- 未执行写成完成

## 需要确认

是否存在可靠链路让 Claude 触发 Codex 执行
