"""Add north arrow to layout + generate JSON execution log. No external image dependency."""
import json
from pathlib import Path
from datetime import datetime
from qgis.core import QgsPrintLayout, QgsLayoutItemPicture, QgsLayoutItemLabel, QgsProject


def add_north_arrow(layout: QgsPrintLayout, x: float = 185, y: float = 5,
                    w: float = 15, h: float = 15) -> QgsLayoutItemLabel:
    """Add a north arrow placeholder (text-based, no external image).

    For a real north arrow SVG, QGIS has built-in symbols.
    This uses a text 'N ▲' placeholder when no SVG is available.
    If QGIS built-in SVG path is accessible, use QgsLayoutItemPicture instead.

    Args:
        layout: QgsPrintLayout instance
        x, y: Position (mm from top-left)
        w, h: Size (mm)
    """
    # Try built-in north arrow SVG first
    try:
        from qgis.core import QgsApplication, QgsLayoutItemPicture
        svg_path = QgsApplication.defaultThemePath() + "/arrows/NorthArrow_02.svg"
        if Path(svg_path).exists():
            pic = QgsLayoutItemPicture(layout)
            pic.setPicturePath(svg_path)
            from qgis.PyQt.QtCore import QRectF
            pic.setRect(QRectF(x, y, w, h))
            layout.addLayoutItem(pic)
            return pic
    except Exception:
        pass

    # Fallback: text-based north arrow
    label = QgsLayoutItemLabel(layout)
    label.setText("N\n▲")
    from qgis.PyQt.QtCore import QRectF
    label.setRect(QRectF(x, y, w, h))
    layout.addLayoutItem(label)
    return label


class ExecutionLogger:
    """Simple JSON execution logger for QGIS operations."""

    def __init__(self, log_path: str = None):
        self.log_path = Path(log_path or f"qgis_exec_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        self.entries = []
        self.start_time = datetime.now().isoformat()

    def log_step(self, step: int, action: str, status: str, details: str = "",
                 input_path: str = "", output_path: str = "", error: str = ""):
        entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "status": status.lower(),  # success | failed | skipped | pending
            "details": details,
            "input": input_path,
            "output": output_path,
            "error": error,
        }
        self.entries.append(entry)
        return entry

    def save(self):
        """Save log as JSON. Does not overwrite existing log."""
        out = self.log_path
        if out.exists():
            out = out.parent / f"{out.stem}_{datetime.now().strftime('%H%M%S')}{out.suffix}"
        data = {
            "session_start": self.start_time,
            "session_end": datetime.now().isoformat(),
            "total_steps": len(self.entries),
            "success": sum(1 for e in self.entries if e["status"] == "success"),
            "failed": sum(1 for e in self.entries if e["status"] == "failed"),
            "entries": self.entries,
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Execution log saved: {out}")
        return str(out)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  north-arrow: python add_north_arrow_and_log.py north <layout_name>")
        print("  log:         python add_north_arrow_and_log.py log <log_path>")
        sys.exit(1)

    op = sys.argv[1]
    if op == "north":
        layout_name = sys.argv[2] if len(sys.argv) > 2 else None
        layouts = QgsProject.instance().layoutManager().printLayouts()
        layout = layouts[0] if layouts else None
        if layout and layout_name:
            layout = QgsProject.instance().layoutManager().layoutByName(layout_name)
        if layout:
            add_north_arrow(layout)
            print(f"[OK] North arrow added to layout: {layout.name()}")
        else:
            print("[WARN] No layout found. Create a Print Layout first.")
    elif op == "log":
        logger = ExecutionLogger(sys.argv[2] if len(sys.argv) > 2 else None)
        logger.log_step(1, "init", "success", "Logger initialized")
        logger.save()
