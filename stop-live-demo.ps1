param(
    [int[]]$Ports = @(8000, 3000)
)

$ErrorActionPreference = "SilentlyContinue"

foreach ($port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen
    foreach ($connection in $connections) {
        $processId = $connection.OwningProcess
        if ($processId) {
            $process = Get-Process -Id $processId
            Write-Host "Stopping $($process.ProcessName) on port $port (PID $processId)"
            Stop-Process -Id $processId -Force
        }
    }
}

Write-Host "Live demo ports stopped."
