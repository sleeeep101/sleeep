"""
知识图谱健康监控
================
每次 build 后自动运行，检测异常并生成报告。
零外部依赖。
"""

import os, json, re
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter

import networkx as nx

from .kg_config import KG_DATA_FILE, LONG_TERM_KB, TERMINOLOGY_DB, TECHNIQUE_DB


class HealthMonitor:
    """图谱健康监控器"""

    def __init__(self, graph: nx.DiGraph, entities: Dict[str, Dict],
                 kg_file: str = KG_DATA_FILE):
        self.graph = graph
        self.entities = entities
        self.kg_file = kg_file

    def check_all(self) -> Dict[str, Any]:
        """全量健康检查"""
        return {
            "timestamp": datetime.now().isoformat(),
            "status": self._overall_status(),
            "connectivity": self._check_connectivity(),
            "growth": self._check_growth(),
            "anomalies": self._detect_anomalies(),
            "warnings": self._generate_warnings(),
        }

    # ── 总体状态 ──────────────────────────────────────

    def _overall_status(self) -> str:
        """红/黄/绿 状态判定"""
        warnings = self._generate_warnings()
        critical = [w for w in warnings if w["level"] == "critical"]
        if critical:
            return "RED"
        warning = [w for w in warnings if w["level"] == "warning"]
        if len(warning) >= 3:
            return "YELLOW"
        return "GREEN"

    # ── 连通性 ────────────────────────────────────────

    def _check_connectivity(self) -> Dict[str, Any]:
        """连通性指标"""
        total = self.graph.number_of_nodes()
        isolated = sum(1 for n in self.graph.nodes() if self.graph.degree(n) == 0)

        # 各类型孤立率
        type_isolated = {}
        for etype in set(self.graph.nodes[n].get("entity_type", "?") for n in self.graph.nodes()):
            type_nodes = [n for n in self.graph.nodes()
                         if self.graph.nodes[n].get("entity_type") == etype]
            iso = sum(1 for n in type_nodes if self.graph.degree(n) == 0)
            if type_nodes:
                type_isolated[etype] = round(100 * iso / len(type_nodes), 1)

        return {
            "total_nodes": total,
            "total_edges": self.graph.number_of_edges(),
            "isolated_count": isolated,
            "isolated_pct": round(100 * isolated / max(total, 1), 1),
            "isolated_by_type": type_isolated,
        }

    # ── 增长检测 ──────────────────────────────────────

    def _check_growth(self) -> Dict[str, Any]:
        """检测异常增长/萎缩"""
        # 对比上次 build 的节点数
        history_file = self.kg_file.replace(".json", "_history.json")
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass

        current = {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "date": datetime.now().isoformat(),
        }

        growth = {}
        if history:
            last = history[-1] if isinstance(history, list) else history
            node_delta = current["nodes"] - last.get("nodes", 0)
            edge_delta = current["edges"] - last.get("edges", 0)
            growth = {
                "node_change": node_delta,
                "edge_change": edge_delta,
                "node_change_pct": round(100 * node_delta / max(last.get("nodes", 1), 1), 1),
                "previous_date": last.get("date", ""),
            }

        # 保存历史
        if isinstance(history, list):
            history.append(current)
            if len(history) > 30:
                history = history[-30:]
        else:
            history = [current]
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        return growth

    # ── 异常检测 ──────────────────────────────────────

    def _detect_anomalies(self) -> List[Dict]:
        """检测具体异常"""
        anomalies = []

        # 1. 孤立体超过阈值
        conn = self._check_connectivity()
        for etype, pct in conn["isolated_by_type"].items():
            if pct > 50 and conn["total_nodes"] > 0:
                type_count = sum(1 for n in self.graph.nodes()
                                if self.graph.nodes[n].get("entity_type") == etype)
                anomalies.append({
                    "type": "high_isolation",
                    "entity_type": etype,
                    "isolated_pct": pct,
                    "detail": f"{etype} 孤立率 {pct}%（>{50}%），共 {type_count} 个实体",
                })

        # 2. 边/节点比异常
        ratio = conn["total_edges"] / max(conn["total_nodes"], 1)
        if ratio < 1:
            anomalies.append({
                "type": "low_density",
                "ratio": round(ratio, 1),
                "detail": f"边/节点比 {ratio:.1f}，图谱过于稀疏",
            })

        # 3. 未知类型实体
        unknown = [n for n in self.graph.nodes()
                   if self.graph.nodes[n].get("entity_type") in ("?", "Unknown")]
        if unknown:
            anomalies.append({
                "type": "unknown_entity_type",
                "count": len(unknown),
                "detail": f"发现 {len(unknown)} 个未知类型的实体",
                "ids": unknown[:5],
            })

        # 4. 空标签实体
        empty_labels = [n for n in self.graph.nodes()
                        if not self.graph.nodes[n].get("label", "").strip()]
        if empty_labels:
            anomalies.append({
                "type": "empty_labels",
                "count": len(empty_labels),
                "detail": f"{len(empty_labels)} 个实体没有 label",
            })

        return anomalies

    # ── 告警生成 ──────────────────────────────────────

    def _generate_warnings(self) -> List[Dict]:
        """生成 actionable 的告警"""
        warnings = []
        conn = self._check_connectivity()

        # 总孤立率
        if conn["isolated_pct"] > 20:
            warnings.append({
                "level": "critical",
                "msg": f"总孤立率 {conn['isolated_pct']}%，需检查关系提取链路",
                "action": "运行 python -m knowledge_graph build 全量重建",
            })
        elif conn["isolated_pct"] > 10:
            warnings.append({
                "level": "warning",
                "msg": f"总孤立率 {conn['isolated_pct']}%，建议检查新增实体是否缺少关系",
            })

        # 核心类型连通
        for core_type in ["Paper", "Term", "Innovation"]:
            pct = conn["isolated_by_type"].get(core_type, 0)
            if pct > 30:
                warnings.append({
                    "level": "critical",
                    "msg": f"{core_type} 孤立率 {pct}%，核心知识链可能断裂",
                    "action": f"检查 {core_type} 提取器和关系链路",
                })
            elif pct > 10:
                warnings.append({
                    "level": "warning",
                    "msg": f"{core_type} 孤立率 {pct}%，部分实体未连接",
                })

        # 源文件检查
        for path in [LONG_TERM_KB, TERMINOLOGY_DB, TECHNIQUE_DB]:
            if not os.path.exists(path):
                warnings.append({
                    "level": "critical",
                    "msg": f"源文件丢失: {os.path.basename(path)}",
                    "action": "检查文件是否被移动或删除",
                })

        return warnings

    # ── 报告输出 ──────────────────────────────────────

    def print_report(self):
        """打印健康报告到终端"""
        report = self.check_all()
        status_icon = {"GREEN": "G", "YELLOW": "Y", "RED": "R"}

        print(f"[{status_icon.get(report['status'], '?')}] KG Health: {report['status']}")
        conn = report["connectivity"]
        print(f"  Nodes: {conn['total_nodes']} | Edges: {conn['total_edges']} | "
              f"Isolated: {conn['isolated_count']} ({conn['isolated_pct']}%)")

        if report["anomalies"]:
            print(f"  Anomalies: {len(report['anomalies'])}")
            for a in report["anomalies"]:
                print(f"    - [{a['type']}] {a['detail']}")

        if report["warnings"]:
            print(f"  Warnings: {len(report['warnings'])}")
            for w in report["warnings"]:
                print(f"    - [{w['level']}] {w['msg']}")

        growth = report.get("growth", {})
        if growth:
            delta = growth.get("node_change", 0)
            if delta:
                print(f"  Growth: {delta:+d} nodes since {growth.get('previous_date', 'N/A')[:10]}")

        return report
