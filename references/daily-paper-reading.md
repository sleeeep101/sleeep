# 每日论文精读流程

## 主流程：桌面PDF批量精读

```
桌面PDF → process_desktop_pdfs.py → 文本提取(pdf_ingest) → Claude精读 → 日报 → 知识卡片 → KG更新
```

## 每日最低质量标准

| 指标 | 基线 |
|------|------|
| 最少精读篇数 | 3篇（≥60分入库） |
| 日报产出 | `01_每日论文/YYYY-MM-DD_论文阅读日报.md` |
| 知识卡片 | 每篇22字段（含方法提取+迁移价值+可信度） |
| KG同步 | `finalize_daily_reading_batch.py` 验证通过后自动更新 |

## 备用流程：在线检索

当无桌面PDF时使用semantic-scholar检索（已搁置，等待scholar-mcp-server配置）。

## 阅读后处理

1. PDF归档 → `02_论文阅读库/paper_sources/`
2. 中间产物清理 → OCR临时文件/Python缓存
3. 知识卡片入库 → `04_长期知识库/长期知识库.md`
4. KG更新 → `kg_hook.update_kg_if_changed()`

*最后更新: 2026-07-24*
