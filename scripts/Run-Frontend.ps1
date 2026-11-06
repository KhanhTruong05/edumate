$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $projectPath 'frontend')
try { pnpm dev } finally { Pop-Location }
