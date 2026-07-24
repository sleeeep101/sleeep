from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis

from .bridge_server import BridgeServer
from .handlers import Handlers

DEFAULT_PORT = 9876
SETTINGS_PORT_KEY = "qgis_mcp_bridge/port"
SETTINGS_AUTOSTART_KEY = "qgis_mcp_bridge/autostart"


class QgisMcpBridgePlugin:
    def __init__(self, iface):
        self.iface = iface
        self._server = None
        self._handlers = None
        self._action_toggle = None
        self._action_settings = None

    # --- QGIS plugin lifecycle -------------------------------------------------

    def initGui(self):
        self._action_toggle = QAction(QIcon(), "Start MCP Bridge", self.iface.mainWindow())
        self._action_toggle.setCheckable(True)
        self._action_toggle.triggered.connect(self._on_toggle)

        self.iface.addPluginToMenu("&MCP Bridge", self._action_toggle)
        self.iface.addToolBarIcon(self._action_toggle)

        if self._read_autostart():
            self._start()

    def unload(self):
        try:
            self._stop()
        finally:
            if self._action_toggle is not None:
                self.iface.removePluginMenu("&MCP Bridge", self._action_toggle)
                self.iface.removeToolBarIcon(self._action_toggle)
                self._action_toggle = None

    # --- actions ---------------------------------------------------------------

    def _on_toggle(self, checked: bool):
        if checked:
            self._start()
        else:
            self._stop()

    def _start(self):
        if self._server is not None:
            return
        port = self._read_port()
        self._handlers = Handlers(self.iface)
        self._server = BridgeServer(self._handlers.dispatch, parent=self.iface.mainWindow())
        try:
            actual = self._server.start(port)
        except Exception as e:
            self._server = None
            self._handlers = None
            self._action_toggle.setChecked(False)
            self.iface.messageBar().pushMessage(
                "MCP Bridge", f"Failed to start: {e}", level=Qgis.Critical, duration=10
            )
            return
        self._action_toggle.setChecked(True)
        self._action_toggle.setText("Stop MCP Bridge")
        self.iface.messageBar().pushMessage(
            "MCP Bridge",
            f"Listening on 127.0.0.1:{actual}",
            level=Qgis.Success,
            duration=5,
        )

    def _stop(self):
        if self._server is None:
            return
        try:
            self._server.stop()
        except Exception:
            pass
        self._server = None
        self._handlers = None
        if self._action_toggle is not None:
            self._action_toggle.setChecked(False)
            self._action_toggle.setText("Start MCP Bridge")
        self.iface.messageBar().pushMessage(
            "MCP Bridge", "Stopped", level=Qgis.Info, duration=3
        )

    # --- settings --------------------------------------------------------------

    def _read_port(self) -> int:
        s = QSettings()
        try:
            return int(s.value(SETTINGS_PORT_KEY, DEFAULT_PORT))
        except (TypeError, ValueError):
            return DEFAULT_PORT

    def _read_autostart(self) -> bool:
        s = QSettings()
        v = s.value(SETTINGS_AUTOSTART_KEY, True)
        if isinstance(v, bool):
            return v
        return str(v).lower() in ("true", "1", "yes")
