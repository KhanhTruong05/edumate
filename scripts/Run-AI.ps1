$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Tạo .venv và cài requirements theo README trước.' }
Push-Location $projectPath
try { & $pythonPath -m uvicorn edumate_ai.service:create_app --factory --env-file ai/.env --host 127.0.0.1 --port 8001 } finally { Pop-Location }
