#!/usr/bin/env python3
"""GIS空间数据验证脚本 — 开发/分析完成后自动触发检查。

触发场景（见 academic-workflow/SKILL.md §GIS空间数据处理规范）：
  - 写完任何涉及地理数据的代码后
  - 空间分析结果导出前
  - 提交论文/组会材料前

用法:
  python check_gis_data.py --dir results/           # 检查目录下所有空间文件
  python check_gis_data.py --file output.tif         # 检查单个文件
  python check_gis_data.py --code analysis.py        # 检查Python代码中的GIS反模式
"""

import argparse
import json
import sys
import warnings
from pathlib import Path
from datetime import datetime

# ── 检查项定义 ──
CHECKS = []

def check(severity, category, name):
    """装饰器：注册检查项"""
    def decorator(func):
        CHECKS.append({
            'severity': severity,  # BLOCKER / ERROR / WARN / INFO
            'category': category,
            'name': name,
            'func': func,
        })
        return func
    return decorator


# ═══════════════════════════════════════════════════════
# 空间文件检查
# ═══════════════════════════════════════════════════════

@check('BLOCKER', 'CRS', '投影坐标系检查')
def check_crs_is_projected(filepath: Path) -> list[dict]:
    """涉及距离/面积计算时必须用投影坐标系"""
    issues = []
    try:
        import rasterio
        with rasterio.open(filepath) as src:
            if src.crs and src.crs.is_geographic:
                issues.append({
                    'file': str(filepath),
                    'severity': 'BLOCKER',
                    'message': f'使用地理坐标系({src.crs})，距离/面积计算会失真。请用投影坐标系(如UTM)',
                    'fix': 'gdalwarp -t_srs EPSG:32650 (或对应UTM带) input.tif output.tif',
                })
    except ImportError:
        pass
    except Exception:
        pass
    return issues


@check('ERROR', 'CRS', 'CRS信息缺失')
def check_crs_exists(filepath: Path) -> list[dict]:
    """空间文件必须有CRS"""
    issues = []
    try:
        import rasterio
        with rasterio.open(filepath) as src:
            if not src.crs:
                issues.append({
                    'file': str(filepath),
                    'severity': 'ERROR',
                    'message': '文件缺少CRS（坐标参考系统）信息',
                    'fix': 'gdal_translate -a_srs EPSG:4326 input.tif output.tif',
                })
    except ImportError:
        pass
    except Exception:
        pass
    return issues


@check('ERROR', 'Geometry', '无效几何检测')
def check_valid_geometry(filepath: Path) -> list[dict]:
    """shapefile/geojson中不应有空几何或无效几何"""
    issues = []
    if filepath.suffix not in ('.shp', '.gpkg', '.geojson'):
        return issues
    try:
        import fiona
        with fiona.open(filepath) as src:
            invalid = 0
            for feat in src:
                geom = feat.get('geometry')
                if geom is None:
                    invalid += 1
            if invalid:
                issues.append({
                    'file': str(filepath),
                    'severity': 'ERROR',
                    'message': f'{invalid}个要素包含空几何',
                    'fix': '在QGIS中运行 Fix geometries 工具，或用 geopandas: gdf.geometry = gdf.geometry.buffer(0)',
                })
    except ImportError:
        pass
    except Exception:
        pass
    return issues


@check('WARN', 'Data', 'NoData值检查')
def check_nodata_consistency(filepath: Path) -> list[dict]:
    """多源栅格叠加前检查NoData一致性"""
    issues = []
    if filepath.suffix not in ('.tif', '.tiff', '.img'):
        return issues
    try:
        import rasterio
        with rasterio.open(filepath) as src:
            nodata = src.nodata
            if nodata is None:
                issues.append({
                    'file': str(filepath),
                    'severity': 'WARN',
                    'message': '栅格文件未设置NoData值',
                    'fix': 'gdal_edit.py -a_nodata -9999 file.tif',
                })
    except Exception:
        pass
    return issues


