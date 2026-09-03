# agent/scripts/install_service.ps1

param(
    [string]$ServiceName = "HECRASAgent",
    [string]$DisplayName = "HEC-RAS Simulation Agent",
    [string]$Description = "HEC-RAS Simulation Agent for Flood WebGIS System",
    [string]$PythonExe = "python.exe",
    [string]$ScriptPath = "C:\HECRAS\Agent\src\main.py"
)

# Kiểm tra quyền admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing HEC-RAS Agent Service..." -ForegroundColor Green

# Tạo script để chạy agent
$ServiceScript = @"
import sys
import os
import win32serviceutil
import win32service
import win32event
import servicemanager
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import HECRASAgent

class HECRASAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "$ServiceName"
    _svc_display_name_ = "$DisplayName"
    _svc_description_ = "$Description"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.agent = None
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.agent:
            self.agent.stop()
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.agent = HECRASAgent()
        self.agent.run()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(HECRASAgentService)
"@

# Tạo file service.py
$ServiceFile = "C:\HECRAS\Agent\service.py"
$ServiceScript | Out-File -FilePath $ServiceFile -Encoding UTF8

# Cài đặt service
python -m pip install pywin32

python $ServiceFile install
python $ServiceFile start

Write-Host "Service installed and started successfully!" -ForegroundColor Green
Write-Host "Service Name: $ServiceName" -ForegroundColor Cyan
Write-Host "To check status: sc query $ServiceName" -ForegroundColor Cyan
Write-Host "To stop: python $ServiceFile stop" -ForegroundColor Cyan
Write-Host "To uninstall: python $ServiceFile remove" -ForegroundColor Cyan