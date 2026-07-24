"""FastMCP server exposing tools that drive a running QGIS Desktop session."""
from __future__ import annotations

import base64
from typing import Any

from mcp.server.fastmcp import FastMCP, Image

from .bridge import Bridge

mcp = FastMCP("qgis")
bridge = Bridge()


# --- introspection --------------------------------------------------------

@mcp.tool()
def ping() -> dict:
    """Check that the QGIS bridge plugin is reachable. Returns QGIS version."""
    return bridge.call("ping")


@mcp.tool()
def qgis_info() -> dict:
    """QGIS version, release name, profile path, and prefix path."""
    return bridge.call("qgis_info")


@mcp.tool()
def project_info() -> dict:
    """Info about the currently open QGIS project (filename, CRS, dirty flag,
    layer count, current canvas extent/scale/CRS)."""
    return bridge.call("project_info")


@mcp.tool()
def list_layers() -> list[dict]:
    """List all layers in the project: id, name, type, source, CRS, visibility,
    geometry type and feature count for vector layers."""
    return bridge.call("list_layers")


@mcp.tool()
def get_layer_info(layer_id: str) -> dict:
    """Detailed info for a single layer: extent, plus fields for vector layers
    or band/width/height for raster layers."""
    return bridge.call("get_layer_info", layer_id=layer_id)


@mcp.tool()
def get_features(
    layer_id: str,
    limit: int = 50,
    expression: str = "",
    include_geometry: bool = False,
    geometry_format: str = "wkt",
) -> dict:
    """Read features from a vector layer.

    expression: optional QGIS expression filter, e.g. "population > 10000".
    geometry_format: "wkt" or "geojson". Only used when include_geometry is True.
    """
    return bridge.call(
        "get_features",
        layer_id=layer_id,
        limit=limit,
        expression=expression or None,
        include_geometry=include_geometry,
        geometry_format=geometry_format,
    )


# --- project / layer mutation --------------------------------------------

@mcp.tool()
def load_project(path: str) -> dict:
    """Open a QGIS project file (.qgz / .qgs). Returns project_info on success."""
    return bridge.call("load_project", path=path)


@mcp.tool()
def save_project(path: str = "") -> dict:
    """Save the current project. Pass a path to save-as, or omit to save in place."""
    return bridge.call("save_project", path=path or None)


@mcp.tool()
def add_vector_layer(source: str, name: str = "", provider: str = "ogr") -> dict:
    """Add a vector layer to the project.

    source: data source URI — file path, GeoPackage URI, PostGIS URI, etc.
    provider: 'ogr' (file-based, default), 'postgres', 'memory', 'wfs', etc.
    """
    return bridge.call(
        "add_vector_layer", source=source, name=name or None, provider=provider
    )


@mcp.tool()
def add_raster_layer(source: str, name: str = "", provider: str = "gdal") -> dict:
    """Add a raster layer to the project.

    source: file path or URI.
    provider: 'gdal' (default), 'wms', 'wcs', 'xyz', etc.
    """
    return bridge.call(
        "add_raster_layer", source=source, name=name or None, provider=provider
    )


@mcp.tool()
def remove_layer(layer_id: str) -> dict:
    """Remove a layer from the project by id."""
    return bridge.call("remove_layer", layer_id=layer_id)


@mcp.tool()
def set_layer_visibility(layer_id: str, visible: bool) -> dict:
    """Show or hide a layer in the layer tree."""
    return bridge.call("set_layer_visibility", layer_id=layer_id, visible=visible)


# --- view ----------------------------------------------------------------

@mcp.tool()
def zoom_to_layer(layer_id: str) -> dict:
    """Zoom the map canvas to a layer's extent. Returns updated canvas state."""
    return bridge.call("zoom_to_layer", layer_id=layer_id)


@mcp.tool()
def zoom_to_full_extent() -> dict:
    """Zoom the map canvas to fit all layers."""
    return bridge.call("zoom_to_full_extent")


@mcp.tool()
def set_canvas_extent(xmin: float, ymin: float, xmax: float, ymax: float) -> dict:
    """Set the canvas extent to a bounding box (in the canvas CRS)."""
    return bridge.call(
        "set_canvas_extent", xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax
    )


@mcp.tool()
def screenshot(
    refresh: bool = False,
    max_kb: int = 1000,
    format: str = "auto",
    quality: int = 85,
    max_dimension: int = 0,
) -> Image:
    """Capture the QGIS map canvas, sized to fit under Claude Desktop's image cap.

    Default ('auto'): try PNG first. If the base64 payload would exceed max_kb,
    fall back to JPEG at `quality`, stepping quality down by 10 to a floor of 50.
    If even floor JPEG at full size doesn't fit (common with dense satellite
    basemaps), the bridge progressively downscales the canvas (0.75, 0.5, 0.35,
    0.25) and retries until it fits.

    max_dimension: optional one-shot upfront cap on the longer side, in pixels
    (e.g. 1920). Use 0 (default) to skip and rely on auto-fallback.
    format='png' forces lossless (may exceed max_kb).
    refresh=True redraws layers and processes events before capture.
    """
    result = bridge.call(
        "screenshot",
        refresh=refresh,
        max_kb=max_kb,
        format=format,
        quality=quality,
        max_dimension=max_dimension or None,
    )
    return Image(
        data=base64.b64decode(result["image_base64"]),
        format=result["format"],
    )


# --- processing ----------------------------------------------------------

@mcp.tool()
def list_processing_algorithms(filter: str = "") -> list[dict]:
    """List Processing algorithms. Pass `filter` to substring-match id or display name."""
    return bridge.call("list_processing_algorithms", filter=filter or None)


@mcp.tool()
def run_processing(algorithm: str, parameters: dict[str, Any] | None = None) -> dict:
    """Run a Processing algorithm by id (e.g. 'native:buffer').

    Outputs are returned as string reprs; use execute_code for typed access.
    """
    return bridge.call("run_processing", algorithm=algorithm, parameters=parameters or {})


# --- escape hatch --------------------------------------------------------

@mcp.tool()
def execute_code(code: str, return_var: str = "result") -> dict:
    """Execute arbitrary PyQGIS code inside QGIS.

    In scope: iface, processing, QgsProject, QgsApplication, QgsVectorLayer,
    QgsRasterLayer, QgsCoordinateReferenceSystem, QgsRectangle.

    Set a variable named `result` (or pass return_var) and its repr is returned.
    print() output is captured. User-code errors do NOT raise — they are
    reported via the `error`/`traceback` fields of the result.
    """
    return bridge.call("execute_code", code=code, return_var=return_var)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
