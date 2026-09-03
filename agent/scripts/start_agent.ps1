# agent/scripts/start_agent.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentDir = Split-Path -Parent $ScriptDir

Write-Host "Starting HEC-RAS Agent..." -ForegroundColor Green
Write-Host "Agent Directory: $AgentDir" -ForegroundColor Cyan

# Activate virtual environment if exists
if (Test-Path "$AgentDir\venv\Scripts\Activate.ps1") {
    & "$AgentDir\venv\Scripts\Activate.ps1"
}

# Start agent
python "$AgentDir\src\main.py"