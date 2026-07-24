"""Sync TCP client for the QGIS MCP bridge plugin.

Wire format must match plugin/qgis_mcp_bridge/bridge_server.py: 4-byte
big-endian length prefix, then UTF-8 JSON body.
"""
from __future__ import annotations

import json
import os
import socket
import struct
import threading
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


class BridgeError(RuntimeError):
    pass


class Bridge:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout: float = 30.0,
    ):
        self.host = host or os.environ.get("QGIS_MCP_HOST", DEFAULT_HOST)
        self.port = int(port or os.environ.get("QGIS_MCP_PORT", DEFAULT_PORT))
        self.timeout = timeout
        self._lock = threading.Lock()
        self._next_id = 0

    def call(self, command: str, **params: Any) -> Any:
        with self._lock:
            self._next_id += 1
            req_id = self._next_id
        req = {"id": req_id, "command": command, "params": params}
        body = json.dumps(req).encode("utf-8")
        frame = struct.pack(">I", len(body)) + body
        try:
            with socket.create_connection(
                (self.host, self.port), timeout=self.timeout
            ) as sock:
                sock.sendall(frame)
                resp = self._recv_frame(sock)
        except ConnectionRefusedError:
            raise BridgeError(
                f"Could not connect to the QGIS bridge at {self.host}:{self.port}. "
                f"Open QGIS Desktop, then enable and start the 'QGIS MCP Bridge' "
                f"plugin (Plugins menu → MCP Bridge → Start)."
            ) from None
        except socket.timeout:
            raise BridgeError(
                f"Timed out talking to the QGIS bridge at {self.host}:{self.port}"
            ) from None
        except OSError as e:
            raise BridgeError(
                f"Network error talking to QGIS bridge at {self.host}:{self.port}: {e}"
            ) from None

        if not resp.get("ok"):
            err = resp.get("error", "unknown error")
            tb = resp.get("traceback")
            msg = f"QGIS bridge error: {err}"
            if tb:
                msg += f"\n{tb}"
            raise BridgeError(msg)
        return resp.get("result")

    def _recv_frame(self, sock: socket.socket) -> dict:
        header = self._recv_exact(sock, 4)
        (length,) = struct.unpack(">I", header)
        body = self._recv_exact(sock, length)
        return json.loads(body.decode("utf-8"))

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise BridgeError("connection closed before full frame received")
            buf.extend(chunk)
        return bytes(buf)
