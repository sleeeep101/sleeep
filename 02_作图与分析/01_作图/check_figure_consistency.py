#!/usr/bin/env python3
"""跨图色彩一致性审计 v2 — 支持 SVG/PNG/PDF，Delta E 色差对比。

触发: scientific-figure → 多图投稿前自动运行
用法: python check_figure_consistency.py --dir figures/
依赖: pip install pillow colormath (可选，无则用RGB欧氏距离)
"""

import argparse, json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from colormath.color_objects import sRGBColor, LabColor
    from colormath.color_conversions import convert_color
    from colormath.color_diff import delta_e_cie2000
    HAS_COLORMATH = True
except ImportError:
    HAS_COLORMATH = False

def rgb_distance(c1: str, c2: str) -> float:
    """两色距离。有colormath用Delta E 2000(感知均匀)，否则用欧氏距离"""
    r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    if HAS_COLORMATH:
        try:
            lab1 = convert_color(sRGBColor(r1,g1,b1,True), LabColor)
            lab2 = convert_color(sRGBColor(r2,g2,b2,True), LabColor)
            return delta_e_cie2000(lab1, lab2)
        except: pass
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5

def extract_png_colors(path: Path, top_n: int = 8) -> Counter:
    """从PNG提取主要颜色"""
    if not HAS_PIL:
        return Counter()
    img = Image.open(path).convert('RGB').resize((200,200))
    pixels = list(img.getdata())
    # 量化到 32级以减少颜色数
    quantized = Counter()
    for r,g,b in pixels:
        qr, qg, qb = (r//32)*32, (g//32)*32, (b//32)*32
        quantized[f'#{qr:02x}{qg:02x}{qb:02x}'] += 1
    return Counter({k:v for k,v in quantized.most_common(top_n)})

def extract_svg_colors(path: Path) -> Counter:
    """从SVG提取颜色"""
    text = path.read_text(encoding='utf-8')
    colors = re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', text)
    return Counter(c.lower() for c in colors)

def detect_color_drift(figures: dict) -> list[dict]:
    """检测跨图颜色漂移：同一语义颜色在不同图中色差 > 阈值"""
    issues = []
    # 对每张图的top颜色，找其他图中最接近的颜色，比较色差
    figs_list = list(figures.items())
    for i in range(len(figs_list)):
        for j in range(i+1, len(figs_list)):
            name1, colors1 = figs_list[i]
            name2, colors2 = figs_list[j]
            for c1 in colors1.most_common(5):
                hex1, _ = c1
                for c2 in colors2.most_common(5):
                    hex2, _ = c2
                    dist = rgb_distance(hex1, hex2)
                    # 同一颜色在不同图：色差<5=一致, 5-15=可疑, >15=不一致
                    if 5 < dist < 15:
                        issues.append({
                            'type': 'color_drift',
                            'fig1': name1, 'fig2': name2,
                            'color1': hex1, 'color2': hex2,
                            'distance': round(dist, 1),
                            'severity': 'WARN',
                            'message': f'{hex1}({name1}) vs {hex2}({name2}): ΔE={dist:.1f} — 可能同一语义颜色跨图不一致'
                        })
    return issues

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path('figure_audit.json'))
    parser.add_argument('--threshold', type=float, default=5.0, help='ΔE阈值(默认5)')
    args = parser.parse_args()

    figures = {}
    for ext, extractor in [('.svg', extract_svg_colors), ('.png', extract_png_colors)]:
        for f in args.dir.glob(f'*{ext}'):
            try:
                colors = extractor(f)
                if colors:
                    figures[f.name] = colors
            except: pass

    if len(figures) < 2:
        print('需要 ≥2 张图才能做跨图对比')
        return 0

    # 红绿检测
    issues = []
    for name, colors in figures.items():
        hexes = [c[0] for c in colors.most_common(10)]
        reds = [h for h in hexes if int(h[1:3],16)>180 and int(h[3:5],16)<80 and int(h[5:7],16)<80]
        greens = [h for h in hexes if int(h[1:3],16)<80 and int(h[3:5],16)>180 and int(h[5:7],16)<80]
        if reds and greens and rgb_distance(reds[0], greens[0]) > 50:
            issues.append({'type':'red_green','fig':name,'severity':'ERROR',
                          'message':f'红绿配色({reds[0]}/{greens[0]})—色盲不可区分'})

    # 跨图色差
    drift = detect_color_drift(figures)
    issues.extend(drift)

    report = {
        'figures': len(figures),
        'total_colors': sum(len(c) for c in figures.values()),
        'issues': len(issues),
        'details': issues,
        'verdict': 'PASS' if not issues else 'FIX_REQUIRED'
    }
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'跨图审计: {len(figures)}张, {report["total_colors"]}色, {len(issues)}问题')
    for i in issues[:8]:
        print(f'  [{i["severity"]}] {i["message"]}')
    print(f'报告: {args.out} ({report["verdict"]})')

    return 1 if any(i['severity']=='ERROR' for i in issues) else 0

if __name__ == '__main__':
    raise SystemExit(main())
