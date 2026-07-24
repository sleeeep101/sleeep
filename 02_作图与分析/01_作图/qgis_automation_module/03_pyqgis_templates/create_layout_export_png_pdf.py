"""Create a Print Layout with map/legend/title/scalebar and export to PNG/PDF."""
from pathlib import Path
from qgis.core import (
    QgsProject, QgsPrintLayout, QgsLayoutItemMap,
    QgsLayoutItemLegend, QgsLayoutItemLabel, QgsLayoutItemScaleBar,
    QgsLayoutExporter, QgsLayoutPoint, QgsUnitTypes,
)
from qgis.PyQt.QtCore import QRectF


def create_layout(layout_name: str = "MapExport") -> QgsPrintLayout:
    """Create a new Print Layout."""
    project = QgsProject.instance()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)
    return layout


def add_map(layout: QgsPrintLayout, x=10, y=10, w=200, h=140):
    """Add map item showing all project layers."""
    map_item = QgsLayoutItemMap(layout)
    map_item.setRect(QRectF(x, y, w, h))
    map_item.setFrameEnabled(True)
    # Fit to all layers
    layers = list(QgsProject.instance().mapLayers().values())
    if layers:
        map_item.setExtent(layers[0].extent())
        map_item.zoomToExtent(layers[0].extent())
    layout.addLayoutItem(map_item)
    return map_item


def add_title(layout: QgsPrintLayout, text: str, x=10, y=155, w=200, h=10):
    """Add a title label."""
    label = QgsLayoutItemLabel(layout)
    label.setText(text)
    label.setRect(QRectF(x, y, w, h))
    layout.addLayoutItem(label)
    return label


def add_legend(layout: QgsPrintLayout, x=10, y=155, w=40, h=40):
    """Add a legend."""
    legend = QgsLayoutItemLegend(layout)
    legend.setRect(QRectF(x, y, w, h))
    layout.addLayoutItem(legend)
    return legend


def add_scalebar(layout: QgsPrintLayout, x=150, y=155, w=60, h=5):
    """Add a scale bar."""
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setRect(QRectF(x, y, w, h))
    layout.addLayoutItem(scalebar)
    return scalebar


def export_png(layout: QgsPrintLayout, output_path: str, dpi: int = 300):
    """Export layout to PNG."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = dpi
    result = QgsLayoutExporter(layout).exportToImage(str(out), settings)
    if result != QgsLayoutExporter.Success:
        raise Exception(f"PNG export failed: {result}")
    print(f"[OK] Exported PNG ({dpi}dpi): {output_path}")


def export_pdf(layout: QgsPrintLayout, output_path: str):
    """Export layout to PDF."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    settings = QgsLayoutExporter.PdfExportSettings()
    result = QgsLayoutExporter(layout).exportToPdf(str(out), settings)
    if result != QgsLayoutExporter.Success:
        raise Exception(f"PDF export failed: {result}")
    print(f"[OK] Exported PDF: {output_path}")


if __name__ == "__main__":
    import sys
    layout = create_layout()
    add_map(layout)
    add_title(layout, "Map Title Here")
    add_legend(layout)
    add_scalebar(layout)

    base = sys.argv[1] if len(sys.argv) > 1 else "output/map"
    export_png(layout, f"{base}.png")
    export_pdf(layout, f"{base}.pdf")
