$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'build_overlay.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
