Write-Host "Killing processes on port 8000..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $processIds) {
        Write-Host "Killing PID: $procId" -ForegroundColor Cyan
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Done! Port 8000 is now free." -ForegroundColor Green
} else {
    Write-Host "No process found on port 8000." -ForegroundColor Green
}

Start-Sleep -Seconds 1

