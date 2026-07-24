"""
文献综述流水线 — 基于 ScholarFlow 8节点设计 + 本地KG查询
============================================================
节点: 查询分解→多源并行检索→KG存量比对→引文扩展→质量排序→结构化综述→引文图谱→成本追踪
"""
import json, sys, os, re, hashlib
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ═══ Node 1: 查询分解 ═══
def decompose_query(topic: str) -> List[str]:
    """将研究主题分解为多个子查询，覆盖不同角度"""
    sub_queries = [topic]
    # 方法角度
    if any(k in topic for k in ['侵蚀', 'erosion', '滑坡', 'landslide']):
        sub_queries.extend([
            f"{topic} machine learning",
            f"{topic} remote sensing",
            f"{topic} GIS spatial analysis",
        ])
    # 区域角度
    if any(k in topic for k in ['黄土', '紫色土', '西南', 'loess']):
        sub_queries.append(f"{topic} 中国")
    return list(set(sub_queries))


# ═══ Node 2: 多源并行检索 ═══
def multi_source_search(queries: List[str], max_per_query: int = 10) -> List[Dict]:
    """并行检索多个数据源，去重合并"""
    from daily_paper_curator import search_semantic_scholar, search_arxiv
    all_papers = []
    seen = set()

    for q in queries:
        # Semantic Scholar
        try:
            s2_results = search_semantic_scholar(q, max_per_query)
            for p in s2_results:
                key = p.get("paper_id", "")
                if key and key not in seen:
                    seen.add(key)
                    p["search_source"] = "Semantic Scholar"
                    all_papers.append(p)
        except Exception:
            pass

        # arXiv
        try:
            arxiv_results = search_arxiv(q, max_per_query)
            for p in arxiv_results:
                key = p.get("paper_id", "")
                if key and key not in seen:
                    seen.add(key)
                    p["search_source"] = "arXiv"
                    all_papers.append(p)
        except Exception:
            pass

    return all_papers


# ═══ Node 3: KG存量比对 ═══
def check_kg_coverage(papers: List[Dict]) -> Dict:
    """检查知识图谱中已有覆盖，标记新/旧论文"""
    kg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "knowledge_graph", "kg_data.json")

    existing_titles = set()
    try:
        with open(kg_path, "r", encoding="utf-8") as f:
            kg = json.load(f)
        for node in kg.get("nodes", []):
            if node.get("entity_type") == "Paper":
                title = (node.get("title", "")).lower().strip()
                existing_titles.add(title)
    except Exception:
        pass

    new_count = 0
    for p in papers:
        p_title = (p.get("title", "")).lower().strip()
        p["in_kg"] = p_title in existing_titles
        if not p["in_kg"]:
            new_count += 1

    return {"total": len(papers), "in_kg": len(papers) - new_count, "new": new_count}


# ═══ Node 4: 引文扩展 ═══
def citation_expansion(papers: List[Dict], max_citations: int = 20) -> List[Dict]:
    """追踪高引论文的引用链，扩展文献覆盖"""
    expanded = list(papers)
    seen_ids = {p.get("paper_id", "") for p in papers}

    for p in papers[:5]:  # 只扩展top5论文的引用
        paper_id = p.get("paper_id", "")
        if not paper_id:
            continue
        # Semantic Scholar citations API
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations?limit=10"
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "LitReview/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("data", [])[:5]:
                cp = item.get("citingPaper", {})
                cid = cp.get("paperId", "")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    expanded.append({
                        "paper_id": cid,
                        "title": cp.get("title", "Unknown"),
                        "source": "Citation expansion",
                        "is_citation": True,
                    })
        except Exception:
            pass
        if len(expanded) >= len(papers) + max_citations:
            break

    return expanded


# ═══ Node 5: 质量排序 ═══
def quality_ranking(papers: List[Dict]) -> List[Dict]:
    """三维排序：相关性+时效性+引用数"""
    for p in papers:
        citations = p.get("citations", 0) or 0
        year = int(p.get("year", 2020) or 2020)
        recency = max(0, 1 - (2026 - year) * 0.1)
        p["_rank_score"] = (
            0.4 * (1 if not p.get("is_citation") else 0.6) +  # 直接检索 > 引文扩展
            0.3 * recency +
            0.3 * min(1.0, citations / 50)
        )
    papers.sort(key=lambda x: x.get("_rank_score", 0), reverse=True)
    return papers


