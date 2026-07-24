"""配置文件有效性验证 — 启动/部署时自动运行"""
import json, os, sys
from typing import List, Tuple

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

REQUIRED_FILES = ["paths.json", "paper_grading_config.json"]
REQUIRED_PATHS = ["academic_root", "kg_data"]
REQUIRED_RUBRIC = ["direction_relevance", "method_rigor", "innovation",
                   "evidence_sufficiency", "argument_coherence", "writing_quality", "transferability"]

def validate_all() -> List[Tuple[str, bool, str]]:
    """验证所有配置文件，返回 (文件名, 是否通过, 信息) 列表"""
    results = []

    # 1. 检查必要文件存在
    for fname in REQUIRED_FILES:
        fpath = os.path.join(CONFIG_DIR, fname)
        if not os.path.exists(fpath):
            results.append((fname, False, f"文件缺失: {fpath}"))
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                json.load(f)
            results.append((fname, True, "OK"))
        except json.JSONDecodeError as e:
            results.append((fname, False, f"JSON解析错误: {e}"))
        except Exception as e:
            results.append((fname, False, str(e)))

    # 2. 验证paths.json关键路径存在
    paths_file = os.path.join(CONFIG_DIR, "paths.json")
    if os.path.exists(paths_file):
        try:
            with open(paths_file, "r", encoding="utf-8") as f:
                paths = json.load(f)
            for key in REQUIRED_PATHS:
                val = paths.get(key, "")
                if not val:
                    results.append((f"paths.json.{key}", False, "路径未配置"))
                elif key == "kg_data" and not os.path.exists(val):
                    results.append((f"paths.json.{key}", False, f"文件不存在: {val}"))
        except Exception as e:
            results.append(("paths.json", False, str(e)))

    # 3. 验证评分配置7维度完整
    grading_file = os.path.join(CONFIG_DIR, "paper_grading_config.json")
    if os.path.exists(grading_file):
        try:
            with open(grading_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            rubric = cfg.get("unified_rubric", {})
            for dim in REQUIRED_RUBRIC:
                if dim not in rubric:
                    results.append((f"grading.{dim}", False, "评分维度缺失"))
            weights = [v.get("weight", 0) for v in rubric.values()]
            if abs(sum(weights) - 1.0) > 0.01:
                results.append(("grading.weights", False, f"权重和不等于1: {sum(weights)}"))
        except Exception as e:
            results.append(("paper_grading_config.json", False, str(e)))

    return results


if __name__ == "__main__":
    results = validate_all()
    failed = [r for r in results if not r[1]]
    print(f"配置验证: {len(results)-len(failed)}/{len(results)} 通过")
    if failed:
        print(f"失败 {len(failed)}:")
        for fname, ok, msg in failed:
            print(f"  [{fname}] {msg}")
    else:
        print("全部通过")
    sys.exit(1 if failed else 0)
