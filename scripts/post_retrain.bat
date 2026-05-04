@echo off
REM ============================================================
REM Post-retrain：重跑 signals/reports/html + diff vs OLD baseline
REM
REM 用法：retrain (auto_iterate) 完成、final_report 已寫新
REM       config/per_stock_recommendations.yaml 後執行此 bat
REM ============================================================

setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHON=python
set REPO=D:\stock
set LOG_DIR=%REPO%\logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i
set LOG=%LOG_DIR%\post_retrain_%TODAY%.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
cd /d "%REPO%" || exit /b 1

echo ============================================================ >> "%LOG%"
echo  Post-retrain %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

echo [1/5] signals (Takeshi / Katie / universe) >> "%LOG%"
"%PYTHON%" main.py signals --list Takeshi  >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list Katie    >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list universe >> "%LOG%" 2>&1

echo [2/5] build_per_stock_reports >> "%LOG%"
"%PYTHON%" scripts\build_per_stock_reports.py >> "%LOG%" 2>&1

echo [3/5] update_readme >> "%LOG%"
"%PYTHON%" scripts\update_readme.py >> "%LOG%" 2>&1

echo [4/5] build_html >> "%LOG%"
"%PYTHON%" scripts\build_html.py >> "%LOG%" 2>&1

echo [5/5] compare OLD vs NEW recommendations >> "%LOG%"
"%PYTHON%" scripts\compare_recommendations.py >> "%LOG%" 2>&1

echo Done at %TIME% >> "%LOG%"
echo.
echo 完成。看 diff：output\recommendations_diff_%TODAY%.md
echo 看 web UI：file:///D:/stock/docs/index.html
endlocal
