"""
pyvis 交互式可视化
================
将 NetworkX 图渲染为交互式 HTML。
"""

import os
from typing import Optional

import networkx as nx

from ..kg_config import ENTITY_COLORS


def render_pyvis(
    graph: nx.MultiDiGraph,
    output_path: str,
    title: str = "科研知识图谱 — Academic Knowledge Graph",
    height: str = "800px",
    width: str = "100%",
) -> str:
    """
    用 pyvis 渲染 NetworkX 图为交互式 HTML。

    Args:
        graph: NetworkX 图
        output_path: 输出 HTML 路径
        title: 页面标题
        height: 画布高度
        width: 画布宽度
    """
    try:
        from pyvis.network import Network
    except ImportError:
        raise ImportError("请先安装 pyvis: pip install pyvis")

    net = Network(height=height, width=width, directed=True, notebook=False)
    net.set_options(_get_pyvis_options())

    # 添加节点
    for node_id, attrs in graph.nodes(data=True):
        etype = attrs.get("entity_type", "Unknown")
        color = ENTITY_COLORS.get(etype, "#999999")
        label = attrs.get("label", node_id)[:80]
        degree = graph.degree(node_id)

        net.add_node(
            node_id,
            label=label,
            title=_make_tooltip(node_id, attrs),
            color=color,
            size=max(8, min(30, degree * 3)),
            group=etype,
        )

    # 添加边
    for u, v, key, data in graph.edges(keys=True, data=True):
        rel_type = data.get("type", "")
        confidence = data.get("confidence", 1.0)
        net.add_edge(
            u, v,
            title=f"{rel_type} (置信度: {confidence:.0%})",
            label=rel_type,
            arrows="to",
            color={"color": "#999999", "opacity": 0.5},
        )

    # 保存
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    net.save_graph(output_path)
    return output_path


def _make_tooltip(node_id: str, attrs: dict) -> str:
    """生成节点悬停提示"""
    etype = attrs.get("entity_type", "")
    lines = [f"<b>{etype}</b>: {node_id}"]

    for key in ["title", "english", "chinese", "name", "summary", "description",
                 "canonical_name", "rule", "purpose"]:
        val = attrs.get(key, "")
        if val and isinstance(val, str) and len(val) > 1:
            lines.append(f"{key}: {val[:150]}")

    for key in ["topics", "methods", "keywords", "scenarios", "aliases"]:
        val = attrs.get(key, [])
        if val and isinstance(val, list) and len(val) > 0:
            lines.append(f"{key}: {', '.join(str(x) for x in val[:5])}")

    for key in ["score", "grade", "year", "credibility", "paper_count"]:
        val = attrs.get(key)
        if val is not None and val != "":
            lines.append(f"{key}: {val}")

    return "<br>".join(lines)


def _get_pyvis_options() -> str:
    """pyvis 配置选项"""
    return """
    {
      "physics": {
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.005,
          "springLength": 150,
          "springConstant": 0.08,
          "damping": 0.4
        },
        "stabilization": {
          "iterations": 200
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      },
      "edges": {
        "smooth": {
          "type": "continuous"
        },
        "font": {
          "size": 8,
          "strokeWidth": 0
        }
      },
      "nodes": {
        "font": {
          "size": 11,
          "face": "Microsoft YaHei, sans-serif"
        }
      }
    }
    """
