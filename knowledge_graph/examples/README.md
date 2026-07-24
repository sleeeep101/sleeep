# 公开知识图谱示例

`public_graph.json` 仅含 3 个合成节点和 2 条合成关系，用于验证安装、查询与可视化命令；它不是论文数据、研究结论、参考文献，也不应进入正式分析或写作。

从工作流根目录运行：

```powershell
python -m knowledge_graph stats --graph-file knowledge_graph/examples/public_graph.json
python -m knowledge_graph query "gully erosion" --graph-file knowledge_graph/examples/public_graph.json
```

正式使用时，先从已获授权且去标识化的资料构建图谱。默认构建不会读取 Personal-Brain、桌面笔记或联系人文件；只有显式传入 `--include-private-sources` 才会尝试读取这些本地来源。
