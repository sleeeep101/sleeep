"""Load a vector layer (shp/gpkg/geojson) into the current QGIS project."""
from pathlib import Path
from qgis.core import QgsVectorLayer, QgsProject


def load_vector(filepath: str, layer_name: str = None) -> QgsVectorLayer:
    """Load vector file and add to QGIS project.

    Args:
        filepath: Path to shp/gpkg/geojson file
        layer_name: Display name (defaults to filename)
    Returns:
        QgsVectorLayer or raises Exception
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Vector file not found: {filepath}")

    name = layer_name or path.stem
    layer = QgsVectorLayer(str(path), name, "ogr")

    if not layer.isValid():
        raise Exception(f"Layer failed to load: {layer.error().message()}")

    QgsProject.instance().addMapLayer(layer)
    print(f"[OK] Loaded vector: {name}")
    print(f"     Features: {layer.featureCount()}")
    print(f"     Geometry: {layer.geometryType()}")
    print(f"     CRS: {layer.crs().authid()}")
    return layer


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python load_vector_layer.py <filepath> [layer_name]")
        sys.exit(1)
    name = sys.argv[2] if len(sys.argv) > 2 else None
    load_vector(sys.argv[1], name)
