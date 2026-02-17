# 强制清理所有 Python 进程（慎用！）
Write-Host "Force killing all Python processes..." -ForegroundColor Red

Get-Process python* -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Killing: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Yellow
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

Write-Host "`nChecking port 8000..." -ForegroundColor Cyan
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    Write-Host "WARNING: Port 8000 still has connections (might be TIME_WAIT)" -ForegroundColor Yellow
} else {
    Write-Host "Port 8000 is free!" -ForegroundColor Green
}
