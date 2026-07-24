#!/usr/bin/env python3
"""外文论文批量检索与下载 — 通用版（基于 scholar-mcp-server，9 数据源 + Sci-Hub fallback）。

触发: 用户说"下载外网论文""找英文文献""搜外文论文""批量下载论文"时调用。
数据源: Semantic Scholar / OpenAlex / Crossref / arXiv / PubMed / CORE / Europe PMC / DOAJ / dblp
下载链: Unpaywall → Publisher OA → arXiv → Sci-Hub

用法:
  # 自定义关键词（空格分隔多个关键词组）
  python download_foreign_papers.py --keywords "gully erosion GIS" "soil erosion ML" --max 20 --out ~/Desktop/papers

  # 使用预设模板
  python download_foreign_papers.py --preset gully-erosion-gis --out ~/Desktop/papers

  # 运行所有预设模板（全量搜索）
  python download_foreign_papers.py --preset ALL --out ~/Desktop/papers

  # 只搜不下载
  python download_foreign_papers.py --keywords "landslide susceptibility" --search-only

  # 从 DOI 列表直接下载
  python download_foreign_papers.py --doi-file dois.txt --out ~/Desktop/papers

  # 断点续传（跳过已下载的）
  python download_foreign_papers.py --preset ALL --out ~/Desktop/papers --resume

  # 限制下载数量
  python download_foreign_papers.py --preset ALL --max-download 150

  # 自定义标题过滤器（只用默认过滤器时无需指定）
  python download_foreign_papers.py --keywords "climate change hydrology" --filter "climate,hydrology,precipitation,water"

  # 导出 CSV（用于导入 Zotero/EndNote）
  python download_foreign_papers.py --preset ALL --search-only --csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from scholar_mcp_server import search_papers, download_paper
except ImportError:
    print("ERROR: scholar-mcp-server 未安装。请执行: pip install scholar-mcp-server")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════
# 预设搜索模板
# ═══════════════════════════════════════════════════════════════════════

PRESET_SEARCHES: dict[str, list[tuple[str, int]]] = {
    "gully-erosion-gis": [
        ("gully erosion GIS spatial analysis susceptibility mapping remote sensing", 20),
        ("gully erosion machine learning random forest XGBoost susceptibility prediction", 20),
        ("gully erosion UAV drone LiDAR SfM photogrammetry monitoring", 15),
        ("gully erosion gully head retreat DEM terrain morphometric threshold", 15),
        ("gully erosion dryland semiarid arid badland review", 15),
    ],
    "dem-terrain": [
        ("digital elevation model DEM interpolation accuracy uncertainty spatial analysis", 20),
        ("DEM terrain analysis geomorphometry topographic index geomorphon", 20),
        ("UAV LiDAR SfM point cloud DEM generation gully erosion", 15),
    ],
    "erosion-modeling": [
        ("soil erosion RUSLE USPED model GIS remote sensing", 20),
        ("gully erosion susceptibility hazard risk mapping machine learning", 20),
        ("soil erosion sediment yield watershed modeling SWAT", 15),
    ],
    "spatial-analysis": [
        ("geographically weighted regression GWR MGWR spatial heterogeneity GIS", 15),
        ("Geodetector spatial autocorrelation Moran Getis-Ord factor detection", 15),
        ("spatial analysis GIS remote sensing land use landscape pattern", 15),
    ],
}

# 默认标题过滤关键词（用于确保搜索结果与GIS/遥感/空间分析相关）
DEFAULT_TITLE_FILTER = [
    "gully", "erosion", "soil", "sediment", "dem", "digital elevation",
    "terrain", "landslide", "badland", "rill", "water", "hydrolog",
    "geomorph", "spatial", "gis", "remote sensing", "uav", "lidar",
    "machine learning", "deep learning", "susceptibility", "hazard",
    "topographic", "slope", "watershed", "catchment", "runoff",
    "land use", "land cover", "ndvi", "vegetation", "morphometric",
    "gorge", "ravine", "gully erosion", "soil loss", "conservation",
    "sentinel", "landsat", "google earth engine", "gee",
    "random forest", "xgboost", "cnn", "neural network",
    "insar", "photogrammetry", "structure from motion",
    "flash flood", "debris flow", "weathering",
]


# ═══════════════════════════════════════════════════════════════════════
# 核心函数
# ═══════════════════════════════════════════════════════════════════════

def search_and_collect(
    keywords: list,
    max_per_query: int = 15,
    title_filter: Optional[list[str]] = None,
    sleep_between: float = 2.0,
) -> list[dict]:
    """跨多组关键词搜索，DOI 去重后返回论文列表。

    Parameters
    ----------
    keywords : list
        支持两种格式:
        - 纯字符串列表: ["query1", "query2"]  → 统一使用 max_per_query
        - 元组列表: [("query1", 20), ("query2", 15)]  → 各自指定 max
    max_per_query : int
        纯字符串模式下，每组关键词的最大搜索结果数（元组模式下被覆盖）
    title_filter : list[str] or None
        标题过滤关键词列表。None 时不启用标题过滤。
        论文标题（小写后）必须包含至少一个过滤词才会被收录。
    sleep_between : float
        搜索请求间隔（秒），避免触发 API 限速
    """
    all_papers: dict[str, dict] = {}
    total_queries = len(keywords)

    for idx, item in enumerate(keywords, 1):
        # 解包 (query, rows) 或纯字符串
        if isinstance(item, tuple):
            query, rows = item
        else:
            query, rows = item, max_per_query

        print(f"[搜索 {idx}/{total_queries}] {query[:70]}... (max {rows})", end=" ", flush=True)

        try:
            result = search_papers(query, rows=rows)
            hits = len(result.get("results", []))
            print(f"→ 返回 {hits} 篇")

            for paper in result.get("results", []):
                doi = paper.get("doi", "")
                if not doi or doi in all_papers:
                    continue

                # 标题过滤（可选）
                if title_filter is not None:
                    title = (paper.get("title", "") or "").lower()
                    if not any(kw.lower() in title for kw in title_filter):
                        continue

                all_papers[doi] = paper

        except Exception as e:
            print(f"→ 失败: {e}")

        if idx < total_queries:
            time.sleep(sleep_between)

    papers = sorted(all_papers.values(), key=lambda x: int(x.get("year", 0) or 0), reverse=True)
    return papers


def download_papers(
    papers: list[dict],
    output_dir: Path,
    max_downloads: int = 50,
    resume: bool = False,
    sleep_between: float = 2.0,
) -> tuple[int, int, int]:
    """下载论文 PDF。

    Parameters
    ----------
    papers : list[dict]
        论文列表（需含 doi 字段）
    output_dir : Path
        输出目录
    max_downloads : int
        最多下载成功篇数（达到后停止）
    resume : bool
        True 时跳过 output_dir 中已存在的 PDF（断点续传）
    sleep_between : float
        下载请求间隔（秒）

    Returns
    -------
    (ok, fail, skipped) — 成功数、失败数、跳过数
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ok, fail, skipped = 0, 0, 0
    total = min(len(papers), max_downloads) if max_downloads > 0 else len(papers)

    print(f"\n{'='*60}")
    print(f"开始下载: 目标 {total} 篇 → {output_dir}")
    if resume:
        print("断点续传模式: 跳过已存在的 PDF")
    print(f"{'='*60}\n")

    for i, paper in enumerate(papers):
        if max_downloads > 0 and ok >= max_downloads:
            break

        doi = paper.get("doi", "")
        title = (paper.get("title", "") or "")[:80]
        year = paper.get("year", "?")

        if not doi:
            skipped += 1
            continue

        # 断点续传: 跳过已存在的
        doi_fn = doi.replace("/", "_").replace(".", "_")
        if resume and list(output_dir.glob(f"*{doi_fn[:30]}*")):
            paper["downloaded"] = True
            skipped += 1
            continue

        try:
            result = download_paper(doi=doi, output_dir=str(output_dir))
            if result and result.get("success"):
                paper["downloaded"] = True
                paper["local_file"] = result.get("filename", "")
                ok += 1
                progress = f"[{ok}/{total}]" if max_downloads > 0 else f"[{ok}]"
                print(f"{progress} [{year}] {title[:70]}...")
            else:
                fail += 1

        except Exception as e:
            fail += 1
            if ok + fail <= 5:  # 只打印前几次错误，避免刷屏
                print(f"  [下载失败] {doi[:40]}...: {e}")

        if i < len(papers) - 1:
            time.sleep(sleep_between)

    return ok, fail, skipped


