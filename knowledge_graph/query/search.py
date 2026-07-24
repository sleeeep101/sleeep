"""
知识图谱查询模块
===============
搜索、遍历、路径发现、推荐。
"""

from typing import List, Dict, Any, Optional

import networkx as nx

from ..graph.builder import KnowledgeGraphBuilder


class KnowledgeGraphQuery:
    """知识图谱查询接口"""

    def __init__(self, builder: KnowledgeGraphBuilder):
        self.builder = builder
        self.graph = builder.graph

    # ── 搜索 ──────────────────────────────────────────

    def search(self, keyword: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """关键词搜索节点"""
        results = []
        keyword_lower = keyword.lower()

        for node_id, attrs in self.graph.nodes(data=True):
            etype = attrs.get("entity_type", "")
            if entity_types and etype not in entity_types:
                continue

            # 搜索 ID、标签、各字段
            searchable = f"{node_id} {attrs.get('label', '')} "
            for k, v in attrs.items():
                if isinstance(v, str):
                    searchable += v + " "
                elif isinstance(v, list):
                    searchable += " ".join(str(x) for x in v) + " "

            if keyword_lower in searchable.lower():
                results.append({
                    "id": node_id,
                    "type": etype,
                    "label": attrs.get("label", node_id),
                    "degree": self.graph.degree(node_id),
                    "attrs": {k: v for k, v in attrs.items()
                              if k not in ("label", "entity_type", "color")},
                })

        # 按 degree 排序（连接多的在前）
        results.sort(key=lambda r: r["degree"], reverse=True)
        return results

    # ── 邻居 ──────────────────────────────────────────

    def neighbors(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """获取节点的 N 度邻居"""
        if node_id not in self.graph:
            return {"error": f"节点 {node_id} 不存在"}

        result = {
            "node": {
                "id": node_id,
                "label": self.graph.nodes[node_id].get("label", node_id),
                "type": self.graph.nodes[node_id].get("entity_type", ""),
            },
            "neighbors": {},
        }

        # 使用 BFS 获取 N 度邻居
        for d in range(1, depth + 1):
            neighbors_at_depth = []
            if d == 1:
                # 直接邻居
                for neighbor in self.graph.neighbors(node_id):
                    edges = self.graph.get_edge_data(node_id, neighbor)
                    for key, edge_data in (edges or {}).items():
                        neighbors_at_depth.append({
                            "id": neighbor,
                            "label": self.graph.nodes[neighbor].get("label", neighbor),
                            "type": self.graph.nodes[neighbor].get("entity_type", ""),
                            "relation": edge_data.get("type", "unknown"),
                            "confidence": edge_data.get("confidence", 1.0),
                        })
            else:
                # 更深层：简单 BFS
                visited = {node_id}
                frontier = [node_id]
                for _ in range(d):
                    new_frontier = []
                    for n in frontier:
                        for neighbor in self.graph.neighbors(n):
                            if neighbor not in visited:
                                visited.add(neighbor)
                                new_frontier.append(neighbor)
                    frontier = new_frontier

                for n in frontier:
                    neighbors_at_depth.append({
                        "id": n,
                        "label": self.graph.nodes[n].get("label", n),
                        "type": self.graph.nodes[n].get("entity_type", ""),
                    })

            result["neighbors"][f"depth_{d}"] = neighbors_at_depth

        return result

    # ── 路径 ──────────────────────────────────────────

    def find_path(self, from_id: str, to_id: str) -> Optional[List[str]]:
        """查找两个节点间的最短路径"""
        if from_id not in self.graph or to_id not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph, from_id, to_id)
            # 标注每步的关系类型
            annotated = []
            for i, node in enumerate(path):
                entry = {
                    "id": node,
                    "label": self.graph.nodes[node].get("label", node),
                    "type": self.graph.nodes[node].get("entity_type", ""),
                }
                if i > 0:
                    prev = path[i - 1]
                    edges = self.graph.get_edge_data(prev, node)
                    if edges:
                        edge = list(edges.values())[0]
                        entry["relation"] = edge.get("type", "unknown")
                annotated.append(entry)
            return annotated
        except nx.NetworkXNoPath:
            return None

    # ── 推荐 ──────────────────────────────────────────

    def recommend(self, node_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """基于图的协同推荐：同一篇论文关联的其他实体"""
        if node_id not in self.graph:
            return []

        # 找到当前节点的直接邻居
        direct_neighbors = set(self.graph.neighbors(node_id))

        # 找到 neighbor-of-neighbor（当前节点两跳可达）
        candidates: Dict[str, float] = {}
        for neighbor in direct_neighbors:
            for n2 in self.graph.neighbors(neighbor):
                if n2 != node_id and n2 not in direct_neighbors:
                    candidates[n2] = candidates.get(n2, 0) + 1

        # 按共同邻居数排序
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)

        results = []
        for cid, score in sorted_candidates[:top_k]:
            results.append({
                "id": cid,
                "label": self.graph.nodes[cid].get("label", cid),
                "type": self.graph.nodes[cid].get("entity_type", ""),
                "score": score,
            })

        return results

    # ── 统计 ──────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """图统计 + top 节点"""
        base_stats = self.builder.stats()
        if not self.graph.number_of_nodes():
            return base_stats

        # Top 10 度最高节点
        degrees = sorted(self.graph.degree(), key=lambda x: x[1], reverse=True)
        top_nodes = []
        for nid, deg in degrees[:10]:
            top_nodes.append({
                "id": nid,
                "label": self.graph.nodes[nid].get("label", nid),
                "type": self.graph.nodes[nid].get("entity_type", ""),
                "degree": deg,
            })
        base_stats["top_nodes"] = top_nodes

        return base_stats
