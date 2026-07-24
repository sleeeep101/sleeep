"""
Origin 桥接层：启动、退出、错误处理、导出、保存工程文件。

Usage (as module):
    from origin_bridge import OriginSession
    with OriginSession() as op:
        wb = op.new_workbook(...)
        ...

Usage (direct test):
    python origin_bridge.py          # dry-run, checks import only
    python origin_bridge.py --live   # start Origin, print version, exit
"""

import os
import sys
from contextlib import contextmanager

_ORIGIN_AVAILABLE = None


def is_origin_available() -> bool:
    """检查 originpro 是否可导入（幂等缓存）。"""
    global _ORIGIN_AVAILABLE
    if _ORIGIN_AVAILABLE is None:
        try:
            import originpro  # noqa: F401
            _ORIGIN_AVAILABLE = True
        except ImportError:
            _ORIGIN_AVAILABLE = False
    return _ORIGIN_AVAILABLE


def ensure_origin():
    """如果 originpro 不可用，抛出带指引的错误。"""
    if not is_origin_available():
        raise RuntimeError(
            "需要 Windows + Origin/OriginPro 2021+ + pip install originpro\n"
            "当前环境无法 import originpro，请确认：\n"
            "  1. 操作系统为 Windows\n"
            "  2. 已安装 Origin 或 OriginPro 2021+\n"
            "  3. 已运行 pip install originpro\n"
            "如果仅做开发/测试，可用 python origin_bridge.py 做 dry-run 检查。"
        )


class OriginSession:
    """管理 Origin 实例的生命周期。"""

    def __init__(self, show: bool = True):
        self.show = show
        self.op = None

    def __enter__(self):
        ensure_origin()
        import originpro as op
        op.set_show(self.show)
        self.op = op
        return op

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.op is not None:
            try:
                self.op.exit()
            except Exception:
                pass
        return False


def ensure_output_dir(path: str) -> str:
    """确保输出目录存在，返回绝对路径。"""
    os.makedirs(path, exist_ok=True)
    return os.path.abspath(path)


def export_graph(graph, output_path: str, formats: list):
    """将 graph 导出为指定格式。

    Args:
        graph: Origin graph 对象
        output_path: 无扩展名的基础路径
        formats: ['png', 'pdf', 'tif', 'svg', 'jpg', 'eps'] 的子集
    """
    fmt_map = {
        'png': 'png',
        'pdf': 'pdf',
        'tif': 'tif',
        'svg': 'svg',
        'jpg': 'jpg',
        'eps': 'eps',
    }
    for fmt in formats:
        if fmt not in fmt_map:
            print(f"[WARN] 不支持的导出格式: {fmt}，跳过")
            continue
        dest = f"{output_path}.{fmt}"
        graph.export(dest, fmt_map[fmt])
        print(f"[OK] 导出: {dest}")


def save_opju(project_path: str):
    """保存当前 Origin 工程为 .opju 文件。"""
    ensure_origin()
    import originpro as op
    op.save(project_path)
    print(f"[OK] 保存工程: {project_path}")


# ---------------------------------------------------------------------------
# CLI dry-run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    if '--live' in sys.argv:
        with OriginSession(show=True) as op:
            print(f"Origin 已启动，版本信息通过 op 对象可用。")
    else:
        if is_origin_available():
            print("[OK] originpro 可导入，环境就绪。")
        else:
            ensure_origin()
