"""Apply categorized or graduated symbology to a vector layer. No data overwrite."""
from pathlib import Path
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer, QgsRendererCategory, QgsRendererRange,
    QgsSymbol, QgsColorRampShader, QgsStyle,
)


def apply_categorized(layer: QgsVectorLayer, field_name: str,
                      color_ramp: str = "Random colors") -> QgsCategorizedSymbolRenderer:
    """Apply categorized renderer by field values.

    Args:
        layer: Loaded QgsVectorLayer
        field_name: Field to categorize by
        color_ramp: QGIS color ramp name
    """
    idx = layer.fields().indexOf(field_name)
    if idx < 0:
        raise ValueError(f"Field not found: {field_name}")

    values = sorted(set(str(f.attribute(field_name)) for f in layer.getFeatures()
                       if f.attribute(field_name) is not None))

    categories = []
    default_style = QgsStyle().defaultStyle()
    ramp = default_style.colorRamp(color_ramp)
    n = len(values)

    for i, val in enumerate(values):
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        if ramp and n > 1:
            symbol.setColor(ramp.color(i / (n - 1)))
        categories.append(QgsRendererCategory(val, symbol, val))

    renderer = QgsCategorizedSymbolRenderer(field_name, categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    print(f"[OK] Categorized: {field_name} ({len(values)} categories)")
    return renderer


def apply_graduated(layer: QgsVectorLayer, field_name: str, classes: int = 5,
                    color_ramp: str = "Blues") -> QgsGraduatedSymbolRenderer:
    """Apply graduated (choropleth) renderer.

    Args:
        layer: Loaded QgsVectorLayer
        field_name: Numeric field
        classes: Number of classes (2-10)
        color_ramp: QGIS color ramp name
    """
    idx = layer.fields().indexOf(field_name)
    if idx < 0:
        raise ValueError(f"Field not found: {field_name}")

    vals = [f.attribute(field_name) for f in layer.getFeatures()
            if f.attribute(field_name) is not None]
    if not vals:
        raise ValueError(f"No valid values in field: {field_name}")

    vmin, vmax = min(vals), max(vals)
    step = (vmax - vmin) / classes

    default_style = QgsStyle().defaultStyle()
    ramp = default_style.colorRamp(color_ramp)

    ranges = []
    for i in range(classes):
        lo = vmin + i * step
        hi = vmin + (i + 1) * step
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        if ramp:
            symbol.setColor(ramp.color(i / max(1, classes - 1)))
        ranges.append(QgsRendererRange(lo, hi, symbol, f"{lo:.1f} - {hi:.1f}"))

    renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    print(f"[OK] Graduated: {field_name} ({classes} classes, {vmin:.1f}-{vmax:.1f})")
    return renderer


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage:")
        print("  cat: python categorized_graduated_style.py cat <layer_path> <field> [color_ramp]")
        print("  grad: python categorized_graduated_style.py grad <layer_path> <field> [classes] [color_ramp]")
        sys.exit(1)

    op = sys.argv[1]
    path = Path(sys.argv[2])
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    layer = QgsVectorLayer(str(path), path.stem, "ogr")
    if not layer.isValid():
        print(f"ERROR: Invalid layer: {path}")
        sys.exit(1)

    QgsProject.instance().addMapLayer(layer)

    if op == "cat":
        apply_categorized(layer, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "Random colors")
    elif op == "grad":
        apply_graduated(layer, sys.argv[3],
                        int(sys.argv[4]) if len(sys.argv) > 4 else 5,
                        sys.argv[5] if len(sys.argv) > 5 else "Blues")