# ═══ Node 6: 结构化综述 ═══
def generate_review_outline(papers: List[Dict], topic: str) -> str:
    """生成文献综述大纲 — 按主题聚类"""
    # 简单 TF-IDF 聚类（基于标题关键词）
    clusters = {"方法": [], "数据": [], "应用": [], "综述": [], "其他": []}
    method_kw = ["method", "approach", "algorithm", "model", "framework", "pipeline"]
    data_kw = ["dataset", "satellite", "imagery", "dem", "survey", "monitoring"]
    review_kw = ["review", "survey", "state-of-the-art", "systematic", "comprehensive"]

    for p in papers:
        title = p.get("title", "").lower()
        if any(k in title for k in review_kw):
            clusters["综述"].append(p)
        elif any(k in title for k in method_kw):
            clusters["方法"].append(p)
        elif any(k in title for k in data_kw):
            clusters["数据"].append(p)
        elif len(title) > 20:
            clusters["应用"].append(p)
        else:
            clusters["其他"].append(p)

    lines = [f"# 文献综述大纲: {topic}", f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for cluster, paps in clusters.items():
        if not paps:
            continue
        lines.append(f"## {cluster} ({len(paps)}篇)")
        for p in paps[:5]:
            lines.append(f"- {p.get('title', 'Unknown')} ({p.get('year', '?')})")
        lines.append("")
    return "\n".join(lines)


# ═══ Node 7: 引文图谱 ═══
def export_citation_graph(papers: List[Dict], output_path: str) -> str:
    """导出引文关系为Mermaid图"""
    lines = ["```mermaid", "graph TD"]
    for i, p in enumerate(papers[:30]):
        pid = f"P{i}"
        title = p.get("title", "Unknown")[:40].replace('"', "'")
        lines.append(f"    {pid}[{title}]")
        if i > 0 and i % 5 == 0:
            lines.append(f"    {pid} --> P{i-1}")
    lines.append("```")

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    return "\n".join(lines)


# ═══ Node 8: 成本追踪 ═══
class CostTracker:
    def __init__(self):
        self.api_calls = {"Semantic Scholar": 0, "arXiv": 0, "Citations": 0}
        self.estimated_cost = 0.0

    def record_call(self, source: str):
        self.api_calls[source] = self.api_calls.get(source, 0) + 1

    def report(self) -> str:
        lines = ["## 成本追踪", f"API调用: {sum(self.api_calls.values())}次"]
        for src, count in self.api_calls.items():
            lines.append(f"  {src}: {count}次")
        lines.append(f"  估算费用: ${self.estimated_cost:.2f}")
        return "\n".join(lines)


# ═══ 主流水线 ═══
def run_literature_review(topic: str, max_papers: int = 30, output_dir: Optional[str] = None):
    """运行完整的8节点文献综述流水线"""
    tracker = CostTracker()

    print(f"[1/8] 查询分解: {topic}")
    queries = decompose_query(topic)
    print(f"  子查询: {len(queries)}个")

    print(f"[2/8] 多源检索...")
    papers = multi_source_search(queries, max_papers // len(queries))
    tracker.record_call("Semantic Scholar")
    tracker.record_call("arXiv")
    print(f"  检索到: {len(papers)}篇")

    print(f"[3/8] KG存量比对...")
    coverage = check_kg_coverage(papers)
    print(f"  已入库: {coverage['in_kg']}, 新增: {coverage['new']}")

    print(f"[4/8] 引文扩展...")
    papers = citation_expansion(papers)
    print(f"  扩展后: {len(papers)}篇")

    print(f"[5/8] 质量排序...")
    papers = quality_ranking(papers)
    print(f"  Top5: {[p.get('title','')[:50] for p in papers[:5]]}")

    print(f"[6/8] 结构化综述...")
    outline = generate_review_outline(papers, topic)
    print(f"  聚类: 完成")

    print(f"[7/8] 引文图谱...")
    graph_path = os.path.join(output_dir, "citation_graph.md") if output_dir else None
    export_citation_graph(papers, graph_path)

    print(f"[8/8] 成本追踪...")
    print(tracker.report())

    return {
        "papers": papers,
        "coverage": coverage,
        "outline": outline,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="8节点文献综述流水线")
    parser.add_argument("topic", help="研究主题")
    parser.add_argument("--max", type=int, default=30, help="最大论文数")
    parser.add_argument("--out", type=str, default=None, help="输出目录")
    args = parser.parse_args()
    run_literature_review(args.topic, args.max, args.out)
