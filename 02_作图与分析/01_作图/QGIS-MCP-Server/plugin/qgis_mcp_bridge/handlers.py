"""Command handlers for the MCP bridge.

All methods run on the Qt main thread (QTcpServer dispatches there), so PyQGIS
calls are safe. Any uncaught exception is converted into an error response by
``BridgeServer``.
"""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import traceback

from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsFeatureRequest,
    QgsMapLayer,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)


_LAYER_TYPE_NAMES = {
    QgsMapLayer.VectorLayer: "vector",
    QgsMapLayer.RasterLayer: "raster",
}
for _attr, _name in (
    ("MeshLayer", "mesh"),
    ("VectorTileLayer", "vector_tile"),
    ("AnnotationLayer", "annotation"),
    ("PointCloudLayer", "point_cloud"),
    ("GroupLayer", "group"),
    ("PluginLayer", "plugin"),
):
    if hasattr(QgsMapLayer, _attr):
        _LAYER_TYPE_NAMES[getattr(QgsMapLayer, _attr)] = _name

_GEOM_TYPE_NAMES = {
    QgsWkbTypes.PointGeometry: "point",
    QgsWkbTypes.LineGeometry: "line",
    QgsWkbTypes.PolygonGeometry: "polygon",
    QgsWkbTypes.UnknownGeometry: "unknown",
    QgsWkbTypes.NullGeometry: "null",
}


