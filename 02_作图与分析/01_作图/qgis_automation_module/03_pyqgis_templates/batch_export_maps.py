"""Batch export maps by feature attribute — one map per category/region."""
from pathlib import Path
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsPrintLayout, QgsLayoutItemMap,
    QgsLayoutItemLabel, QgsLayoutExporter, QgsFeatureRequest,
)
from qgis.PyQt.QtCore import QRectF


def batch_export_by_field(
    layer_path: str,
    field_name: str,
    output_dir: str,
    title_prefix: str = "",
    dpi: int = 200,
):
    """Export one map per unique value of a field.

    Args:
        layer_path: Path to vector layer
        field_name: Field to group by (e.g. "region", "category")
        output_dir: Directory for output PNGs
        title_prefix: Optional prefix for map titles
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    layer = QgsVectorLayer(layer_path, "source", "ogr")
    if not layer.isValid():
        raise Exception(f"Failed to load layer: {layer_path}")

    # Get unique values
    idx = layer.fields().indexOf(field_name)
    if idx < 0:
        raise ValueError(f"Field not found: {field_name}")

    values = set()
    for feat in layer.getFeatures():
        val = feat.attribute(field_name)
        if val:
            values.add(str(val))

    print(f"Found {len(values)} unique values for '{field_name}'")

    for val in sorted(values):
        # Set filter
        layer.setSubsetString(f'"{field_name}" = \'{val}\'')

        # Create layout
        project = QgsProject.instance()
        project.addMapLayer(layer)
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(f"batch_{val}")

        # Map
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(QRectF(5, 5, 180, 130))
        map_item.setExtent(layer.extent())
        layout.addLayoutItem(map_item)

        # Title
        title = QgsLayoutItemLabel(layout)
        title.setText(f"{title_prefix} - {val}")
        title.setRect(QRectF(5, 140, 180, 15))
        layout.addLayoutItem(title)

        # Export
        safe_name = val.replace("/", "_").replace("\\", "_")
        output_path = out_dir / f"{safe_name}.png"
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = dpi
        QgsLayoutExporter.exportToImage(layout, str(output_path), settings)
        print(f"  [{val}] -> {output_path}")

        project.removeMapLayer(layer)

    layer.setSubsetString("")
    print(f"[OK] Batch export complete: {len(values)} maps -> {output_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python batch_export_maps.py <layer> <field> <output_dir> [title_prefix]")
        sys.exit(1)
    prefix = sys.argv[4] if len(sys.argv) > 4 else ""
    batch_export_by_field(sys.argv[1], sys.argv[2], sys.argv[3], prefix)
