"""Save QGIS project and optionally package with data into a zip archive."""
from pathlib import Path
import shutil
from qgis.core import QgsProject


def save_project(project_path: str) -> str:
    """Save the current QGIS project."""
    path = Path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    result = QgsProject.instance().write(str(path))
    if not result:
        raise Exception(f"Failed to save project: {project_path}")
    print(f"[OK] Project saved: {project_path}")
    return str(path)


def package_project(project_path: str, output_zip: str) -> str:
    """Package a QGIS project directory into a zip archive.

    Args:
        project_path: Path to the .qgz project file
        output_zip: Path for output .zip (without extension)
    """
    proj = Path(project_path)
    if not proj.exists():
        raise FileNotFoundError(f"Project not found: {project_path}")

    out = Path(output_zip)
    shutil.make_archive(str(out.with_suffix("")), "zip", str(proj.parent))
    print(f"[OK] Packaged: {output_zip}.zip")
    return f"{output_zip}.zip"


def get_project_info():
    """Print basic project info."""
    project = QgsProject.instance()
    print("=== Project Info ===")
    print(f"  File: {project.fileName() or '(unsaved)'}")
    print(f"  CRS: {project.crs().authid()}")
    print(f"  Layers: {len(project.mapLayers())}")
    for lid, layer in project.mapLayers().items():
        print(f"    - {layer.name()} ({layer.type()})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  save:  python project_save_and_package.py save <project_path>")
        print("  pack:  python project_save_and_package.py pack <project_path> <output_zip>")
        print("  info:  python project_save_and_package.py info")
        sys.exit(1)

    op = sys.argv[1]
    if op == "save":
        save_project(sys.argv[2])
    elif op == "pack":
        package_project(sys.argv[2], sys.argv[3])
    elif op == "info":
        get_project_info()