class Handlers:
    def __init__(self, iface):
        self.iface = iface

    def dispatch(self, command: str, params: dict):
        method = getattr(self, f"cmd_{command}", None)
        if not callable(method):
            raise ValueError(f"unknown command: {command}")
        return method(**params)

    # --- introspection ---------------------------------------------------------

    def cmd_ping(self):
        return {"pong": True, "qgis_version": Qgis.QGIS_VERSION}

    def cmd_qgis_info(self):
        return {
            "qgis_version": Qgis.QGIS_VERSION,
            "qgis_release_name": Qgis.QGIS_RELEASE_NAME,
            "profile_path": QgsApplication.qgisSettingsDirPath(),
            "prefix_path": QgsApplication.prefixPath(),
        }

    def cmd_project_info(self):
        proj = QgsProject.instance()
        canvas = self.iface.mapCanvas()
        crs = proj.crs()
        return {
            "filename": proj.fileName() or None,
            "title": proj.title() or None,
            "crs": crs.authid() if crs.isValid() else None,
            "crs_description": crs.description() if crs.isValid() else None,
            "is_dirty": proj.isDirty(),
            "layer_count": len(proj.mapLayers()),
            "canvas": _canvas_state(canvas),
        }

    def cmd_list_layers(self):
        proj = QgsProject.instance()
        root = proj.layerTreeRoot()
        out = []
        for layer_id, layer in proj.mapLayers().items():
            node = root.findLayer(layer_id) if root else None
            visible = bool(node.isVisible()) if node else None
            out.append(_layer_summary(layer, visible=visible))
        return out

    def cmd_get_layer_info(self, layer_id: str):
        layer = _require_layer(layer_id)
        info = _layer_summary(layer)
        if isinstance(layer, QgsVectorLayer):
            info["fields"] = [
                {"name": f.name(), "type": f.typeName(), "length": f.length()}
                for f in layer.fields()
            ]
            ext = layer.extent()
            info["extent"] = _rect_to_dict(ext)
        elif isinstance(layer, QgsRasterLayer):
            info["band_count"] = layer.bandCount()
            info["width"] = layer.width()
            info["height"] = layer.height()
            ext = layer.extent()
            info["extent"] = _rect_to_dict(ext)
        return info

    def cmd_get_features(
        self,
        layer_id: str,
        limit: int = 50,
        expression: str | None = None,
        include_geometry: bool = False,
        geometry_format: str = "wkt",
    ):
        layer = _require_layer(layer_id)
        if not isinstance(layer, QgsVectorLayer):
            raise ValueError("get_features requires a vector layer")
        request = QgsFeatureRequest()
        if expression:
            request.setFilterExpression(expression)
        if isinstance(limit, int) and limit > 0:
            request.setLimit(limit)
        fields = layer.fields()
        out = []
        for feat in layer.getFeatures(request):
            out.append(
                _feature_to_dict(feat, fields, include_geometry, geometry_format)
            )
        return {"count": len(out), "features": out}

    # --- project / layer mutation ---------------------------------------------

    def cmd_load_project(self, path: str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        proj = QgsProject.instance()
        if not proj.read(path):
            raise RuntimeError(f"failed to read project: {path}")
        return self.cmd_project_info()

    def cmd_save_project(self, path: str | None = None):
        proj = QgsProject.instance()
        if path:
            ok = proj.write(path)
        else:
            if not proj.fileName():
                raise RuntimeError(
                    "project has no filename; pass a path to save-as"
                )
            ok = proj.write()
        if not ok:
            raise RuntimeError("failed to save project")
        return {"filename": proj.fileName() or None}

    def cmd_add_vector_layer(
        self, source: str, name: str | None = None, provider: str = "ogr"
    ):
        if name is None:
            name = os.path.splitext(os.path.basename(source))[0] or "vector"
        layer = QgsVectorLayer(source, name, provider)
        if not layer.isValid():
            raise RuntimeError(
                f"invalid vector layer: {source} (provider={provider})"
            )
        QgsProject.instance().addMapLayer(layer)
        return _layer_summary(layer)

    def cmd_add_raster_layer(
        self, source: str, name: str | None = None, provider: str = "gdal"
    ):
        if name is None:
            name = os.path.splitext(os.path.basename(source))[0] or "raster"
        layer = QgsRasterLayer(source, name, provider)
        if not layer.isValid():
            raise RuntimeError(
                f"invalid raster layer: {source} (provider={provider})"
            )
        QgsProject.instance().addMapLayer(layer)
        return _layer_summary(layer)

    def cmd_remove_layer(self, layer_id: str):
        layer = _require_layer(layer_id)
        QgsProject.instance().removeMapLayer(layer.id())
        return {"removed": layer_id}

    def cmd_set_layer_visibility(self, layer_id: str, visible: bool):
        layer = _require_layer(layer_id)
        node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if node is None:
            raise RuntimeError(f"no tree node for layer {layer_id}")
        node.setItemVisibilityChecked(bool(visible))
        return {"layer_id": layer_id, "visible": bool(visible)}

    # --- view ------------------------------------------------------------------

    def cmd_zoom_to_layer(self, layer_id: str):
        layer = _require_layer(layer_id)
        canvas = self.iface.mapCanvas()
        canvas.setExtent(layer.extent())
        canvas.refresh()
        return _canvas_state(canvas)

    def cmd_zoom_to_full_extent(self):
        canvas = self.iface.mapCanvas()
        canvas.zoomToFullExtent()
        canvas.refresh()
        return _canvas_state(canvas)

    def cmd_set_canvas_extent(
        self, xmin: float, ymin: float, xmax: float, ymax: float
    ):
        canvas = self.iface.mapCanvas()
        canvas.setExtent(QgsRectangle(xmin, ymin, xmax, ymax))
        canvas.refresh()
        return _canvas_state(canvas)

    def cmd_screenshot(
        self,
        refresh: bool = False,
        max_kb: int = 1000,
        format: str = "auto",
        quality: int = 85,
        min_quality: int = 50,
        max_dimension: int | None = None,
    ):
        """Capture the canvas, sized to fit under max_kb base64 chars.

        Pipeline:
          1. Optional upfront downsample to `max_dimension` longer side.
          2. Try PNG (skipped if format='jpeg').
          3. JPEG quality stepdown from `quality` to `min_quality`.
          4. Progressive auto-downscale (0.75, 0.5, 0.35, 0.25) retrying JPEG
             when even floor quality at full size exceeds the cap.

        Returns the first attempt that fits, or the smallest best-effort with
        a populated `note` field if nothing fits.
        """
        from qgis.PyQt.QtWidgets import QApplication

        canvas = self.iface.mapCanvas()
        if refresh:
            canvas.refreshAllLayers()
            QApplication.processEvents()
        pixmap = canvas.grab()
        original_size = (pixmap.width(), pixmap.height())

        if max_dimension and max(pixmap.width(), pixmap.height()) > int(max_dimension):
            pixmap = _scale_pixmap_to_longest(pixmap, int(max_dimension))

        cap = max(1, int(max_kb)) * 1024
        fmt = (format or "auto").lower()
        if fmt == "jpg":
            fmt = "jpeg"
        if fmt not in ("auto", "png", "jpeg"):
            raise ValueError(
                f"format must be 'auto', 'png', or 'jpeg' (got {format!r})"
            )

        notes = []
        if pixmap.size() != _qsize(*original_size):
            notes.append(
                f"pre-scaled from {original_size[0]}x{original_size[1]} "
                f"to {pixmap.width()}x{pixmap.height()} (max_dimension)"
            )

        if fmt in ("auto", "png"):
            png_bytes = _pixmap_to_bytes(pixmap, "PNG")
            png_b64 = base64.b64encode(png_bytes).decode("ascii")
            if fmt == "png" or len(png_b64) <= cap:
                note = None
                if fmt == "png" and len(png_b64) > cap:
                    note = f"forced PNG is {len(png_b64) // 1024}kb, exceeds max_kb"
                if notes:
                    note = "; ".join(notes + ([note] if note else []))
                return _screenshot_result(
                    "png", None, png_b64,
                    pixmap.width(), pixmap.height(),
                    original_size, note,
                )
            notes.append(
                f"PNG was {len(png_b64) // 1024}kb b64, exceeded max_kb={max_kb}"
            )

        # JPEG sweep: full-size quality stepdown, then auto-downscale.
        q_steps = _quality_steps(quality, min_quality)
        attempts: list[tuple[float, int]] = [(1.0, q) for q in q_steps]
        for scale in (0.75, 0.5, 0.35, 0.25):
            attempts.append((scale, max(int(quality), min_quality)))
            attempts.append((scale, min_quality))

        best = None  # (scale, q, b64, w, h)
        for scale, q in attempts:
            scaled = pixmap if scale >= 1.0 else _scale_pixmap_factor(pixmap, scale)
            if scaled.width() < 64 or scaled.height() < 64:
                continue
            jpeg_bytes = _pixmap_to_bytes(scaled, "JPEG", q)
            b64 = base64.b64encode(jpeg_bytes).decode("ascii")
            attempt = (scale, q, b64, scaled.width(), scaled.height())
            if best is None or len(b64) < len(best[2]):
                best = attempt
            if len(b64) <= cap:
                if scale < 1.0:
                    notes.append(
                        f"downscaled by {scale:g} to {scaled.width()}x{scaled.height()}"
                    )
                return _screenshot_result(
                    "jpeg", q, b64, scaled.width(), scaled.height(),
                    original_size, "; ".join(notes) or None,
                )

        # Nothing fit — return smallest attempt with a warning.
        scale, q, b64, w, h = best
        notes.append(
            f"could not fit under {max_kb}kb; returning {len(b64) // 1024}kb "
            f"at scale {scale:g}, quality {q}"
        )
        return _screenshot_result(
            "jpeg", q, b64, w, h, original_size, "; ".join(notes),
        )

    # --- processing ------------------------------------------------------------

    def cmd_list_processing_algorithms(self, filter: str | None = None):
        reg = QgsApplication.processingRegistry()
        out = []
        needle = filter.lower() if filter else None
        for alg in reg.algorithms():
            ident = alg.id()
            label = alg.displayName()
            if needle and needle not in ident.lower() and needle not in label.lower():
                continue
            out.append(
                {
                    "id": ident,
                    "display_name": label,
                    "group": alg.group(),
                    "provider": alg.provider().id() if alg.provider() else None,
                }
            )
        out.sort(key=lambda a: a["id"])
        return out

    def cmd_run_processing(self, algorithm: str, parameters: dict | None = None):
        import processing

        result = processing.run(algorithm, parameters or {})
        return {k: _safe_repr(v, limit=2000) for k, v in result.items()}

    # --- escape hatch ----------------------------------------------------------

    def cmd_execute_code(self, code: str, return_var: str = "result"):
        """Run an arbitrary Python snippet in a namespace preloaded with PyQGIS.

        Captures stdout/stderr. If the namespace contains ``return_var`` after
        execution, its repr is returned. The bridge call itself succeeds even
        when the user code raises — the error appears in ``error``/``traceback``.
        """
        import processing

        ns = {
            "__name__": "__qgis_mcp_exec__",
            "iface": self.iface,
            "processing": processing,
            "QgsProject": QgsProject,
            "QgsApplication": QgsApplication,
            "QgsVectorLayer": QgsVectorLayer,
            "QgsRasterLayer": QgsRasterLayer,
            "QgsCoordinateReferenceSystem": QgsCoordinateReferenceSystem,
            "QgsRectangle": QgsRectangle,
        }
        out, err = io.StringIO(), io.StringIO()
        error = None
        tb = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                exec(code, ns)
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                tb = traceback.format_exc()
        value = ns.get(return_var)
        return {
            "success": error is None,
            "error": error,
            "traceback": tb,
            "stdout": out.getvalue(),
            "stderr": err.getvalue(),
            "value": _safe_repr(value) if value is not None else None,
        }


# --- helpers ------------------------------------------------------------------

def _pixmap_to_bytes(pixmap, fmt: str, quality: int = -1) -> bytes:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    try:
        if not pixmap.save(buf, fmt, quality):
            raise RuntimeError(f"failed to encode canvas as {fmt}")
        return bytes(ba)
    finally:
        buf.close()


def _screenshot_result(fmt, quality, b64, width, height, original_size, note):
    out = {
        "format": fmt,
        "quality": quality,
        "size_b64": len(b64),
        "size_kb": round(len(b64) / 1024, 1),
        "width": width,
        "height": height,
        "image_base64": b64,
        "note": note,
    }
    if original_size and tuple(original_size) != (width, height):
        out["original_size"] = list(original_size)
    return out


def _quality_steps(start: int, floor: int, step: int = 10) -> list[int]:
    s = max(1, min(100, int(start)))
    f = max(1, min(s, int(floor)))
    out = []
    q = s
    while q > f:
        out.append(q)
        q -= step
    out.append(f)
    return out


def _scale_pixmap_factor(pixmap, factor: float):
    new_w = max(1, int(pixmap.width() * factor))
    new_h = max(1, int(pixmap.height() * factor))
    from qgis.PyQt.QtCore import Qt

    return pixmap.scaled(
        new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )


def _scale_pixmap_to_longest(pixmap, longest: int):
    from qgis.PyQt.QtCore import Qt

    if pixmap.width() >= pixmap.height():
        return pixmap.scaledToWidth(int(longest), Qt.SmoothTransformation)
    return pixmap.scaledToHeight(int(longest), Qt.SmoothTransformation)


def _qsize(w: int, h: int):
    from qgis.PyQt.QtCore import QSize

    return QSize(w, h)


def _require_layer(layer_id: str):
    layer = QgsProject.instance().mapLayer(layer_id)
    if layer is None:
        raise ValueError(f"no layer with id {layer_id}")
    return layer


def _layer_summary(layer, visible=None):
    info = {
        "id": layer.id(),
        "name": layer.name(),
        "type": _LAYER_TYPE_NAMES.get(layer.type(), "unknown"),
        "source": layer.source(),
        "crs": layer.crs().authid() if layer.crs().isValid() else None,
        "is_valid": layer.isValid(),
    }
    if visible is not None:
        info["visible"] = visible
    if isinstance(layer, QgsVectorLayer):
        try:
            geom_type = QgsWkbTypes.geometryType(layer.wkbType())
            info["geometry_type"] = _GEOM_TYPE_NAMES.get(geom_type, "unknown")
            info["wkb_type"] = QgsWkbTypes.displayString(layer.wkbType())
        except Exception:
            pass
        try:
            info["feature_count"] = layer.featureCount()
        except Exception:
            pass
    return info


def _rect_to_dict(rect):
    if rect is None or rect.isEmpty():
        return None
    return {
        "xmin": rect.xMinimum(),
        "ymin": rect.yMinimum(),
        "xmax": rect.xMaximum(),
        "ymax": rect.yMaximum(),
    }


def _canvas_state(canvas):
    ext = canvas.extent()
    crs = canvas.mapSettings().destinationCrs()
    return {
        "extent": _rect_to_dict(ext),
        "crs": crs.authid() if crs.isValid() else None,
        "scale": canvas.scale(),
        "rotation": canvas.rotation(),
        "size": [canvas.width(), canvas.height()],
    }


def _feature_to_dict(feat, fields, include_geometry, geometry_format):
    attrs = {}
    for i, field in enumerate(fields):
        attrs[field.name()] = _serialize_value(feat.attribute(i))
    out = {"id": feat.id(), "attributes": attrs}
    if include_geometry:
        geom = feat.geometry()
        if geom is None or geom.isNull():
            out["geometry"] = None
        elif geometry_format == "geojson":
            try:
                out["geometry"] = json.loads(geom.asJson())
            except Exception:
                out["geometry_wkt"] = geom.asWkt()
        else:
            out["geometry_wkt"] = geom.asWkt()
    return out


def _serialize_value(v):
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    try:
        from qgis.PyQt.QtCore import QDate, QDateTime, QTime, QVariant

        if isinstance(v, QVariant) and v.isNull():
            return None
        if isinstance(v, QDateTime):
            return v.toString("yyyy-MM-ddTHH:mm:ss")
        if isinstance(v, QDate):
            return v.toString("yyyy-MM-dd")
        if isinstance(v, QTime):
            return v.toString("HH:mm:ss")
    except Exception:
        pass
    try:
        return str(v)
    except Exception:
        return repr(v)


def _safe_repr(value, limit: int = 4000):
    try:
        s = repr(value)
    except Exception as e:
        s = f"<repr error: {e}>"
    if len(s) > limit:
        s = s[:limit] + f"... (truncated, full length {len(s)})"
    return s