def export_csv(papers: list[dict], output_path: Path) -> None:
    """导出论文清单为 CSV（兼容 Zotero/EndNote 导入）。"""
    fields = ["title", "authors", "year", "doi", "journal", "source", "url", "downloaded"]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in papers:
            row = {
                "title": p.get("title", ""),
                "authors": ", ".join(p.get("authors", [])) if isinstance(p.get("authors"), list) else p.get("authors", ""),
                "year": p.get("year", ""),
                "doi": p.get("doi", ""),
                "journal": p.get("journal", ""),
                "source": p.get("source", ""),
                "url": p.get("url", ""),
                "downloaded": "Y" if p.get("downloaded") else "N",
            }
            writer.writerow(row)
    print(f"CSV 已导出: {output_path}")


def summarize_years(papers: list[dict]) -> None:
    """按年份统计论文分布。"""
    years: dict[str, int] = {}
    for p in papers:
        y = str(p.get("year", "?") or "?")
        years[y] = years.get(y, 0) + 1
    print("\n年份分布:")
    for y in sorted(years, reverse=True):
        bar = "█" * min(years[y], 50)
        print(f"  {y:>6}: {years[y]:>4} 篇  {bar}")


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="外文论文批量检索与下载 — scholar-mcp-server (9 数据源 + Sci-Hub fallback)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自定义关键词搜索+下载
  python download_foreign_papers.py --keywords "gully erosion GIS" "soil erosion ML" --out ~/Desktop/papers

  # 使用预设模板
  python download_foreign_papers.py --preset gully-erosion-gis

  # 运行所有预设模板
  python download_foreign_papers.py --preset ALL --max-download 150

  # 只搜索不下载
  python download_foreign_papers.py --keywords "landslide susceptibility" --search-only

  # 断点续传
  python download_foreign_papers.py --preset ALL --out ~/Desktop/papers --resume

  # 禁用标题过滤（收录所有搜索结果）
  python download_foreign_papers.py --keywords "machine learning" --no-filter
        """,
    )

    # ── 搜索选项 ──
    search_group = parser.add_argument_group("搜索")
    search_group.add_argument("--keywords", nargs="*", default=[], help="搜索关键词（可多组，空格分隔）")
    search_group.add_argument(
        "--preset", choices=list(PRESET_SEARCHES) + ["ALL"],
        help="预设搜索模板。ALL = 运行全部预设"
    )
    search_group.add_argument("--max", type=int, default=15, dest="max_per_query",
                               help="每组关键词最大结果数（默认 15）")
    search_group.add_argument("--no-filter", action="store_true",
                               help="禁用标题关键词过滤（收录所有搜索结果，不过滤不相关论文）")
    search_group.add_argument("--filter", type=str, default=None,
                               help="自定义标题过滤关键词（逗号分隔）。不指定则使用内置默认过滤器")
    search_group.add_argument("--sleep-search", type=float, default=2.0,
                               help="搜索请求间隔秒数（默认 2.0）")

    # ── DOI 导入 ──
    doi_group = parser.add_argument_group("DOI 导入")
    doi_group.add_argument("--doi-file", type=Path, help="DOI 列表文件（每行一个 DOI）")

    # ── 下载选项 ──
    dl_group = parser.add_argument_group("下载")
    dl_group.add_argument("--out", type=Path, default=Path.home() / "Desktop" / "foreign_papers",
                           help="输出目录（默认 ~/Desktop/foreign_papers）")
    dl_group.add_argument("--max-download", type=int, default=50,
                           help="最多下载成功篇数（默认 50）")
    dl_group.add_argument("--resume", action="store_true",
                           help="断点续传：跳过输出目录中已存在的 PDF")
    dl_group.add_argument("--sleep-download", type=float, default=2.0,
                           help="下载请求间隔秒数（默认 2.0）")

    # ── 模式选项 ──
    mode_group = parser.add_argument_group("模式")
    mode_group.add_argument("--search-only", action="store_true", help="只搜索不下载")
    mode_group.add_argument("--csv", action="store_true", help="额外导出 CSV（兼容 Zotero/EndNote）")
    mode_group.add_argument("--no-save-list", action="store_true", help="不保存 paper_list.json")

    args = parser.parse_args()

    # ── 解析标题过滤器 ──
    if args.no_filter:
        title_filter = None
        print("[过滤器] 已禁用（收录所有搜索结果）")
    elif args.filter:
        title_filter = [kw.strip() for kw in args.filter.split(",") if kw.strip()]
        print(f"[过滤器] 自定义: {title_filter}")
    else:
        title_filter = DEFAULT_TITLE_FILTER
        print(f"[过滤器] 默认（{len(title_filter)} 个关键词）")

    # ── 收集论文 ──
    papers: list[dict] = []

    # 1) DOI 文件导入
    if args.doi_file and args.doi_file.exists():
        dois = [line.strip() for line in args.doi_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"\n从 {args.doi_file} 读取 {len(dois)} 个 DOI")
        for doi in dois:
            papers.append({"doi": doi, "title": "DOI-direct", "year": ""})
        print()

    # 2) 预设模板
    keywords_list: list = []
    if args.preset:
        if args.preset == "ALL":
            for preset_name, queries in PRESET_SEARCHES.items():
                print(f"[预设] {preset_name}: {len(queries)} 组关键词")
                keywords_list.extend(queries)
            print(f"[预设] 总计 {len(keywords_list)} 组关键词\n")
        else:
            keywords_list = PRESET_SEARCHES[args.preset]
            print(f"[预设] {args.preset}: {len(keywords_list)} 组关键词\n")

    # 3) 命令行关键词
    if args.keywords:
        keywords_list.extend(args.keywords)

    # 4) 搜索
    if keywords_list and not args.doi_file:
        queries = keywords_list
        # 纯字符串列表 → 包装为 (query, max_per_query)
        if isinstance(queries[0], str):
            queries = [(q, args.max_per_query) for q in queries]
        print(f"开始搜索 {len(queries)} 组关键词...\n")
        papers = search_and_collect(
            queries,
            max_per_query=args.max_per_query,
            title_filter=title_filter,
            sleep_between=args.sleep_search,
        )

    # ── 保存清单 ──
    if papers and not args.no_save_list:
        args.out.mkdir(parents=True, exist_ok=True)
        list_path = args.out / "paper_list.json"
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"\n论文清单: {len(papers)} 篇 → {list_path}")

    # ── 摘要统计 ──
    if papers:
        summarize_years(papers)
    else:
        print("\n[无结果] 未搜索到论文。尝试: 放宽关键词、禁用过滤器 (--no-filter)、或增大 --max")

    # ── CSV 导出 ──
    if args.csv and papers:
        csv_path = args.out / "paper_list.csv"
        export_csv(papers, csv_path)

    # ── 仅搜索模式 ──
    if args.search_only:
        print("\n[search-only 模式，不下载]")
        return 0

    if not papers:
        return 0

    # ── 下载 ──
    ok, fail, skipped = download_papers(
        papers, args.out,
        max_downloads=args.max_download,
        resume=args.resume,
        sleep_between=args.sleep_download,
    )

    # ── 更新清单 ──
    if not args.no_save_list:
        list_path = args.out / "paper_list.json"
        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)

        if args.csv:
            csv_path = args.out / "paper_list.csv"
            export_csv(papers, csv_path)

    # ── 未下载 DOI ──
    missing = [p for p in papers if not p.get("downloaded") and p.get("doi")]
    if missing:
        doi_path = args.out / "doi_to_download.txt"
        with open(doi_path, "w", encoding="utf-8") as f:
            for p in missing:
                f.write(f'{p["doi"]}\n')
        print(f"\n{len(missing)} 篇未下载 (DOI → {doi_path})")

    # ── 最终统计 ──
    print(f"\n{'='*60}")
    print(f"完成: {ok} 下载成功 | {fail} 失败 | {skipped} 跳过 | {len(missing)} 待手动")
    print(f"输出目录: {args.out.resolve()}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