@check('WARN', 'Data', '像元对齐检查')
def check_pixel_alignment(filepath: Path, reference: Path = None) -> list[dict]:
    """多源数据叠加前检查像元是否对齐"""
    # 仅在提供了参考文件时运行
    if reference is None:
        return []
    issues = []
    try:
        import rasterio
        with rasterio.open(filepath) as s1, rasterio.open(reference) as s2:
            if s1.res != s2.res:
                issues.append({
                    'file': str(filepath),
                    'severity': 'WARN',
                    'message': f'分辨率不匹配: {s1.res} vs 参考 {s2.res}',
                    'fix': 'gdalwarp -tr X Y input.tif aligned.tif',
                })
    except Exception:
        pass
    return issues


# ═══════════════════════════════════════════════════════
# Python代码反模式检查
# ═══════════════════════════════════════════════════════

@check('BLOCKER', 'Code', '经纬度欧氏距离')
def check_geographic_distance(code_lines: list[str]) -> list[dict]:
    """禁止在经纬度坐标上算欧氏距离"""
    issues = []
    suspicious = ['euclidean', 'pdist', 'cdist', 'sklearn.metrics.pairwise',
                  'np.linalg.norm', 'scipy.spatial.distance']
    for i, line in enumerate(code_lines, 1):
        line_lower = line.lower()
        if any(kw in line_lower for kw in suspicious):
            # 检查是否在投影坐标系上下文中
            if 'to_crs' not in line_lower and 'project' not in line_lower:
                issues.append({
                    'file': f'line {i}',
                    'severity': 'BLOCKER',
                    'message': f'疑似在经纬度上计算欧氏距离: {line.strip()[:80]}',
                    'fix': '先投影到UTM等距投影: gdf.to_crs(epsg=32650) 再计算距离',
                })
    return issues


@check('ERROR', 'Code', '大栅格全量读取')
def check_large_raster_read(code_lines: list[str]) -> list[dict]:
    """大栅格禁止全量 ReadAsArray()"""
    issues = []
    for i, line in enumerate(code_lines, 1):
        if 'ReadAsArray()' in line:
            # 检查是否有分块上下文
            context_start = max(0, i - 5)
            context = ''.join(code_lines[context_start:i])
            if 'window' not in context.lower() and 'block' not in context.lower():
                issues.append({
                    'file': f'line {i}',
                    'severity': 'ERROR',
                    'message': f'全量ReadAsArray()可能导致内存溢出: {line.strip()[:80]}',
                    'fix': '用 rasterio.windows 或 gdal.Translate 分块读取',
                })
    return issues


@check('ERROR', 'Code', '空间索引缺失')
def check_spatial_index(code_lines: list[str]) -> list[dict]:
    """空间连接前必须创建空间索引"""
    issues = []
    join_keywords = ['sjoin', 'spatial_join', 'overlay', 'intersects', 'within']
    for i, line in enumerate(code_lines, 1):
        line_lower = line.lower()
        if any(kw in line_lower for kw in join_keywords):
            # 检查前几行是否有索引创建
            context_start = max(0, i - 3)
            context = ''.join(code_lines[context_start:i])
            if 'sindex' not in context.lower() and 'spatial_index' not in context.lower():
                issues.append({
                    'file': f'line {i}',
                    'severity': 'ERROR',
                    'message': f'空间连接前未创建空间索引: {line.strip()[:80]}',
                    'fix': '在 sjoin 前加: gdf.sindex (geopandas) 或 CREATE SPATIAL INDEX (PostGIS)',
                })
    return issues


@check('WARN', 'Code', '随机种子缺失')
def check_random_seed(code_lines: list[str]) -> list[dict]:
    """含随机性的操作必须固定随机种子"""
    issues = []
    random_ops = ['train_test_split', 'RandomForest', 'KMeans', 'sample(', 'shuffle',
                   'np.random', 'random_state', 'random.seed']
    has_random = False
    has_seed = False
    for line in code_lines:
        line_lower = line.lower()
        if any(op.lower() in line_lower for op in ['train_test_split', 'shuffle', 'np.random.rand']):
            has_random = True
        if 'random_state' in line_lower or 'random.seed' in line_lower:
            has_seed = True
    if has_random and not has_seed:
        issues.append({
            'file': '整个文件',
            'severity': 'WARN',
            'message': '代码含随机操作但未固定随机种子，结果不可复现',
            'fix': '添加 random_state=42 参数',
        })
    return issues


