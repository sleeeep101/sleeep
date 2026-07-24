import json
import traceback

from qgis.PyQt.QtCore import QByteArray, QObject
from qgis.PyQt.QtNetwork import QHostAddress, QTcpServer

LENGTH_PREFIX = 4
MAX_FRAME_BYTES = 64 * 1024 * 1024


class BridgeServer(QObject):
    """Localhost-only TCP server that runs on the Qt main thread.

    Wire format: 4-byte big-endian length prefix, then UTF-8 JSON body.
    Request:  {"id": <int|null>, "command": "<name>", "params": {...}}
    Response: {"id": <id>, "ok": true,  "result": <any>}
              {"id": <id>, "ok": false, "error": "<msg>", "traceback": "..."}
    """

    def __init__(self, dispatch, parent=None):
        super().__init__(parent)
        self._dispatch = dispatch
        self._server = QTcpServer(self)
        self._buffers = {}
        self._server.newConnection.connect(self._on_new_connection)

    def start(self, port: int) -> int:
        if not self._server.listen(QHostAddress(QHostAddress.LocalHost), port):
            raise RuntimeError(
                f"could not listen on 127.0.0.1:{port}: {self._server.errorString()}"
            )
        return int(self._server.serverPort())

    def stop(self) -> None:
        for sock in list(self._buffers):
            try:
                sock.disconnectFromHost()
            except Exception:
                pass
        self._buffers.clear()
        self._server.close()

    def _on_new_connection(self):
        while self._server.hasPendingConnections():
            sock = self._server.nextPendingConnection()
            self._buffers[sock] = bytearray()
            sock.readyRead.connect(lambda s=sock: self._on_ready_read(s))
            sock.disconnected.connect(lambda s=sock: self._on_disconnect(s))

    def _on_ready_read(self, sock):
        buf = self._buffers.get(sock)
        if buf is None:
            return
        buf.extend(bytes(sock.readAll()))
        while True:
            if len(buf) < LENGTH_PREFIX:
                return
            length = int.from_bytes(buf[:LENGTH_PREFIX], "big")
            if length > MAX_FRAME_BYTES:
                self._send(sock, {"id": None, "ok": False, "error": "frame too large"})
                sock.disconnectFromHost()
                return
            if len(buf) < LENGTH_PREFIX + length:
                return
            payload = bytes(buf[LENGTH_PREFIX:LENGTH_PREFIX + length])
            del buf[:LENGTH_PREFIX + length]
            self._handle_frame(sock, payload)

    def _on_disconnect(self, sock):
        self._buffers.pop(sock, None)
        sock.deleteLater()

    def _handle_frame(self, sock, payload: bytes):
        req_id = None
        try:
            req = json.loads(payload.decode("utf-8"))
            req_id = req.get("id")
            command = req.get("command")
            params = req.get("params") or {}
            if not isinstance(command, str):
                raise ValueError("missing 'command'")
            if not isinstance(params, dict):
                raise ValueError("'params' must be an object")
            result = self._dispatch(command, params)
            self._send(sock, {"id": req_id, "ok": True, "result": result})
        except Exception as e:
            self._send(
                sock,
                {
                    "id": req_id,
                    "ok": False,
                    "error": f"{type(e).__name__}: {e}",
                    "traceback": traceback.format_exc(),
                },
            )

    def _send(self, sock, obj) -> None:
        data = json.dumps(obj, default=_json_default).encode("utf-8")
        frame = len(data).to_bytes(LENGTH_PREFIX, "big") + data
        sock.write(QByteArray(frame))
        sock.flush()


def _json_default(obj):
    # Best-effort fallback for QGIS objects that slip through.
    try:
        return str(obj)
    except Exception:
        return repr(obj)
