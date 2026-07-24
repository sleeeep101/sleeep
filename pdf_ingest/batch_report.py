"""PDF批量提取统计仪表板"""
import json, os, sys, glob
from collections import Counter
from datetime import datetime

def batch_stats(pdf_dir: str, output_dir: str = None) -> dict:
    """扫描output目录，汇总所有已处理PDF的质量统计"""
    if not output_dir:
        output_dir = os.path.join(pdf_dir, "..", "output") if os.path.exists(os.path.join(pdf_dir, "..", "output")) else pdf_dir

    metadata_files = glob.glob(os.path.join(output_dir, "**", "metadata.json"), recursive=True)
    if not metadata_files:
        metadata_files = glob.glob(os.path.join(pdf_dir, "**", "metadata.json"), recursive=True)

    stats = {
        "report_time": datetime.now().isoformat(),
        "total_processed": len(metadata_files),
        "by_engine": Counter(),
        "by_level": Counter(),
        "by_confidence": Counter(),
        "quality_scores": [],
        "issues": [],
    }

    for mf in metadata_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            stats["issues"].append({"file": mf, "error": "metadata不可读"})
            continue

        engine = meta.get("engine_used", meta.get("engine", "unknown"))
        level = meta.get("reading_level", "UNKNOWN")
        confidence = meta.get("confidence", "unknown")
        quality = meta.get("quality_score")

        stats["by_engine"][engine] += 1
        stats["by_level"][level] += 1
        stats["by_confidence"][confidence] += 1
        if quality is not None:
            stats["quality_scores"].append(quality)

        if quality is not None and quality < 0.3:
            stats["issues"].append({
                "file": os.path.basename(mf),
                "engine": engine,
                "quality": quality,
                "suggestion": "需升级引擎或人工处理",
            })

    if stats["quality_scores"]:
        scores = stats["quality_scores"]
        stats["quality_avg"] = round(sum(scores) / len(scores), 3)
        stats["quality_min"] = round(min(scores), 3)
        stats["quality_max"] = round(max(scores), 3)

    return stats


def print_report(stats: dict):
    """终端友好输出"""
    print(f"=== PDF提取批量统计 ===")
    print(f"时间: {stats['report_time']}")
    print(f"总计: {stats['total_processed']} 篇")
    print(f"\n引擎分布: {dict(stats['by_engine'])}")
    print(f"等级分布: {dict(stats['by_level'])}")
    print(f"置信度: {dict(stats['by_confidence'])}")
    if stats.get("quality_avg"):
        print(f"质量评分: avg={stats['quality_avg']}, min={stats['quality_min']}, max={stats['quality_max']}")
    if stats["issues"]:
        print(f"\n⚠ 需关注 ({len(stats['issues'])}):")
        for iss in stats["issues"][:5]:
            print(f"  {iss['file']}: {iss.get('suggestion', iss.get('error', ''))}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("dir", help="PDF或output目录")
    p.add_argument("--output-dir", help="output目录(如不同于PDF目录)")
    args = p.parse_args()
    stats = batch_stats(args.dir, args.output_dir)
    print_report(stats)
