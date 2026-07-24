"""GIS科学配色方案 — Color Universal Design + 学术期刊常用"""
import json

# ── 地形/DEM配色 ──
DEM_PALETTES = {
    "elevation_grayscale": {
        "name": "灰度高程",
        "colors": ["#FFFFFF", "#E0E0E0", "#B0B0B0", "#808080", "#505050", "#202020"],
        "use": "论文发表首选，黑白打印友好",
    },
    "elevation_earth": {
        "name": "地球色调",
        "colors": ["#1B5E20", "#4CAF50", "#FFEB3B", "#FF9800", "#BF360C", "#FFFFFF"],
        "use": "PPT/海报，视觉冲击力强",
    },
    "slope_classic": {
        "name": "坡度分级(CUD)",
        "colors": ["#F7F7F7", "#D1E5F0", "#92C5DE", "#4393C3", "#2166AC", "#053061"],
        "use": "色盲友好，发表安全",
    },
}

# ── 土壤侵蚀配色 ──
EROSION_PALETTES = {
    "severity_5class": {
        "name": "侵蚀强度5级",
        "colors": ["#1A9641", "#A6D96A", "#FFFFBF", "#FDAE61", "#D7191C"],
        "use": "微度-轻度-中度-强烈-剧烈，红绿对比清晰",
    },
    "risk_binary": {
        "name": "侵蚀风险",
        "colors": ["#4575B4", "#D73027"],
        "use": "安全/危险二分",
    },
}

# ── 土地利用/覆盖配色 ──
LANDCOVER_PALETTES = {
    "esa_worldcover": {
        "name": "ESA WorldCover 10类",
        "colors": ["#006400","#FFBB22","#FFFF4C","#F096FF","#FA0000",
                   "#B4B4B4","#F0F0F0","#0064C8","#0096A0","#F5DCC0"],
        "labels": ["林地","灌丛","草地","农田","建成区","裸地","冰雪","水域","湿地","红树林"],
    },
}

# ── 统计图配色(CUD安全) ──
CHART_PALETTES = {
    "cud_6class": {
        "name": "6类色盲安全",
        "colors": ["#0072B2", "#D55E00", "#009E73", "#F0E442", "#CC79A7", "#56B4E9"],
        "use": "散点/折线/柱状图通用",
    },
    "categorical_8": {
        "name": "8类自然科学",
        "colors": ["#332288","#117733","#44AA99","#88CCEE","#DDCC77","#CC6677","#AA4499","#882255"],
        "use": "Nature/Science期刊常用配色",
    },
}

ALL = {**DEM_PALETTES, **EROSION_PALETTES, **LANDCOVER_PALETTES, **CHART_PALETTES}

def get_palette(name: str) -> dict:
    return ALL.get(name, {"error": f"未找到配色 {name}，可用: {list(ALL.keys())}"})

def list_palettes():
    for k, v in ALL.items():
        print(f"  {k:25s} — {v['name']} ({v['use']})")

# 导出为matplotlib可直接用的格式
def to_matplotlib(name: str):
    """返回matplotlib ListedColormap"""
    p = get_palette(name)
    if "error" in p:
        return None
    from matplotlib.colors import ListedColormap
    return ListedColormap(p["colors"])

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--list", action="store_true")
    p.add_argument("--name", help="获取指定配色")
    p.add_argument("--json", action="store_true", help="JSON输出")
    args = p.parse_args()
    if args.list:
        list_palettes()
    elif args.name:
        result = get_palette(args.name)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result)
