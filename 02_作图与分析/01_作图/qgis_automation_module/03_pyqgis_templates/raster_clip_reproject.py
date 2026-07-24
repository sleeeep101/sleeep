"""Raster operations: clip by mask, reproject via GDAL Processing."""
from pathlib import Path
import processing


def check_input(*paths):
    for p in paths:
        if not Path(p).exists():
            raise FileNotFoundError(f"Input not found: {p}")


def clip_raster(raster_path: str, mask_path: str, output_path: str) -> str:
    """Clip raster by mask layer (vector boundary)."""
    check_input(raster_path, mask_path)
    result = processing.run("gdal:cliprasterbymasklayer", {
        "INPUT": raster_path,
        "MASK": mask_path,
        "OUTPUT": output_path,
    })
    print(f"[OK] Clipped raster: {output_path}")
    return result["OUTPUT"]


def reproject_raster(raster_path: str, target_crs: str, output_path: str) -> str:
    """Reproject raster to target CRS (EPSG:xxxx)."""
    check_input(raster_path)
    result = processing.run("gdal:warpreproject", {
        "INPUT": raster_path,
        "SOURCE_CRS": None,
        "TARGET_CRS": target_crs,
        "OUTPUT": output_path,
    })
    print(f"[OK] Reprojected to {target_crs}: {output_path}")
    return result["OUTPUT"]


def hillshade(dem_path: str, output_path: str, azimuth: float = 315, angle: float = 45) -> str:
    """Generate hillshade from DEM."""
    check_input(dem_path)
    result = processing.run("native:hillshade", {
        "INPUT": dem_path,
        "Z_FACTOR": 1.0,
        "AZIMUTH": azimuth,
        "V_ANGLE": angle,
        "OUTPUT": output_path,
    })
    print(f"[OK] Hillshade: {output_path}")
    return result["OUTPUT"]


def slope(dem_path: str, output_path: str) -> str:
    """Calculate slope from DEM."""
    check_input(dem_path)
    result = processing.run("native:slope", {
        "INPUT": dem_path,
        "OUTPUT": output_path,
    })
    print(f"[OK] Slope: {output_path}")
    return result["OUTPUT"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  clip:    python raster_clip_reproject.py clip <raster> <mask> <output>")
        print("  reproj:  python raster_clip_reproject.py reproj <raster> <EPSG:xxxx> <output>")
        print("  hillshade: python raster_clip_reproject.py hillshade <dem> <output>")
        print("  slope:   python raster_clip_reproject.py slope <dem> <output>")
        sys.exit(1)
    op = sys.argv[1]
    if op == "clip":
        clip_raster(sys.argv[2], sys.argv[3], sys.argv[4])
    elif op == "reproj":
        reproject_raster(sys.argv[2], sys.argv[3], sys.argv[4])
    elif op == "hillshade":
        hillshade(sys.argv[2], sys.argv[3])
    elif op == "slope":
        slope(sys.argv[2], sys.argv[3])
