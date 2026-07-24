# Scripts 脚本注册表

## 核心脚本

| 脚本 | 用途 | 触发方式 | 输入 | 输出 |
|------|------|---------|------|------|
| `daily_paper_curator.py` | 每日论文全流程引擎 | Windows Task Scheduler / 手动 | 桌面PDF + scholar-mcp | 日报 + 知识卡片 + KG |
| `ingest_pdf.py` | PDF文本提取（7引擎级联） | CLI `--pdf` / `--dir` | PDF文件 | paper.md + metadata.json |
| `import_claude_paper_reading.py` | 导入Claude手动阅读笔记 | CLI | markdown阅读笔记 | 统一格式 + 元数据 |
| `fulltext_utils.py` | 全文获取工具集 | import调用 | DOI/URL | PDF下载 + 元数据 |
| `paper_source_utils.py` | 论文源数据处理 | import调用 | 论文元数据 | source.json + 归档 |
| `build_public_release.py` | 构建不含本地资料的公开副本 | CLI | 本地工作流目录 | 新的公开发布目录 |

## 批处理入口

| 文件 | 用途 |
|------|------|
| `run_paper_curator.bat` | Windows定时任务入口，调用 `daily_paper_curator.py` |

## 使用示例

```bash
# PDF提取（自动选择引擎）
python scripts/ingest_pdf.py --pdf "paper.pdf"

# PDF提取（强制OCR）
python scripts/ingest_pdf.py --pdf "paper.pdf" --force-ocr

# 批量目录
python scripts/ingest_pdf.py --dir "pdf_folder/"

# 导入Claude阅读
python scripts/import_claude_paper_reading.py --source "reading.md" --pdf "original.pdf"

# 查看可用引擎
python scripts/ingest_pdf.py --list-engines

# 先筛查，再创建新的公开副本；不会移动、删除或限制本地资料的位置
python scripts/build_public_release.py --destination "path/to/academic-workflow-public" --dry-run
python scripts/build_public_release.py --destination "path/to/academic-workflow-public" --redact-local-paths
```

公开发布构建器会排除阅读语料、运行日志、个人待确认区、生成图谱和已知历史运行记录；随后扫描候选文本中的绝对本机路径。默认发现路径会拒绝构建；明确传入 `--redact-local-paths` 时，只会在新发布副本中以 `<LOCAL_PATH>` 替换路径。它不会修改源目录，也不会覆盖已存在的目标目录。

## 依赖关系

```
daily_paper_curator.py
  ├── fulltext_utils.py (全文下载)
  ├── paper_source_utils.py (数据管理)
  ├── pdf_ingest/ (PDF提取模块)
  └── knowledge_graph.kg_hook (知识图谱更新)
```

*最后更新: 2026-07-24*
