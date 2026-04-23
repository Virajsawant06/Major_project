@echo off
title Sentinel AI

REM Check if the first argument is "scan" (case-insensitive)
if /i "%1"=="scan" (
    echo.
    echo  Starting Sentinel AI Scanner...
    echo.
    echo  [1/2] Starting ZAP daemon...
    start "ZAP Daemon" /min cmd /c "cd /d ""C:\Program Files\ZAP\Zed Attack Proxy"" && zap.bat -daemon -port 8080 -config api.disablekey=true -config api.addrs.addr.name=127.0.0.1 -config api.addrs.addr.regex=true"
    
    echo  [2/2] Waiting for ZAP to boot - 40 seconds...
    timeout /t 40 /nobreak > nul
    echo  ZAP ready. Launching Sentinel...
    echo.
)

REM Activate Conda Environment
call conda activate sentinel

REM Set Working Directory to Sentinel Project Root
cd /d %~dp0

REM Pass all arguments directly to main.py
python src\main.py %*
