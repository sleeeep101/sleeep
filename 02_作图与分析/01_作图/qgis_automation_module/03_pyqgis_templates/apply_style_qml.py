"""Apply a QML style file to a vector or raster layer."""
from pathlib import Path
from qgis.core import QgsProject


def apply_qml(layer_name: str, qml_path: str) -> None:
    """Apply QML style to an existing layer by name.

    Args:
        layer_name: Name of the layer in the current project
        qml_path: Path to .qml style file
    """
    qml = Path(qml_path)
    if not qml.exists():
        raise FileNotFoundError(f"QML file not found: {qml_path}")

    layers = QgsProject.instance().mapLayersByName(layer_name)
    if not layers:
        raise ValueError(f"Layer not found: {layer_name}")

    layer = layers[0]
    result = layer.loadNamedStyle(str(qml))
    if not result[0]:
        raise Exception(f"Failed to apply QML: {result[1]}")

    layer.triggerRepaint()
    print(f"[OK] Applied QML style to: {layer_name}")
    print(f"     QML: {qml_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python apply_style_qml.py <layer_name> <qml_path>")
        sys.exit(1)
    apply_qml(sys.argv[1], sys.argv[2])
