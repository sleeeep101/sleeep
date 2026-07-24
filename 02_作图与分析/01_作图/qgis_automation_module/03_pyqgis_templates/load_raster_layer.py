"""Load a raster layer (tif/img) into the current QGIS project."""
from pathlib import Path
from qgis.core import QgsRasterLayer, QgsProject


def load_raster(filepath: str, layer_name: str = None) -> QgsRasterLayer:
    """Load raster file and add to QGIS project.

    Args:
        filepath: Path to tif/img raster file
        layer_name: Display name (defaults to filename)
    Returns:
        QgsRasterLayer or raises Exception
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Raster file not found: {filepath}")

    name = layer_name or path.stem
    layer = QgsRasterLayer(str(path), name)

    if not layer.isValid():
        raise Exception(f"Raster failed to load: {filepath}")

    QgsProject.instance().addMapLayer(layer)
    print(f"[OK] Loaded raster: {name}")
    print(f"     Size: {layer.width()}x{layer.height()}")
    print(f"     Bands: {layer.bandCount()}")
    print(f"     CRS: {layer.crs().authid()}")
    return layer


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python load_raster_layer.py <filepath> [layer_name]")
        sys.exit(1)
    name = sys.argv[2] if len(sys.argv) > 2 else None
    load_raster(sys.argv[1], name)
