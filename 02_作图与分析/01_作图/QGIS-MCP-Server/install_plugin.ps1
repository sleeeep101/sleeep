# Installs the QGIS MCP Bridge plugin into the QGIS user profile by creating
# a directory junction. Editing files in this repo immediately affects the
# installed plugin (no rebuild step). Re-run anytime to refresh the link.
#
# Junctions don't require admin rights or Windows Developer Mode.
# Run: powershell -ExecutionPolicy Bypass -File install_plugin.ps1

$ErrorActionPreference = "Stop"

$src = Join-Path $PSScriptRoot "plugin\qgis_mcp_bridge"
$pluginsDir = Join-Path $env:APPDATA "QGIS\QGIS3\profiles\default\python\plugins"
$dst = Join-Path $pluginsDir "qgis_mcp_bridge"

if (-not (Test-Path $src)) {
    throw "Source plugin not found at $src"
}

if (-not (Test-Path $pluginsDir)) {
    Write-Host "Creating $pluginsDir"
    New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null
}

if (Test-Path $dst) {
    Write-Host "Removing existing plugin at $dst"
    # Works for both junctions and regular directories.
    cmd /c rmdir /S /Q "`"$dst`""
}

Write-Host "Linking $dst -> $src"
cmd /c mklink /J "`"$dst`"" "`"$src`""

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  1. Open QGIS (<LOCAL_PATH>"
Write-Host "  2. Plugins -> Manage and Install Plugins... -> Installed -> tick 'QGIS MCP Bridge'"
Write-Host "  3. The bridge auto-starts; look for 'Listening on 127.0.0.1:9876' in the message bar."
