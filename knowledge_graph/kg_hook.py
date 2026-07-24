"""
知识图谱集成 Hook
=================
供 daily_paper_curator.py 等现有脚本调用，实现"非孤儿"集成。

用法:
  # 在现有脚本末尾加一行:
  from knowledge_graph.kg_hook import update_kg_if_changed
  update_kg_if_changed()

  # 或者在 daily_paper_curator.py 中:
  parser.add_argument("--kg-update", action="store_true", help="更新知识图谱")
  if args.kg_update:
      from knowledge_graph.kg_hook import rebuild_and_export
      rebuild_and_export()
"""

import os
import sys

# 确保 academic-workflow 在 path 中
_ACADEMIC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ACADEMIC_ROOT not in sys.path:
    sys.path.insert(0, _ACADEMIC_ROOT)


def update_kg_if_changed() -> bool:
    """增量更新知识图谱（如果源文件有变动）"""
    from knowledge_graph.graph.updater import IncrementalUpdater
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder

    updater = IncrementalUpdater()
    if updater.needs_rebuild():
        print("[KG Hook] 检测到文件变更，自动更新知识图谱...")
        try:
            builder = KnowledgeGraphBuilder()
            builder.build_full()
            builder.save()
            updater.save_state()
            stats = builder.stats()
            print(f"[KG Hook] 图谱已更新: {stats['nodes']} 节点, {stats['edges']} 边")
            return True
        except Exception as e:
            print(f"[KG Hook] 更新失败: {e}")
            return False
    else:
        print("[KG Hook] 无文件变更，跳过更新")
        return False


def rebuild_and_export() -> bool:
    """全量重建知识图谱"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder

    print("[KG Hook] 全量重建知识图谱...")
    try:
        builder = KnowledgeGraphBuilder()
        builder.build_full()
        builder.save()

        stats = builder.stats()
        print(f"[KG Hook] 图谱已构建: {stats['nodes']} 节点, {stats['edges']} 边")
        return True
    except Exception as e:
        print(f"[KG Hook] 构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def quick_stats():
    """快速查看图谱状态（轻量级，不重建）"""
    from knowledge_graph.graph.builder import KnowledgeGraphBuilder

    builder = KnowledgeGraphBuilder.load()
    stats = builder.stats()
    print(f"[KG] {stats['nodes']} 节点, {stats['edges']} 边, "
          f"孤立率 {stats.get('isolated_ratio', 0):.1%}")
    return stats


# ── 命令行直接调用 ───────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="知识图谱集成 Hook")
    parser.add_argument("--update", action="store_true", help="增量更新")
    parser.add_argument("--rebuild", action="store_true", help="全量重建")
    parser.add_argument("--stats", action="store_true", help="查看统计")
    args = parser.parse_args()

    if args.stats:
        quick_stats()
    elif args.rebuild:
        rebuild_and_export()
    elif args.update:
        update_kg_if_changed()
    else:
        # 默认：增量更新
        update_kg_if_changed()
