"""
命令行工具：读取 CSV + YAML FigureSpec，调用 Origin 自动生成图表。

Usage:
    python plot_from_csv.py --spec examples/demo_figure_spec.yaml
    python plot_from_csv.py --spec my_spec.yaml --output-dir results
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import yaml

# 将父目录加入 path，支持从项目根或模块目录运行
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from origin_bridge import OriginSession, ensure_origin, export_graph, save_opju, ensure_output_dir


# ---------------------------------------------------------------------------
# JSON Schema 基本校验（不引入 jsonschema 依赖）
# ---------------------------------------------------------------------------
def validate_spec(spec: dict):
    """对 FigureSpec 做基本字段校验，不符合则抛出 ValueError。"""
    SCHEMA_PATH = _THIS_DIR / "figure_spec.schema.json"
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)

    required = schema.get("required", [])
    for key in required:
        if key not in spec:
            raise ValueError(f"缺少必填字段: {key}")

    figure_type = spec.get("figure_type", "")
    allowed_types = schema["properties"]["figure_type"]["enum"]
    if figure_type not in allowed_types:
        raise ValueError(f"不支持的 figure_type: '{figure_type}'，允许: {allowed_types}")

    if figure_type in ("line", "scatter", "bar") and "y" not in spec:
        raise ValueError(f"{figure_type} 图必须指定 y 字段")

    if figure_type == "heatmap" and "z" not in spec:
        raise ValueError("heatmap 图必须指定 z 字段")

    # 校验 export_formats
    allowed_fmts = schema["properties"]["export_formats"]["items"]["enum"]
    for fmt in spec.get("export_formats", ["png"]):
        if fmt not in allowed_fmts:
            raise ValueError(f"不支持的导出格式: '{fmt}'，允许: {allowed_fmts}")


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------
def resolve_path(spec_file: str, target: str) -> str:
    """以 spec 文件所在目录为基准解析相对路径。"""
    base = Path(spec_file).resolve().parent
    return str(base / target)


def read_csv_columns(csv_path: str) -> list:
    """读取 CSV 列名。"""
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        return next(reader)


def read_csv_data(csv_path: str) -> list:
    """读取 CSV 全部数据行（返回 list of list of float/str）。"""
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = []
        for row in reader:
            parsed = []
            for val in row:
                try:
                    parsed.append(float(val))
                except ValueError:
                    parsed.append(val)
            rows.append(parsed)
        return header, rows


def _to_list(val):
    """标准化为 list。"""
    if isinstance(val, list):
        return val
    return [val]


# ---------------------------------------------------------------------------
# 主绘图逻辑
# ---------------------------------------------------------------------------
def plot_spec(spec_file: str, output_dir_override: str | None = None):
    """执行完整的 spec → 图表流程。"""
    # 1. 读取 YAML
    spec_path = Path(spec_file).resolve()
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    validate_spec(spec)

    # 2. 定位 CSV
    csv_path = resolve_path(spec_file, spec["input_csv"])
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

    # 3. 校验列名
    columns = read_csv_columns(csv_path)
    x_cols = _to_list(spec["x"])
    y_cols = _to_list(spec.get("y", []))
    z_col = spec.get("z")
    for c in x_cols + y_cols:
        if c not in columns:
            raise ValueError(f"CSV 中缺少列: '{c}'，可用列: {columns}")
    if z_col and z_col not in columns:
        raise ValueError(f"CSV 中缺少 z 列: '{z_col}'，可用列: {columns}")

    # 4. 输出目录
    output_dir = output_dir_override or spec.get("output_dir", "output")
    output_dir = resolve_path(spec_file, output_dir)
    ensure_output_dir(output_dir)

    output_base = os.path.join(output_dir, spec["output_name"])
    figure_type = spec["figure_type"]

    print(f"[INFO] 读取 CSV: {csv_path}")
    print(f"[INFO] 图表类型: {figure_type}")
    print(f"[INFO] X: {x_cols}, Y: {y_cols}")
    print(f"[INFO] 输出: {output_base}.*")

    # 5. 启动 Origin 并绘图
    with OriginSession(show=True) as op:
        # 创建 workbook 并写入数据
        header, rows = read_csv_data(csv_path)
        wb = op.new_book("w")
        ws = wb[0]
        ws.from_list(0, [header] + rows)
        wb.lname = spec.get("title", spec["output_name"])

        # 根据类型创建图
        if figure_type in ("line", "scatter", "bar"):
            # 找到列索引
            x_idx = [columns.index(c) for c in x_cols]
            y_idx = [columns.index(c) for c in y_cols]

            gp = op.new_graph(template=spec.get("template", ""))
            gl = gp[0]

            plot_method = {
                "line": gl.add_plot,
                "scatter": gl.add_plot,
                "bar": gl.add_plot,
            }[figure_type]

            for xi in x_idx:
                for yi in y_idx:
                    plot = plot_method(ws, xi, yi)
                    if figure_type == "scatter":
                        plot.colormap = "scatter"

            gl.set_title(spec.get("title", ""))
            gl.set_xlabel(spec.get("xlabel", ""))
            gl.set_ylabel(spec.get("ylabel", ""))

        elif figure_type == "heatmap":
            x_idx = columns.index(x_cols[0])
            y_idx = columns.index(y_cols[0])
            z_idx = columns.index(z_col)

            gp = op.new_graph(template=spec.get("template", ""))
            gl = gp[0]
            gl.add_plot(ws, x_idx, y_idx, z_idx, type="heatmap")

            gl.set_title(spec.get("title", ""))
            gl.set_xlabel(spec.get("xlabel", ""))
            gl.set_ylabel(spec.get("ylabel", ""))

        # 6. 导出图片
        export_formats = spec.get("export_formats", ["png"])
        export_graph(gp, output_base, export_formats)

        # 7. 保存 opju
        if spec.get("save_opju", True):
            opju_path = os.path.join(output_dir, f"{spec['output_name']}.opju")
            save_opju(opju_path)

    print("[DONE] 所有导出完成。")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Origin Auto Plot — CSV + YAML → Origin 图表"
    )
    parser.add_argument(
        "--spec", required=True,
        help="FigureSpec YAML 文件路径"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="输出目录（覆盖 spec 中的 output_dir）"
    )
    args = parser.parse_args()

    try:
        ensure_origin()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    try:
        plot_spec(args.spec, args.output_dir)
    except Exception as e:
        print(f"[ERROR] 绘图失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