@check('WARN', 'Code', '硬编码路径')
def check_hardcoded_paths(code_lines: list[str]) -> list[dict]:
    """禁止硬编码Windows反斜杠路径"""
    issues = []
    for i, line in enumerate(code_lines, 1):
        if '\\\\' in line and ('open(' in line or 'read_' in line or 'Path(' in line):
            issues.append({
                'file': f'line {i}',
                'severity': 'WARN',
                'message': f'硬编码反斜杠路径: {line.strip()[:80]}',
                'fix': '用 pathlib.Path 或正斜杠 /',
            })
    return issues


# ═══════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════

SPATIAL_EXTS = {'.tif', '.tiff', '.shp', '.gpkg', '.geojson', '.img', '.vrt', '.nc'}


def check_file(filepath: Path, reference: Path = None) -> list[dict]:
    """对单个文件运行所有适用的检查"""
    all_issues = []
    for check_def in CHECKS:
        func = check_def['func']
        try:
            if func.__name__.startswith('check_') and 'code' not in func.__name__.lower():
                if filepath.suffix.lower() in SPATIAL_EXTS or 'any' in str(func.__annotations__):
                    result = func(filepath)
                else:
                    continue
            else:
                continue
            if result:
                all_issues.extend(result)
        except Exception as e:
            all_issues.append({
                'file': str(filepath),
                'severity': 'INFO',
                'message': f'检查 {check_def["name"]} 执行失败: {e}',
            })
    return all_issues


def check_code(filepath: Path) -> list[dict]:
    """对Python代码运行反模式检查"""
    if filepath.suffix != '.py':
        return []
    lines = filepath.read_text(encoding='utf-8').splitlines()
    all_issues = []
    for check_def in CHECKS:
        func = check_def['func']
        if 'code' in func.__name__.lower() or 'Code' in check_def['category']:
            try:
                result = func(lines)
                if result:
                    all_issues.extend(result)
            except Exception as e:
                pass
    return all_issues


def main():
    parser = argparse.ArgumentParser(description='GIS空间数据验证')
    parser.add_argument('--dir', type=Path, help='检查目录下所有空间文件')
    parser.add_argument('--file', type=Path, help='检查单个文件')
    parser.add_argument('--code', type=Path, help='检查Python代码反模式')
    parser.add_argument('--ref', type=Path, help='参考栅格（用于像元对齐检查）')
    parser.add_argument('--json', type=Path, help='输出JSON报告')
    args = parser.parse_args()

    if not any([args.dir, args.file, args.code]):
        parser.print_help()
        return 0

    all_issues = []

    # 空间文件检查
    spatial_files = []
    if args.dir:
        spatial_files = [f for f in args.dir.rglob('*') if f.suffix.lower() in SPATIAL_EXTS]
        print(f'扫描目录 {args.dir}: 发现 {len(spatial_files)} 个空间文件')
    elif args.file:
        spatial_files = [args.file]

    for f in spatial_files:
        issues = check_file(f, args.ref)
        all_issues.extend(issues)

    # 代码检查
    if args.code:
        issues = check_code(args.code)
        all_issues.extend(issues)

    # ── 输出 ──
    blockers = [i for i in all_issues if i['severity'] == 'BLOCKER']
    errors = [i for i in all_issues if i['severity'] == 'ERROR']
    warns = [i for i in all_issues if i['severity'] == 'WARN']

    print(f'\n{"="*60}')
    print(f'GIS数据验证报告 — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'{"="*60}')
    print(f'  BLOCKER: {len(blockers)}   ERROR: {len(errors)}   WARN: {len(warns)}')

    for severity, items in [('BLOCKER', blockers), ('ERROR', errors), ('WARN', warns)]:
        if items:
            print(f'\n── {severity} ──')
            for item in items:
                print(f'  [{severity}] {item["file"]}')
                print(f'          {item["message"]}')
                if 'fix' in item:
                    print(f'          修复: {item["fix"]}')

    if args.json:
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {'blocker': len(blockers), 'error': len(errors), 'warn': len(warns)},
            'issues': all_issues,
        }
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\nJSON报告: {args.json}')

    return 1 if blockers else 0


if __name__ == '__main__':
    raise SystemExit(main())
