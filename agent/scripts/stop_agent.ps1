# agent/scripts/stop_agent.ps1

Write-Host "Stopping HEC-RAS Agent..." -ForegroundColor Yellow

# Find python process running agent
$Process = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*main.py*"
}

if ($Process) {
    $Process | ForEach-Object {
        Write-Host "Stopping process: $($_.Id)" -ForegroundColor Cyan
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "Agent stopped" -ForegroundColor Green
} else {
    Write-Host "Agent not running" -ForegroundColor Yellow
}