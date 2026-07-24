"""
知识图谱 CLI
===========
用法:
  python -m knowledge_graph build          # 全量建图
  python -m knowledge_graph stats           # 图统计
  python -m knowledge_graph query <kw>      # 关键词搜索
  python -m knowledge_graph show <id>       # 查看节点详情和邻居
  python -m knowledge_graph path <a> <b>    # 最短路径
  python -m knowledge_graph recommend <id>  # 推荐关联
  python -m knowledge_graph viz             # 输出 pyvis HTML
  python -m knowledge_graph update          # 增量更新（Phase 4）
"""

import argparse
import sys
import os

# 确保 academic-workflow 在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def cmd_build(args):
    """全量构建知识图谱"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.graph.updater import IncrementalUpdater

    updater = IncrementalUpdater()
    if updater.needs_rebuild():
        print("[KG] 检测到文件变更，开始重建...")
        builder = KnowledgeGraphBuilder(include_private_sources=args.include_private_sources)
        builder.build_full()
        builder.save()
        updater.save_state()
    else:
        print("[KG] 无文件变更，跳过重建（使用缓存）")
        builder = KnowledgeGraphBuilder.load()

    stats = builder.stats()
    print(f"\n图谱统计:")
    print(f"  节点: {stats['nodes']}")
    print(f"  边: {stats['edges']}")
    for etype, count in stats.get("entity_type_counts", {}).items():
        print(f"    {etype}: {count}")
    print(f"  连通分量: {stats.get('connected_components', '?')}")
    print(f"  孤立节点: {stats.get('isolated_nodes', '?')} "
          f"({stats.get('isolated_ratio', 0):.1%})")


def cmd_stats(args):
    """查看图谱统计"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.query.search import KnowledgeGraphQuery

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    query = KnowledgeGraphQuery(builder)
    stats = query.stats()

    print(f"\n===== 知识图谱统计 =====")
    print(f"节点总数: {stats['nodes']}")
    print(f"边总数:   {stats['edges']}")
    print(f"\n实体类型分布:")
    for etype, count in sorted(stats.get("entity_type_counts", {}).items(),
                                key=lambda x: x[1], reverse=True):
        print(f"  {etype:20s} {count:5d}")
    print(f"\n关系类型分布:")
    for rtype, count in sorted(stats.get("edge_type_counts", {}).items(),
                                key=lambda x: x[1], reverse=True):
        print(f"  {rtype:25s} {count:5d}")
    print(f"\n连通分量: {stats.get('connected_components', '?')}")
    print(f"最大连通分量: {stats.get('largest_component_size', '?')} 节点")
    print(f"孤立节点: {stats.get('isolated_nodes', '?')} "
          f"({stats.get('isolated_ratio', 0):.1%})")

    if stats.get("top_nodes"):
        print(f"\nTop 10 核心节点 (按连接度):")
        for i, n in enumerate(stats["top_nodes"], 1):
            print(f"  {i}. [{n['type']}] {n['label'][:80]} (度={n['degree']})")


def cmd_query(args):
    """关键词搜索"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.query.search import KnowledgeGraphQuery

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    query = KnowledgeGraphQuery(builder)
    results = query.search(args.keyword)

    if not results:
        print(f"未找到匹配 '{args.keyword}' 的结果")
        return

    print(f"\n===== 搜索: '{args.keyword}' — {len(results)} 条结果 =====\n")
    for i, r in enumerate(results[:args.limit], 1):
        print(f"{i}. [{r['type']}] {r['label'][:100]}")
        print(f"   ID: {r['id']}  |  连接度: {r['degree']}")
        # 显示关键属性
        for k, v in r.get("attrs", {}).items():
            if isinstance(v, str) and 3 < len(v) < 150:
                print(f"   {k}: {v[:120]}")
            elif isinstance(v, list) and v:
                print(f"   {k}: {', '.join(str(x) for x in v[:5])}")
        print()


def cmd_show(args):
    """查看节点详情"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.query.search import KnowledgeGraphQuery

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    query = KnowledgeGraphQuery(builder)

    result = query.neighbors(args.node_id, depth=args.depth)
    if "error" in result:
        print(f"错误: {result['error']}")
        return

    node = result["node"]
    print(f"\n===== {node['type']}: {node['label'][:100]} =====")
    print(f"ID: {node['id']}")

    # 显示邻居
    for depth_key in sorted(result.get("neighbors", {}).keys()):
        neighbors = result["neighbors"][depth_key]
        if not neighbors:
            continue
        print(f"\n── {depth_key.replace('_', ' ')} ({len(neighbors)} 个) ──")
        for n in neighbors[:20]:
            rel = n.get("relation", "")
            conf = n.get("confidence", 1.0)
            conf_str = f" (置信度:{conf:.0%})" if conf < 1.0 else ""
            print(f"  [{n['type']}] {n['label'][:80]}")
            if rel:
                print(f"       -> {rel}{conf_str}")


