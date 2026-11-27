$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run uv sync --frozen first.' }
Set-Location -LiteralPath $projectRoot
$backendListeners = @(Get-NetTCPConnection -LocalPort 8099 -State Listen -ErrorAction SilentlyContinue)
foreach ($listener in $backendListeners) {
    $backendProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
    $belongsToProject = $false
    for ($depth = 0; $depth -lt 4 -and $backendProcess; $depth++) {
        if ($backendProcess.ExecutablePath -and $backendProcess.ExecutablePath.StartsWith($projectRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            $belongsToProject = $true
            break
        }
        $backendProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($backendProcess.ParentProcessId)"
    }
    if (-not $belongsToProject) {
        throw "Port 8099 is used by another project (PID $($listener.OwningProcess)). Stop that backend before running this demo."
    }
}
& $pythonPath scripts/setup_demo.py
if ($LASTEXITCODE -ne 0) { throw 'Could not prepare local settings.' }
docker compose up -d --wait --wait-timeout 120 postgres
if ($LASTEXITCODE -ne 0) { throw 'Could not start PostgreSQL. Check Docker Desktop.' }
if (-not (Get-NetTCPConnection -LocalPort 8099 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8099') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.backend.stdout.log') -RedirectStandardError (Join-Path $projectRoot '.backend.stderr.log')
}
if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
    $frontendPath = Join-Path $projectRoot 'fe'
    Start-Process -FilePath 'npm.cmd' -ArgumentList @('run', 'dev', '--', '--host', 'localhost', '--port', '5173', '--strictPort') -WorkingDirectory $frontendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.frontend.stdout.log') -RedirectStandardError (Join-Path $projectRoot '.frontend.stderr.log')
}
Write-Output 'Frontend: http://localhost:5173'
Write-Output 'Admin credentials: .env -> INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD'
