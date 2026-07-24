# Origin Auto Plot

通过 CSV + YAML 规格文件，调用 Windows 本机 Origin/OriginPro 自动生成图表并导出图片和可编辑工程文件。

## 环境要求

- Windows 操作系统
- Origin 或 OriginPro 2021 或更高版本
- Python 3.8+
- `pip install -r requirements.txt`

## 安装

```bash
pip install -r tools\origin_auto_plot\requirements.txt
```

## 输入

| 输入 | 格式 | 说明 |
|------|------|------|
| 数据文件 | `.csv` | 包含绘图所需列 |
| 图形说明文件 | `.yaml`（符合 `figure_spec.schema.json`） | 指定图类型、列映射、导出参数 |

## 输出

| 输出 | 格式 | 说明 |
|------|------|------|
| 图片 | png / pdf / tif / svg / jpg / eps | 按 `export_formats` 指定导出到 `output_dir` |
| 工程文件 | `.opju` | 可编辑 Origin 工程（可选，默认保存） |

## FigureSpec YAML 协议

完整字段定义见 `figure_spec.schema.json`。最小示例：

```yaml
input_csv: data.csv
figure_type: line
x: Time
y:
  - Signal_A
  - Signal_B
output_name: my_plot
export_formats:
  - png
  - pdf
save_opju: true
output_dir: output
```

支持图表类型：`line`、`scatter`、`bar`、`heatmap`。

## 使用示例

```bash
# 演示数据
python tools\origin_auto_plot\plot_from_csv.py --spec tools\origin_auto_plot\examples\demo_figure_spec.yaml

# 自定义 spec
python tools\origin_auto_plot\plot_from_csv.py --spec path\to\my_spec.yaml

# 指定输出目录
python tools\origin_auto_plot\plot_from_csv.py --spec my_spec.yaml --output-dir results
```

## 限制

- 第一版仅支持 line、scatter、bar、heatmap 四种图类型
- 需要在已安装 Origin/OriginPro 的 Windows 机器上运行
- 如果 Origin 不可用，程序会输出清晰错误提示而非崩溃

## 目录结构

```
tools\origin_auto_plot\
├── README.md
├── requirements.txt
├── figure_spec.schema.json
├── origin_bridge.py          # Origin 启动/退出/导出封装
├── plot_from_csv.py          # CLI 入口：CSV + YAML → 图
└── examples\
    ├── demo_line.csv
    └── demo_figure_spec.yaml
```