def cmd_path(args):
    """查找路径"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.query.search import KnowledgeGraphQuery

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    query = KnowledgeGraphQuery(builder)

    path = query.find_path(args.from_id, args.to_id)
    if not path:
        print(f"未找到从 '{args.from_id}' 到 '{args.to_id}' 的路径")
        return

    print(f"\n===== 路径 ({len(path)-1} 步) =====\n")
    for i, step in enumerate(path):
        prefix = "  " * i
        rel = step.get("relation", "")
        arrow = f" → ({rel}) → " if rel else " → "
        if i > 0:
            print(f"{prefix}{arrow}[{step['type']}] {step['label'][:80]}")
        else:
            print(f"{prefix}[{step['type']}] {step['label'][:80]}")


def cmd_recommend(args):
    """推荐"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.query.search import KnowledgeGraphQuery

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    query = KnowledgeGraphQuery(builder)

    results = query.recommend(args.node_id, top_k=args.top_k)
    if not results:
        print(f"未找到与 '{args.node_id}' 相关的推荐")
        return

    print(f"\n===== 推荐 ({len(results)} 条) =====\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['type']}] {r['label'][:100]} (关联度={r['score']})")


def cmd_viz(args):
    """生成可视化 HTML"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    if builder.graph.number_of_nodes() == 0:
        print("图谱为空，请先运行 build")
        return

    try:
        from knowledge_graph.viz.pyvis_render import render_pyvis
        output = args.output or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "knowledge_graph", "graph.html"
        )
        render_pyvis(builder.graph, output)
        print(f"可视化已保存到: {output}")
    except ImportError:
        print("需要安装 pyvis: pip install pyvis")


def cmd_mermaid(args):
    """导出 Mermaid"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.viz.mermaid_export import to_mermaid

    builder = KnowledgeGraphBuilder.load(args.graph_file)
    result = to_mermaid(builder.graph, max_nodes=args.max_nodes)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Mermaid 已保存到: {args.output}")
    else:
        print(result)


def cmd_canvas(args):
    """导出 Canvas JSON"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.viz.mermaid_export import to_canvas_json

    builder = KnowledgeGraphBuilder.load()
    output = args.output or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "knowledge_graph", "kg_canvas.json"
    )
    path = to_canvas_json(builder.graph, output, max_nodes=args.max_nodes)
    print(f"Canvas 已保存到: {path}")


def cmd_update(args):
    """增量更新"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.graph.updater import IncrementalUpdater

    updater = IncrementalUpdater()
    if updater.needs_rebuild():
        print("[KG] 检测到变更，增量更新...")
        builder = KnowledgeGraphBuilder(include_private_sources=args.include_private_sources)
        builder.build_full()
        builder.save()
        updater.save_state()
        print("[KG] 更新完成")
    else:
        print("[KG] 无变更")


