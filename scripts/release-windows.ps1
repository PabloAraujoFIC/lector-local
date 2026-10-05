$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
& .venv/Scripts/python.exe scripts/release.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
