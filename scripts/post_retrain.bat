@echo off
chcp 65001 >nul
REM ============================================================
REM Post-retrain pipeline (run after auto_iterate finishes
REM and final_report has updated config/per_stock_recommendations.yaml)
REM
REM Pipeline:
REM   1. signals (Takeshi / Katie / universe)
REM   2. per_stock backtest reports
REM   3. README.md
REM   4. Web UI (root index.html + stock/*.html)
REM   5. compare OLD vs NEW recommendations
REM ============================================================

setlocal
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
echo Done. See output\recommendations_diff_%TODAY%.md for diff.
echo Open file:///D:/stock/index.html for local preview.
endlocal
