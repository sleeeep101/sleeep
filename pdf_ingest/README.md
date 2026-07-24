# PDF 摄入模块：安装、使用与公开边界

本模块将单篇或目录中的 PDF 转为 Markdown、元数据、分块和质量报告。它是提取工具，不是论文真实性、引用准确性或结论可靠性的证明。

## 最小可用配置

1. 安装 Python 3.10+。
2. 在工作流根目录运行 `python pdf_ingest/ingest_pdf.py --list-engines`，先确认本机实际可用的引擎。
3. 从一份可公开的 PDF 副本开始：`python pdf_ingest/ingest_pdf.py --pdf path/to/paper.pdf --engine auto`。
4. 查看生成目录内的 `extraction_report.md`，对表格、公式、参考文献和 OCR 文本进行人工抽查。

## 不含个人资料的自检示例

仓库不附带论文全文。下载后可先在临时目录生成一页**合成 PDF**，再验证本机的提取链路：

```powershell
python -m unittest pdf_ingest.tests.test_end_to_end_public_fixture
```

该测试只在临时目录写入固定的英文示例句，测试结束即删除；它只能证明“PDF 能被当前环境提取并写出 `paper.md`”，不能证明 OCR、表格、公式或真实论文的提取质量。

为减少误上传时的隐私风险，`paper.md`、`metadata.json` 和 `extraction_report.md` 只记录源文件名与内容哈希，不记录本机绝对路径。原始 PDF、提取文本和处理结果仍应先按研究资料处理，不应因为路径被隐藏就直接公开。

## 可选组件

| 需求 | 可选组件 | 验证方式 |
|---|---|---|
| 常规 PDF 文本 | `pymupdf4llm`、PyMuPDF、pdfplumber 或 pypdf（任一可用即可） | `--list-engines` |
| 扫描件 OCR | EasyOCR，或 Tesseract + `pytesseract` | `--list-engines` 与抽样校对 |
| Markdown 兜底 | MarkItDown | `--list-engines` |
| 结构化 XML/TEI（可选服务） | GROBID 服务 + 客户端 | 仅在受控环境验证输出 |

不要把软件安装路径写进脚本。若 Tesseract 或 MarkItDown 不在系统 `PATH` 中，可在当前终端设置 `PDF_INGEST_TESSERACT` 或 `PDF_INGEST_MARKITDOWN` 后再运行；这些环境变量不应提交到仓库。

## GROBID 的适用边界

GROBID 可作为高结构化提取的**可选服务**，不应替代当前本地级联，也不应默认启动容器或上传文件。Windows 用户优先使用已受控的远程/容器服务，并对输出的题名、作者、参考文献与公式进行抽样复核。

来源与改编说明（2026-07-24）：参考 [grobidOrg/grobid-client-python](https://github.com/grobidOrg/grobid-client-python)（Apache-2.0）关于客户端—服务端分离的部署边界；本文为工作流重新编写，未引入其代码或依赖。
