$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendRoot = Join-Path $ProjectRoot "frontend"
$FrontendModules = Join-Path $FrontendRoot "node_modules"
$ViteEntry = Join-Path $FrontendModules "vite\bin\vite.js"
$BackendProcess = $null
$FrontendProcess = $null

try {
    if (-not (Test-Path $Python)) {
        throw "The existing virtual environment was not found at $Python. Create it using the project's setup instructions."
    }

    & $Python -c "import fastapi, multipart, uvicorn, websockets, vosk" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing missing backend requirements into the existing virtual environment..."
        & $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
        if ($LASTEXITCODE -ne 0) {
            throw "Backend dependency installation failed."
        }
    }

    $NodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
    $NpmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $NodeCommand -or -not $NpmCommand) {
        throw "Node.js and npm are required to run the React frontend."
    }

    if (-not (Test-Path $ViteEntry)) {
        Write-Host "Installing the frontend dependencies..."
        Push-Location $FrontendRoot
        try {
            & $NpmCommand.Source install --no-audit --no-fund
            if ($LASTEXITCODE -ne 0) {
                throw "Frontend dependency installation failed."
            }
        }
        finally {
            Pop-Location
        }
    }

    $BackendProcess = Start-Process `
        -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $ProjectRoot `
        -NoNewWindow `
        -PassThru

    $FrontendProcess = Start-Process `
        -FilePath $NodeCommand.Source `
        -ArgumentList @($ViteEntry, "--host", "127.0.0.1", "--port", "5173", "--strictPort") `
        -WorkingDirectory $FrontendRoot `
        -NoNewWindow `
        -PassThru

    $BackendUrl = "http://127.0.0.1:8000/api/health"
    $FrontendUrl = "http://127.0.0.1:5173"
    $BackendReady = $false
    $FrontendReady = $false

    for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
        if ($BackendProcess.HasExited -or $FrontendProcess.HasExited) {
            throw "The backend or frontend process exited during startup."
        }

        if (-not $BackendReady) {
            try {
                $null = Invoke-WebRequest -Uri $BackendUrl -TimeoutSec 2 -UseBasicParsing
                $BackendReady = $true
            }
            catch {
            }
        }

        if (-not $FrontendReady) {
            try {
                $null = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 2 -UseBasicParsing
                $FrontendReady = $true
            }
            catch {
            }
        }

        if ($BackendReady -and $FrontendReady) {
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $BackendReady -or -not $FrontendReady) {
        throw "The demo did not become ready in time. Check the startup output above."
    }

    Write-Host ""
    Write-Host "Ambient Clinical Listening demo is ready."
    Write-Host "Frontend: $FrontendUrl"
    Write-Host "Backend:  http://127.0.0.1:8000"
    Write-Host "Press Ctrl+C to stop both services."
    try {
        Start-Process $FrontendUrl
    }
    catch {
        Write-Warning "Could not open a browser automatically. Open $FrontendUrl manually."
    }

    while (-not $BackendProcess.HasExited -and -not $FrontendProcess.HasExited) {
        Start-Sleep -Seconds 1
    }

    throw "A demo service exited. See the process output above."
}
finally {
    foreach ($Process in @($FrontendProcess, $BackendProcess)) {
        if ($null -ne $Process -and -not $Process.HasExited) {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
