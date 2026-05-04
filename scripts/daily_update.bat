@echo off
REM ============================================================
REM 台股個股策略系統 — 每日自動更新
REM
REM 目前模式：Phase B（本地自動更新 + 推送 GitHub）
REM   切回 Phase A：把下面 git pull / git commit-push 兩段加 REM 註解
REM ============================================================
REM
REM 工作排程器設定：
REM   觸發程序：每天 18:00（盤後資料穩定後 + 晚餐前）
REM   動作：執行此 .bat
REM   條件：勾「啟動工作以喚醒電腦」
REM
REM 流程：
REM   1. [Phase B] git pull
REM   2. fetch raw + adjusted
REM   3. 各帳戶產 signals 報告
REM   4. 重新產生個股回測報告
REM   5. 重新產生 README.md
REM   6. 重新產生 web UI（docs/index.html + docs/stock/*.html）
REM   7. [Phase B] git add commit push
REM ============================================================

setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHON=python
set REPO=D:\stock
set LOG_DIR=%REPO%\logs
REM 用 PowerShell 產日期字串，避開不同 locale 的 %date% 格式差異
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i
set LOG=%LOG_DIR%\daily_%TODAY%.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
cd /d "%REPO%" || exit /b 1

echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo  Daily update %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

REM ---- Step 1: git pull ----
echo [1/7] git pull >> "%LOG%"
git pull --rebase --autostash >> "%LOG%" 2>&1

REM ---- Step 2: fetch raw + adjusted ----
echo [2/7] update --all >> "%LOG%"
"%PYTHON%" main.py update --all >> "%LOG%" 2>&1

REM ---- Step 3: signals 各帳戶 ----
echo [3/7] signals (Takeshi / Katie / universe) >> "%LOG%"
"%PYTHON%" main.py signals --list Takeshi  >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list Katie    >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list universe >> "%LOG%" 2>&1

REM ---- Step 4: per_stock backtest reports (Markdown) ----
echo [4/7] build_per_stock_reports >> "%LOG%"
"%PYTHON%" scripts\build_per_stock_reports.py >> "%LOG%" 2>&1

REM ---- Step 5: README.md ----
echo [5/7] update_readme >> "%LOG%"
"%PYTHON%" scripts\update_readme.py >> "%LOG%" 2>&1

REM ---- Step 6: Web UI (HTML for mobile) ----
echo [6/7] build_html >> "%LOG%"
"%PYTHON%" scripts\build_html.py >> "%LOG%" 2>&1

REM ---- Step 7: git commit + push ----
echo [7/7] git commit + push >> "%LOG%"
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
