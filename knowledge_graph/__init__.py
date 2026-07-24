"""
科研知识图谱 — Academic Knowledge Graph
=====================================
构建、查询、可视化科研全流程知识连接。

用法:
  python -m knowledge_graph build       # 全量建图
  python -m knowledge_graph query <kw>   # 搜索
  python -m knowledge_graph show <id>    # 查看节点
  python -m knowledge_graph viz          # 可视化

快速集成:
  from knowledge_graph.graph.builder import KnowledgeGraphBuilder
  builder = KnowledgeGraphBuilder.load()
  print(builder.stats())
"""

__version__ = "0.1.0"
