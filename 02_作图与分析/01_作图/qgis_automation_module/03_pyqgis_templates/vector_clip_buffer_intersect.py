"""Vector operations: clip, buffer, intersection via QGIS Processing."""
from pathlib import Path
import processing


def check_input(*paths):
    for p in paths:
        if not Path(p).exists():
            raise FileNotFoundError(f"Input not found: {p}")


def clip_layer(input_path: str, overlay_path: str, output_path: str) -> str:
    """Clip input layer by overlay boundary."""
    check_input(input_path, overlay_path)
    result = processing.run("native:clip", {
        "INPUT": input_path,
        "OVERLAY": overlay_path,
        "OUTPUT": output_path,
    })
    print(f"[OK] Clipped: {output_path}")
    return result["OUTPUT"]


def buffer_layer(input_path: str, distance: float, output_path: str) -> str:
    """Create buffer around input features."""
    check_input(input_path)
    result = processing.run("native:buffer", {
        "INPUT": input_path,
        "DISTANCE": distance,
        "OUTPUT": output_path,
    })
    print(f"[OK] Buffer ({distance}m): {output_path}")
    return result["OUTPUT"]


def intersect_layers(input_path: str, overlay_path: str, output_path: str) -> str:
    """Intersect two vector layers."""
    check_input(input_path, overlay_path)
    result = processing.run("native:intersection", {
        "INPUT": input_path,
        "OVERLAY": overlay_path,
        "OUTPUT": output_path,
    })
    print(f"[OK] Intersection: {output_path}")
    return result["OUTPUT"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  clip:    python vector_clip_buffer_intersect.py clip <input> <overlay> <output>")
        print("  buffer:  python vector_clip_buffer_intersect.py buffer <input> <distance_m> <output>")
        print("  inter:   python vector_clip_buffer_intersect.py inter <input> <overlay> <output>")
        sys.exit(1)

    op = sys.argv[1]
    if op == "clip":
        clip_layer(sys.argv[2], sys.argv[3], sys.argv[4])
    elif op == "buffer":
        buffer_layer(sys.argv[2], float(sys.argv[3]), sys.argv[4])
    elif op == "inter":
        intersect_layers(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown operation: {op}")
