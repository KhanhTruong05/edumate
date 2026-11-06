$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Tạo .venv và cài requirements theo README trước.' }
Push-Location (Join-Path $projectPath 'backend')
try { & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 } finally { Pop-Location }
