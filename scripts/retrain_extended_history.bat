@echo off
chcp 65001 >nul
REM ============================================================
REM 擴大歷史區間 retrain wrapper
REM   Train 2010-01-01 ~ 2020-12-31
REM   Test  2021-01-01 ~ 2026-04-22
REM
REM 建議排程方式：Windows Task Scheduler，每週日 02:00 觸發一次
REM   schtasks /create /tn "stock_retrain_weekly" /tr "D:\stock\scripts\retrain_extended_history.bat" /sc weekly /d SUN /st 02:00
REM
REM 或手動執行：
REM   D:\stock\scripts\retrain_extended_history.bat              ← 全 universe（~數小時 至一天）
REM   D:\stock\scripts\retrain_extended_history.bat --pilot      ← 只跑 Takeshi 驗證
REM ============================================================

setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set REPO=D:\stock
set LOG_DIR=%REPO%\logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmm"') do set TS=%%i
set LOG=%LOG_DIR%\retrain_%TS%.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
cd /d "%REPO%" || exit /b 1

echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo  Extended-history retrain %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

REM 預設：100 trials/pair，全 universe，wide-search OFF（先穩定再加）
python scripts\retrain_extended_history.py %* >> "%LOG%" 2>&1

echo Done at %TIME% >> "%LOG%"
endlocal
