# Markdown → DOCX/PDF 输出格式检查

> Prompt ID: 11 | 用途: 检查 Markdown 草稿在转 DOCX/PDF 前的格式问题

## 检查清单
- 标题层级是否正确（# → ## → ###，不跳级）
- 图表是否有编号和标题（图1、表1）
- 表格是否有表头
- 参考文献是否集中在文末
- 中英文标点是否混用
- 代码块是否有语言标注
- 公式是否正确
- 是否有空段落/多余空格

## 快速命令
```bash
pandoc draft.md -o draft.docx --reference-doc=template.docx
pandoc draft.md -o draft.pdf --pdf-engine=xelatex
```
