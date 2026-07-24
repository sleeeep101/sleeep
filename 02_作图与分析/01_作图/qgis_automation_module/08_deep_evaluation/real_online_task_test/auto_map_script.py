"""Fully automated: download Natural Earth → filter East Asia → styled map → export all"""
import sys, os, json, hashlib
from pathlib import Path
from datetime import datetime

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from qgis.core import *
from qgis.PyQt.QtCore import QRectF

qgs = QgsApplication([], False)
qgs.initQgis()

BASE = Path("<LOCAL_PATH>")
RAW = BASE / "input_raw"
OUT = BASE / "after_outputs/20260606_auto_east_asia"
OUT.mkdir(parents=True, exist_ok=True)

# Load
c = QgsVectorLayer(str(RAW/"countries/ne_110m_admin_0_countries.shp"), "Countries", "ogr")
p = QgsVectorLayer(str(RAW/"places/ne_110m_populated_places_simple.shp"), "Cities", "ogr")
print(f"[OK] Countries: {c.featureCount()} | Cities: {p.featureCount()}")

proj = QgsProject.instance()
proj.addMapLayer(c); proj.addMapLayer(p)
proj.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

# 1. Before preview
lb = QgsPrintLayout(proj); lb.initializeDefaults()
mb = QgsLayoutItemMap(lb); mb.setRect(QRectF(5,5,200,150)); mb.setExtent(c.extent())
lb.addLayoutItem(mb)
QgsLayoutExporter(lb).exportToImage(str(BASE/"before_preview/before_preview.png"), QgsLayoutExporter.ImageExportSettings())
print(f"[OK] Before: {Path(str(BASE/'before_preview/before_preview.png')).stat().st_size} bytes")

# 2. Filter East Asia
east_asia = ["China","Japan","South Korea","North Korea","Mongolia","Taiwan",
    "Vietnam","Laos","Cambodia","Thailand","Myanmar","Philippines","Indonesia",
    "Malaysia","Singapore","Brunei"]
c.setSubsetString(f'"SOVEREIGNT" IN ({",".join(repr(n) for n in east_asia)})')
print(f"[OK] Filtered to {c.featureCount()} countries")

# 3. Style: graduated by LABELRANK
from qgis.core import QgsGraduatedSymbolRenderer, QgsRendererRange
rng = QgsGraduatedSymbolRenderer("LABELRANK", [])
for i, v in enumerate([0,2,4,6,8]):
    sym = QgsFillSymbol.createSimple({"color": f"{200-i*20},{180-i*25},{255-i*10},180",
        "outline_color": "80,80,120,200", "outline_width": "0.6"})
    rng.addClassRange(QgsRendererRange(v, v+2, sym, f"Rank {v}-{v+2}"))
c.setRenderer(rng); c.triggerRepaint()

# 4. Style cities by scalerank
gr = QgsGraduatedSymbolRenderer("scalerank", [])
clrs = [(220,50,50),(240,140,40),(80,160,220),(120,200,100)]
for i, rk in enumerate(sorted(set(f.attribute("scalerank") for f in p.getFeatures() if f.attribute("scalerank") is not None))[:4]):
    sym = QgsMarkerSymbol.createSimple({"color": f"{clrs[i][0]},{clrs[i][1]},{clrs[i][2]}",
        "size": str(10-i*2), "outline_color": "0,0,0,120"})
    gr.addClassRange(QgsRendererRange(rk, rk+1, sym, f"Rank {rk}"))
p.setRenderer(gr); p.triggerRepaint()
print("[OK] Styles applied")

# 5. Layout
layout = QgsPrintLayout(proj); layout.initializeDefaults()
layout.setName("EastAsiaMap")

m = QgsLayoutItemMap(layout); m.setRect(QRectF(8,8,194,142)); m.setExtent(c.extent()); m.zoomToExtent(c.extent())
layout.addLayoutItem(m)

t = QgsLayoutItemLabel(layout); t.setText("East Asia: Countries & Major Cities (Natural Earth)")
t.setRect(QRectF(8,153,194,10)); layout.addLayoutItem(t)

lg = QgsLayoutItemLegend(layout); lg.setRect(QRectF(8,166,90,50)); layout.addLayoutItem(lg)

sb = QgsLayoutItemScaleBar(layout); sb.setRect(QRectF(108,166,80,8)); layout.addLayoutItem(sb)

# North arrow
try:
    svg = QgsApplication.defaultThemePath() + "/arrows/NorthArrow_02.svg"
    if Path(svg).exists():
        n = QgsLayoutItemPicture(layout); n.setPicturePath(svg); n.setRect(QRectF(188,170,12,12))
        layout.addLayoutItem(n)
except: pass

# 6. Export
exp = QgsLayoutExporter(layout)
fs = {"png": str(OUT/"east_asia_map.png"), "pdf": str(OUT/"east_asia_map.pdf"), "qgz": str(OUT/"east_asia_project.qgz")}
for fmt, path in fs.items():
    if fmt == "png": exp.exportToImage(path, QgsLayoutExporter.ImageExportSettings())
    elif fmt == "pdf": exp.exportToPdf(path, QgsLayoutExporter.PdfExportSettings())
    elif fmt == "qgz": proj.write(path)
    print(f"[OK] {fmt.upper()}: {path} ({Path(path).stat().st_size} bytes)")

# 7. Log
with open(str(BASE/"logs/auto_execution_log.json"), "w") as f:
    json.dump({"time": datetime.now().isoformat(), "data": "Natural Earth 1:110m",
        "filter": f"{c.featureCount()} countries", "crs": "EPSG:4326",
        "before_sha256": hashlib.sha256(open(str(RAW/"countries/ne_110m_admin_0_countries.shp"),"rb").read()).hexdigest(),
        "outputs": fs}, f, indent=2, ensure_ascii=False)

qgs.exitQgis()
print("\n=== AUTO DONE ===")
