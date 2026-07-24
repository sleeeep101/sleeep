"""
Mermaid + Canvas JSON 导出
==========================
从 NetworkX 图渲染 Mermaid flowchart 和 Canvas JSON。
"""

import json
import re
from typing import Optional, Dict, List

import networkx as nx


def to_mermaid(graph: nx.DiGraph, max_nodes: int = 80) -> str:
    """渲染为 Mermaid flowchart，可嵌入 Markdown 渲染。

    用法:
        ```mermaid
        graph LR
          node1[Paper: XGBoost DEM]
          node2[Method: XGBoost]
          node1 -->|USES_METHOD| node2
        ```
    """
    _SAFE = re.compile(r"[^A-Za-z0-9_]")

    def mid(s: str) -> str:
        safe = _SAFE.sub("_", s)
        if not safe or safe[0].isdigit():
            safe = "n_" + safe
        return safe[:48]

    def label(attrs: dict) -> str:
        raw = str(attrs.get("label", ""))[:60]
        return raw.replace('"', "'").replace("\n", " ")

    lines = ["graph LR"]

    # Top nodes by degree
    deg = dict(graph.degree())
    top_nodes = sorted(graph.nodes(data=True),
                       key=lambda x: deg.get(x[0], 0), reverse=True)[:max_nodes]
    top_ids = {n[0] for n in top_nodes}

    # Add nodes
    for node_id, attrs in top_nodes:
        nid = mid(node_id)
        etype = attrs.get("entity_type", "")[:12]
        lines.append(f'  {nid}["{etype}: {label(attrs)}"]')

    # Add edges for top nodes
    edge_count = 0
    for u, v, data in graph.edges(data=True):
        if u in top_ids and v in top_ids and edge_count < 200:
            rel = data.get("type", "")[:15]
            lines.append(f"  {mid(u)} -->|{rel}| {mid(v)}")
            edge_count += 1

    return "\n".join(lines)


def to_canvas_json(
    graph: nx.DiGraph,
    output_path: str,
    max_nodes: int = 100,
) -> str:
    """导出为 Canvas JSON 格式。

    Canvas JSON 格式:
    {
      "nodes": [
        {"id": "...", "type": "text", "x": 0, "y": 0, "width": 300, "height": 200, "text": "..."}
      ],
      "edges": [
        {"id": "...", "fromNode": "...", "toNode": "...", "fromSide": "right", "toSide": "left", "label": "..."}
      ]
    }
    """
    deg = dict(graph.degree())
    top_nodes = sorted(graph.nodes(data=True),
                       key=lambda x: deg.get(x[0], 0), reverse=True)[:max_nodes]
    top_ids = {n[0] for n in top_nodes}

    # Layout in a grid
    cols = 8
    canvas_nodes = []
    for i, (node_id, attrs) in enumerate(top_nodes):
        etype = attrs.get("entity_type", "")
        node_label = attrs.get("label", node_id)[:80]
        row, col = divmod(i, cols)
        canvas_nodes.append({
            "id": node_id,
            "type": "text",
            "x": col * 320,
            "y": row * 220,
            "width": 300,
            "height": 200,
            "text": f"## [{etype}] {node_label}\n\n**ID:** {node_id}",
        })

    canvas_edges = []
    edge_count = 0
    for u, v, data in graph.edges(data=True):
        if u in top_ids and v in top_ids and edge_count < 300:
            rel = data.get("type", "")
            canvas_edges.append({
                "id": f"e_{edge_count}",
                "fromNode": u,
                "toNode": v,
                "fromSide": "right",
                "toSide": "left",
                "label": rel,
            })
            edge_count += 1

    canvas_data = {"nodes": canvas_nodes, "edges": canvas_edges}

    import os
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)

    return output_path
