@echo off
chcp 65001 >nul
REM ============================================================
REM Taiwan Stock Daily Update (Phase B: local + git push)
REM
REM Schedule: every day 18:00 (post-market + before dinner)
REM
REM Pipeline:
REM   1. git pull
REM   2. fetch raw + adjusted (TWSE / TPEX / FinMind)
REM   3. signals for Takeshi / Katie / universe
REM   4. per_stock backtest reports (Markdown)
REM   5. README.md
REM   6. Web UI (root index.html + stock/*.html)
REM   7. inventory sync + analyze (from Excel 投資款.xlsx)
REM   8. git add commit push
REM ============================================================

setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHON=python
set REPO=D:\stock
set LOG_DIR=%REPO%\logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i
set LOG=%LOG_DIR%\daily_%TODAY%.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
cd /d "%REPO%" || exit /b 1

echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo  Daily update %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

echo [1/8] git pull >> "%LOG%"
git pull --rebase --autostash >> "%LOG%" 2>&1

echo [2/8] update --all >> "%LOG%"
"%PYTHON%" main.py update --all >> "%LOG%" 2>&1

echo [3/8] signals (Takeshi / Katie / universe) >> "%LOG%"
"%PYTHON%" main.py signals --list Takeshi  >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list Katie    >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list universe >> "%LOG%" 2>&1

echo [4/8] build_per_stock_reports >> "%LOG%"
"%PYTHON%" scripts\build_per_stock_reports.py >> "%LOG%" 2>&1

echo [5/8] update_readme >> "%LOG%"
"%PYTHON%" scripts\update_readme.py >> "%LOG%" 2>&1

echo [6/8] build_html >> "%LOG%"
"%PYTHON%" scripts\build_html.py >> "%LOG%" 2>&1

echo [7/8] inventory sync + analyze (Excel 投資款.xlsx) >> "%LOG%"
"%PYTHON%" main.py inventory >> "%LOG%" 2>&1

echo [8/8] git commit + push >> "%LOG%"
git add -A >> "%LOG%" 2>&1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "daily update %TODAY%" >> "%LOG%" 2>&1
    git push >> "%LOG%" 2>&1
    echo committed and pushed >> "%LOG%"
) else (
    echo no changes to commit >> "%LOG%"
)

echo Done at %TIME% >> "%LOG%"
endlocal
