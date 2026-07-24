# Knowledge Graph — Public Example

`public_graph.json` contains **3 synthetic nodes and 2 synthetic relations** for verifying installation, query, and visualization commands. It is NOT paper data, research conclusions, or reference material.

From the workflow root:

```powershell
python -m knowledge_graph stats --graph-file knowledge_graph/examples/public_graph.json
python -m knowledge_graph query "gully erosion" --graph-file knowledge_graph/examples/public_graph.json
```

For production use, build a graph from authorized, de-identified materials. The default build pipeline never reads personal directories; only passing `--include-private-sources` explicitly will attempt to read local private sources. Keep `kg_data.json` outside version control.
