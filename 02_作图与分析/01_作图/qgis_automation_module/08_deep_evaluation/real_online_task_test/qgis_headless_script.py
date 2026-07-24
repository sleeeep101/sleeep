"""Natural Earth China+Cities Map — Headless PyQGIS"""
import sys, os, json
from pathlib import Path
from datetime import datetime

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemScaleBar,
    QgsLayoutExporter, QgsCoordinateReferenceSystem,
    QgsCategorizedSymbolRenderer, QgsRendererCategory,
    QgsGraduatedSymbolRenderer, QgsRendererRange,
    QgsSymbol, QgsFillSymbol, QgsMarkerSymbol,
    QgsLayoutItemPicture,
)
from qgis.PyQt.QtCore import QRectF

qgs = QgsApplication([], False)
qgs.initQgis()
print(f"QGIS {QgsApplication.instance().showSettings().split(chr(10))[0]}")

TD = Path("<LOCAL_PATH>")
RAW = TD / "input_raw"
OUT = TD / "after_outputs/20260606_natural_earth_china_cities"
BEFORE = TD / "before_preview"
LOG_DIR = TD / "logs"
for d in [OUT, BEFORE, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load
countries = QgsVectorLayer(str(RAW / "countries/ne_110m_admin_0_countries.shp"), "Countries", "ogr")
places = QgsVectorLayer(str(RAW / "places/ne_110m_populated_places_simple.shp"), "Places", "ogr")
for l, n in [(countries, "Countries"), (places, "Places")]:
    if not l.isValid():
        print(f"FAIL: {n}"); qgs.exitQgis(); sys.exit(1)
    print(f"[OK] {n}: {l.featureCount()} features, {l.crs().authid()}")

project = QgsProject.instance()
project.addMapLayer(countries)
project.addMapLayer(places)
project.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

# ── Before preview ──
print("\n=== BEFORE PREVIEW ===")
layout_before = QgsPrintLayout(project)
layout_before.initializeDefaults()
map_before = QgsLayoutItemMap(layout_before)
map_before.setRect(QRectF(5, 5, 200, 150))
map_before.setExtent(countries.extent())
layout_before.addLayoutItem(map_before)
label_b = QgsLayoutItemLabel(layout_before)
label_b.setText("Before: Natural Earth Raw Global Data (Default Style)")
label_b.setRect(QRectF(5, 158, 200, 10))
layout_before.addLayoutItem(label_b)

before_png = str(BEFORE / "before_preview.png")
r = QgsLayoutExporter(layout_before).exportToImage(before_png, QgsLayoutExporter.ImageExportSettings())
print(f"[{'OK' if r==0 else 'FAIL'}] {before_png} ({Path(before_png).stat().st_size if Path(before_png).exists() else 0} bytes)")

# ── Filter ──
print("\n=== PROCESSING ===")
china_region = ["China","India","Japan","South Korea","North Korea","Mongolia","Russia",
    "Kazakhstan","Kyrgyzstan","Tajikistan","Pakistan","Afghanistan","Nepal","Bhutan",
    "Myanmar","Laos","Vietnam","Thailand","Cambodia","Bangladesh","Taiwan","Philippines"]
qstr = ",".join(f"'{n}'" for n in china_region)
countries.setSubsetString(f'"SOVEREIGNT" IN ({qstr})')
print(f"Filtered to {countries.featureCount()} countries")

# Style countries
renderer = QgsCategorizedSymbolRenderer("SOVEREIGNT", [])
for f in countries.getFeatures():
    sov = f.attribute("SOVEREIGNT") or ""
    is_cn = (sov == "China")
    sym = QgsFillSymbol.createSimple({
        "color": "255,80,80,120" if is_cn else "220,220,220,60",
        "outline_color": "180,20,20,220" if is_cn else "160,160,160,120",
        "outline_width": "1.0" if is_cn else "0.3"
    })
    renderer.addCategory(QgsRendererCategory(sov, sym, sov))
countries.setRenderer(renderer)
countries.triggerRepaint()
print("[OK] Country styles")

# Style places
ranks = sorted(set(f.attribute("scalerank") for f in places.getFeatures() if f.attribute("scalerank") is not None))
grad = QgsGraduatedSymbolRenderer("scalerank", [])
colors = [(220,50,50),(240,120,50),(250,180,60),(100,160,220)]
for i, rk in enumerate(ranks[:4]):
    c = colors[i%4]
    sym = QgsMarkerSymbol.createSimple({"color": f"{c[0]},{c[1]},{c[2]}", "size": str(9-i*2), "outline_color": "0,0,0,100"})
    hi = rk + (1 if rk < max(ranks) else 0.01)
    grad.addClassRange(QgsRendererRange(rk, hi, sym, f"Rank {rk}"))
places.setRenderer(grad)
places.triggerRepaint()
print("[OK] Place styles")

# Get filtered extent for China region
ext = countries.extent()
map_center_x = (ext.xMinimum() + ext.xMaximum()) / 2
map_center_y = (ext.yMinimum() + ext.yMaximum()) / 2

# ── After map ──
print("\n=== AFTER MAP ===")
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName("ChinaCities")

map_item = QgsLayoutItemMap(layout)
map_item.setRect(QRectF(10, 10, 190, 140))
map_item.setExtent(ext)
map_item.zoomToExtent(ext)
layout.addLayoutItem(map_item)

title = QgsLayoutItemLabel(layout)
title.setText("Natural Earth: China & Surrounding Major Cities")
title.setRect(QRectF(10, 155, 190, 10))
layout.addLayoutItem(title)

legend = QgsLayoutItemLegend(layout)
legend.setRect(QRectF(10, 168, 80, 55))
layout.addLayoutItem(legend)

scalebar = QgsLayoutItemScaleBar(layout)
scalebar.setRect(QRectF(100, 168, 85, 8))
layout.addLayoutItem(scalebar)

# North arrow
try:
    svg = QgsApplication.defaultThemePath() + "/arrows/NorthArrow_02.svg"
    if Path(svg).exists():
        north = QgsLayoutItemPicture(layout)
        north.setPicturePath(svg)
        north.setRect(QRectF(185, 175, 12, 12))
        layout.addLayoutItem(north)
except Exception as e:
    print(f"[WARN] North arrow: {e}")

exporter = QgsLayoutExporter(layout)
after_png = str(OUT / "after_map.png")
after_pdf = str(OUT / "after_map.pdf")
after_qgz = str(OUT / "after_project.qgz")

r = exporter.exportToImage(after_png, QgsLayoutExporter.ImageExportSettings())
print(f"[{'OK' if r==0 else 'FAIL'}] PNG: {after_png} ({Path(after_png).stat().st_size if Path(after_png).exists() else 0} bytes)")

r = exporter.exportToPdf(after_pdf, QgsLayoutExporter.PdfExportSettings())
print(f"[{'OK' if r==0 else 'FAIL'}] PDF: {after_pdf} ({Path(after_pdf).stat().st_size if Path(after_pdf).exists() else 0} bytes)")

project.write(after_qgz)
print(f"[OK] QGZ: {after_qgz} ({Path(after_qgz).stat().st_size} bytes)")

# Log
with open(str(LOG_DIR / "execution_log.json"), "w") as f:
    json.dump({"timestamp": datetime.now().isoformat(), "data": {
        "countries_zip_sha256": "0f243aeac8ac6cf26f0417285b0bd33ac47f1b5bdb719fd3e0df37d03ea37110",
        "places_zip_sha256": "3f3d99a9a5d84605bb3be07b94c9122b4d69d7545de478b314d75f5b0742afdf"},
        "countries_count": countries.featureCount(), "places_count": places.featureCount(),
        "crs": "EPSG:4326", "outputs": [before_png, after_png, after_pdf, after_qgz]}, f, indent=2)

qgs.exitQgis()
print("\n=== COMPLETE ===")