def cmd_health(args):
    """健康检查"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.kg_health import HealthMonitor

    builder = KnowledgeGraphBuilder.load()
    monitor = HealthMonitor(builder.graph, builder.entities)
    monitor.print_report()


def cmd_ask(args):
    """自然语言查询 — 基于 KG 搜索"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder
    from knowledge_graph.query.search import KnowledgeGraphQuery

    question = " ".join(args.question)
    builder = KnowledgeGraphBuilder.load(args.graph_file)
    q = KnowledgeGraphQuery(builder)
    results = q.search(question)[:15]
    if not results:
        print("未找到匹配内容")
        return
    for i, r in enumerate(results, 1):
        etype = r["type"]
        label = r["label"][:100]
        detail = ""
        for k in ["english", "chinese", "summary", "explanation", "canonical_name"]:
            v = r.get("attrs", {}).get(k, "")
            if v:
                detail = f" — {str(v)[:100]}"
                break
        print(f"{i}. [{etype}] {label}{detail}")


def main():
    parser = argparse.ArgumentParser(
        description="科研知识图谱 — 学术工作流知识连接工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m knowledge_graph build
  python -m knowledge_graph stats
  python -m knowledge_graph stats --graph-file knowledge_graph/examples/public_graph.json
  python -m knowledge_graph query "gully erosion" --graph-file knowledge_graph/examples/public_graph.json
  python -m knowledge_graph show KB-2026-07-21-01
  python -m knowledge_graph path "RUSLE" "写作技法库"
  python -m knowledge_graph recommend KB-2026-07-21-01
  python -m knowledge_graph viz --output graph.html
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # build
    p_build = subparsers.add_parser("build", help="全量构建知识图谱")
    p_build.add_argument(
        "--include-private-sources",
        action="store_true",
        help="Explicitly include Personal-Brain, Desktop notes, and contact files.",
    )

    # stats
    p_stats = subparsers.add_parser("stats", help="查看图谱统计")

    # query
    p_query = subparsers.add_parser("query", help="关键词搜索")
    p_query.add_argument("keyword", help="搜索关键词")
    p_query.add_argument("--limit", "-n", type=int, default=20, help="结果数量限制")

    # show
    p_show = subparsers.add_parser("show", help="查看节点详情和邻居")
    p_show.add_argument("node_id", help="节点 ID")
    p_show.add_argument("--depth", "-d", type=int, default=1, help="邻居深度")

    # path
    p_path = subparsers.add_parser("path", help="查找两节点间最短路径")
    p_path.add_argument("from_id", help="起始节点")
    p_path.add_argument("to_id", help="目标节点")

    # recommend
    p_rec = subparsers.add_parser("recommend", help="推荐关联实体")
    p_rec.add_argument("node_id", help="节点 ID")
    p_rec.add_argument("--top-k", "-k", type=int, default=10, help="推荐数量")

    # viz
    p_viz = subparsers.add_parser("viz", help="生成 pyvis 可视化 HTML")
    p_viz.add_argument("--output", "-o", help="输出文件路径")

    # mermaid
    p_mermaid = subparsers.add_parser("mermaid", help="导出 Mermaid flowchart")
    p_mermaid.add_argument("--output", "-o", help="输出文件路径")
    p_mermaid.add_argument("--max-nodes", "-n", type=int, default=80, help="最大节点数")

    # update
    p_update = subparsers.add_parser("update", help="增量更新")
    p_update.add_argument(
        "--include-private-sources",
        action="store_true",
        help="Explicitly include Personal-Brain, Desktop notes, and contact files.",
    )

    # health
    subparsers.add_parser("health", help="运行健康检查")

    # ask
    p_ask = subparsers.add_parser("ask", help="自然语言查询（基于KG搜索，零LLM）")
    p_ask.add_argument("question", nargs="+", help="问题")

    # 读取命令可显式指定经过审核的公开图谱，避免要求下载者先构建本地知识库。
    read_parsers = [p_stats, p_query, p_show, p_path, p_rec, p_viz, p_mermaid, p_ask]
    for read_parser in read_parsers:
        read_parser.add_argument(
            "--graph-file",
            help="要读取的图谱 JSON；省略时使用本机生成的默认图谱。",
        )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "build": cmd_build,
        "stats": cmd_stats,
        "query": cmd_query,
        "show": cmd_show,
        "path": cmd_path,
        "recommend": cmd_recommend,
        "viz": cmd_viz,
        "mermaid": cmd_mermaid,
        "health": cmd_health,
        "ask": cmd_ask,
        "update": cmd_update,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
