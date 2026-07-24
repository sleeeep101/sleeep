# QGIS MCP

An MCP server that lets Claude (Claude Code or Claude Desktop) drive a running
QGIS Desktop session - list and add layers, query features, run Processing
algorithms, screenshot the canvas, and execute arbitrary PyQGIS snippets.

## Architecture

```
   Claude Code  / Claude Desktop
            |
            v   stdio (MCP)
   +---------------------+        TCP 127.0.0.1:9876        +---------------------+
   |   qgis_mcp server   |  <----- length-prefixed JSON ---> | QGIS MCP Bridge     |
   |   (Python, FastMCP) |                                   | plugin (inside QGIS)|
   +---------------------+                                   +----------+----------+
                                                                        |
                                                                        v
                                                                     PyQGIS
```

Two pieces:

- **`plugin/qgis_mcp_bridge/`** - a QGIS plugin that opens a localhost-only TCP
  server inside QGIS and dispatches JSON commands to PyQGIS on the Qt main thread.
- **`mcp_server/`** - a Python package that exposes MCP tools and forwards calls
  to the bridge over TCP.

The plugin only listens on `127.0.0.1`, so nothing is exposed to the network.

## Install

### 1. Install the QGIS plugin

```powershell
powershell -ExecutionPolicy Bypass -File install_plugin.ps1
```

This creates a directory junction at
`%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\qgis_mcp_bridge` pointing
back to this repo, so edits to the plugin source apply immediately (just toggle
the plugin off/on in QGIS, or use the *Plugin Reloader* plugin).

Then in QGIS:

1. Open `<LOCAL_PATH>`.
2. **Plugins → Manage and Install Plugins…**
3. **Settings** tab → tick **Show also experimental plugins**.
4. **Installed** tab → tick **QGIS MCP Bridge**.
5. The bridge auto-starts. You should see `Listening on 127.0.0.1:9876` in the
   message bar at the top of the canvas, and a toolbar button to start/stop it.

### 2. Install the MCP server

