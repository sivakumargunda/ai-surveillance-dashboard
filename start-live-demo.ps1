param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 3000,
    [string]$CorsOrigins = "http://localhost:3000,http://127.0.0.1:3000"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Logs = Join-Path $Root "artifacts\logs"
$Frontend = Join-Path $Root "frontend"

New-Item -ItemType Directory -Force $Logs | Out-Null

function Test-PortOpen {
    param([int]$Port)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $connected = $result.AsyncWaitHandle.WaitOne(250, $false)
        if ($connected) {
            $client.EndConnect($result)
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-Health {
    param(
        [string]$Url,
        [int]$Seconds = 45
    )

    for ($i = 0; $i -lt $Seconds; $i++) {
        try {
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec 2
            if ($response.status -eq "ok") {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    return $false
}

if (Test-PortOpen $ApiPort) {
    Write-Host "API already appears to be running on port $ApiPort"
}
else {
    $env:AUTO_START_CAMERAS = "true"
    $env:SHOW_WINDOW = "false"
    $env:CORS_ORIGINS = $CorsOrigins
    $env:PORT = "$ApiPort"

    $apiOut = Join-Path $Logs "live-demo-api-output.log"
    $apiErr = Join-Path $Logs "live-demo-api-error.log"

    Write-Host "Starting Sentinel API on http://localhost:$ApiPort ..."
    Start-Process `
        -FilePath python `
        -ArgumentList "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "$ApiPort" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $apiOut `
        -RedirectStandardError $apiErr | Out-Null
}

if (Wait-Health "http://127.0.0.1:$ApiPort/health") {
    Write-Host "API health check passed."
}
else {
    Write-Warning "API health check did not pass. Check artifacts\logs\live-demo-api-error.log"
}

if (Test-PortOpen $FrontendPort) {
    Write-Host "Frontend already appears to be running on port $FrontendPort"
}
else {
    $env:PORT = "$FrontendPort"
    $env:REACT_APP_API_BASE_URL = "http://localhost:$ApiPort"

    $webOut = Join-Path $Logs "live-demo-frontend-output.log"
    $webErr = Join-Path $Logs "live-demo-frontend-error.log"
    $npm = if ($IsWindows -or $env:OS -like "*Windows*") { "npm.cmd" } else { "npm" }

    Write-Host "Starting Sentinel dashboard on http://localhost:$FrontendPort ..."
    Start-Process `
        -FilePath $npm `
        -ArgumentList "start" `
        -WorkingDirectory $Frontend `
        -WindowStyle Hidden `
        -RedirectStandardOutput $webOut `
        -RedirectStandardError $webErr | Out-Null
}

Write-Host ""
Write-Host "Sentinel live demo is starting."
Write-Host "Dashboard: http://localhost:$FrontendPort"
Write-Host "API:       http://localhost:$ApiPort"
Write-Host "API Docs:  http://localhost:$ApiPort/docs"
Write-Host "Health:    http://localhost:$ApiPort/health"
Write-Host ""
Write-Host "Logs:"
Write-Host "  artifacts\logs\live-demo-api-output.log"
Write-Host "  artifacts\logs\live-demo-api-error.log"
Write-Host "  artifacts\logs\live-demo-frontend-output.log"
Write-Host "  artifacts\logs\live-demo-frontend-error.log"
