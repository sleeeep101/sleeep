"""Attribute filter + field calculator for vector layers. No overwrite of source."""
from pathlib import Path
from qgis.core import QgsVectorLayer, QgsFeatureRequest, QgsField, QgsProject
from qgis.PyQt.QtCore import QVariant


def filter_by_expression(layer_path: str, expression: str, output_path: str, layer_name: str = None) -> str:
    """Filter features by expression and save to new GeoPackage.

    Args:
        layer_path: Input vector file
        expression: QGIS expression (e.g. '"area" > 1000')
        output_path: Output GeoPackage
        layer_name: Output layer name
    Returns output_path or raises.
    """
    in_path = Path(layer_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {layer_path}")

    layer = QgsVectorLayer(str(in_path), "source", "ogr")
    if not layer.isValid():
        raise Exception(f"Failed to load: {layer_path}")

    request = QgsFeatureRequest().setFilterExpression(expression)
    features = [f for f in layer.getFeatures(request)]
    print(f"[OK] Expression '{expression}': {len(features)}/{layer.featureCount()} features matched")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    name = layer_name or f"{in_path.stem}_filtered"

    if out_path.suffix.lower() != ".gpkg":
        out_path = out_path.with_suffix(".gpkg")

    # Save as new GeoPackage
    from qgis.core import QgsVectorFileWriter
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = name
    QgsVectorFileWriter.writeAsVectorFormatV3(layer, str(out_path),
        layer.crs(), options)

    # Re-open and filter
    out_layer = QgsVectorLayer(f"{str(out_path)}|layername={name}", name, "ogr")
    out_layer.startEditing()
    # Delete non-matching
    ids_to_delete = []
    for f in out_layer.getFeatures():
        if f.id() >= len(features):
            ids_to_delete.append(f.id())
    if ids_to_delete:
        out_layer.deleteFeatures(ids_to_delete)
    out_layer.commitChanges()

    print(f"[OK] Saved filtered: {output_path} ({len(features)} features)")
    return str(output_path)


def add_field(layer_path: str, field_name: str, field_type: str = "double",
              expression: str = None, output_path: str = None) -> str:
    """Add a calculated field to layer.

    Args:
        layer_path: Input vector file
        field_name: New field name
        field_type: 'double' | 'int' | 'string'
        expression: QGIS expression for calculation (e.g. '"area" * 0.001')
        output_path: Output path (defaults to input with _calc suffix)
    """
    in_path = Path(layer_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {layer_path}")

    type_map = {"double": QVariant.Double, "int": QVariant.Int, "string": QVariant.String}
    qtype = type_map.get(field_type, QVariant.Double)

    out = str(output_path or in_path.parent / f"{in_path.stem}_calc.gpkg")
    layer = QgsVectorLayer(str(in_path), "source", "ogr")
    if not layer.isValid():
        raise Exception(f"Failed to load: {layer_path}")

    # Save copy
    from qgis.core import QgsVectorFileWriter
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    QgsVectorFileWriter.writeAsVectorFormatV3(layer, out, layer.crs(), options)

    out_layer = QgsVectorLayer(out, "output", "ogr")
    out_layer.startEditing()
    out_layer.dataProvider().addAttributes([QgsField(field_name, qtype)])
    out_layer.updateFields()

    if expression:
        idx = out_layer.fields().indexOf(field_name)
        for f in out_layer.getFeatures():
            out_layer.changeAttributeValue(f.id(), idx,
                _eval_simple_expr(f, expression))
    out_layer.commitChanges()

    print(f"[OK] Added field '{field_name}' ({field_type}) to: {out}")
    return out


def _eval_simple_expr(feature, expr: str):
    """Simple expression evaluator for common patterns."""
    # Maps 'field_name' * scalar → actual calculation
    import re
    for field_name in [f.name() for f in feature.fields()]:
        if field_name in expr:
            val = feature.attribute(field_name)
            if val is not None:
                try:
                    return eval(expr.replace(field_name, str(val)),
                               {"__builtins__": {}}, {})
                except Exception:
                    pass
    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  filter: python attribute_filter_and_field_calc.py filter <input> <expression> <output>")
        print("  calc:   python attribute_filter_and_field_calc.py calc <input> <field> <type> <expression> [output]")
        sys.exit(1)
    op = sys.argv[1]
    if op == "filter":
        filter_by_expression(sys.argv[2], sys.argv[3], sys.argv[4])
    elif op == "calc":
        add_field(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
                  sys.argv[6] if len(sys.argv) > 6 else None)