The recommended runner is [`uv`](https://docs.astral.sh/uv/) - it doesn't need
QGIS's bundled Python and resolves dependencies on the fly.

```powershell
# from the mcp_server directory:
cd mcp_server
uv sync
```

Or with a system Python:

```powershell
cd mcp_server
python -m pip install -e .
```

Quick smoke test (with QGIS running and the plugin enabled):

```powershell
uv run --directory mcp_server python -c "from qgis_mcp.bridge import Bridge; print(Bridge().call('ping'))"
```

You should get something like `{'pong': True, 'qgis_version': '3.44.x-...'}`.

### 3. Wire it up to Claude

> In the snippets below, replace `<absolute-path-to-qgis_mcp-repo>` with the
> absolute path where you cloned this repo (e.g. `<LOCAL_PATH>` or
> `<LOCAL_PATH>`). Forward slashes work on Windows in JSON.

#### Claude Code (this project)

Copy `.mcp.json.example` to `.mcp.json` in the project root and edit the path:

```json
{
  "mcpServers": {
    "qgis": {
      "command": "uv",
      "args": [
        "--directory",
        "<absolute-path-to-qgis_mcp-repo>/mcp_server",
        "run",
        "qgis-mcp"
      ]
    }
  }
}
```

Or register it at user scope so it follows you across projects:

```powershell
claude mcp add qgis -s user -- uv --directory "<absolute-path-to-qgis_mcp-repo>/mcp_server" run qgis-mcp
```

Restart Claude Code. `/mcp` should list `qgis` as connected.

#### Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "qgis": {
      "command": "uv",
      "args": [
        "--directory",
        "<absolute-path-to-qgis_mcp-repo>/mcp_server",
        "run",
        "qgis-mcp"
      ]
    }
  }
}
```

Quit and relaunch Claude Desktop. The hammer icon in the chat input should now
list the QGIS tools.

## Tools

| Tool | What it does |
|---|---|
| `ping` | Verify the bridge is reachable. |
| `qgis_info` | QGIS version, profile path, prefix path. |
| `project_info` | Current project metadata + canvas state. |
| `list_layers` | All layers (id, name, type, CRS, visibility, feature count). |
| `get_layer_info` | Detailed info for one layer (fields/extent/etc). |
| `get_features` | Read features from a vector layer with optional expression filter. |
| `load_project` | Open a `.qgz`/`.qgs` file. |
| `save_project` | Save in place or save-as. |
| `add_vector_layer` | Add a vector layer by source URI + provider. |
| `add_raster_layer` | Add a raster layer by source URI + provider. |
| `remove_layer` | Remove a layer by id. |
| `set_layer_visibility` | Toggle a layer in the layer tree. |
| `zoom_to_layer` | Fit canvas to a layer's extent. |
| `zoom_to_full_extent` | Fit canvas to all layers. |
| `set_canvas_extent` | Set canvas to a bounding box. |
| `screenshot` | PNG of the current canvas. Auto-falls back to JPEG with progressive quality stepdown, then progressive downscale (0.75→0.25), to stay under `max_kb` (default 1000 - Claude Desktop's image cap). Pass `max_dimension=1920` for an upfront size cap, or `format='png'` to force lossless. |
| `list_processing_algorithms` | List Processing algorithms (filter by substring). |
| `run_processing` | Run a Processing algorithm by id. |
| `execute_code` | Run arbitrary PyQGIS in QGIS. Returns stdout/stderr/value. |

## Configuration

Override host/port via environment variables on the MCP server side:

- `QGIS_MCP_HOST` (default `127.0.0.1`)
- `QGIS_MCP_PORT` (default `9876`)

The plugin port lives in QGIS settings under `qgis_mcp_bridge/port`. Set it via
the Python console:

```python
from qgis.PyQt.QtCore import QSettings
QSettings().setValue("qgis_mcp_bridge/port", 9876)
```

## Troubleshooting

- **`Could not connect to the QGIS bridge…`** - QGIS isn't running, the plugin
  isn't enabled, or the bridge is stopped. Check the toolbar toggle and the
  message bar.
- **Plugin doesn't appear in the list** - make sure *Show also experimental
  plugins* is ticked in the Plugin Manager **Settings** tab.
- **`address already in use`** on bridge start - another QGIS instance is
  already running the bridge on the same port. Stop one or change the port.
- **Edits to plugin code aren't picked up** - install the *Plugin Reloader*
  plugin (it gives you a one-click reload), or toggle the plugin off/on.
- **Slow `screenshot` after adding a layer** - pass `refresh=True` to force a
  redraw before capture.
- **Screenshot looks washed out / JPEG-y** - the bridge fell back to JPEG to
  stay under `max_kb`. Lower the QGIS window/canvas size, raise `max_kb`, or
  pass `format='png'` if you don't care about the size cap.
- **Screenshot came back smaller than the canvas** - auto-downscale kicked in
  to fit under `max_kb` (typical with dense satellite basemaps). The result
  reports `original_size` and a `note`. Use `max_dimension` for predictable
  upfront sizing, or raise `max_kb` if your client supports larger payloads.

## Layout

```
qgis_mcp/
├── README.md
├── install_plugin.ps1
├── plugin/
│   └── qgis_mcp_bridge/        # QGIS plugin (runs inside QGIS)
│       ├── __init__.py
│       ├── metadata.txt
│       ├── plugin.py           # plugin lifecycle + toolbar action
│       ├── bridge_server.py    # QTcpServer, length-prefixed JSON framing
│       └── handlers.py         # PyQGIS command implementations
└── mcp_server/                 # MCP server (separate Python process)
    ├── pyproject.toml
    └── src/qgis_mcp/
        ├── __init__.py
        ├── __main__.py
        ├── bridge.py           # sync TCP client
        └── server.py           # FastMCP tool definitions
```
