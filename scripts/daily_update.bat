@echo off
REM ============================================================
REM 台股個股策略系統 — 每日自動更新
REM
REM 目前模式：Phase A（本地自動更新，不 push GitHub）
REM   ↓ 跑 1~2 週驗證穩定後可切到 Phase B
REM Phase B 切換方式：
REM   把下面標 [Phase B] 的兩段 REM 註解拿掉即可
REM ============================================================
REM
REM 工作排程器設定：
REM   觸發程序：每天 21:00
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

REM ---- Step 1 [Phase B]: git pull ----
REM 取消下三行註解以啟用 Phase B
REM echo [1/7] git pull >> "%LOG%"
REM git pull --rebase --autostash >> "%LOG%" 2>&1

REM ---- Step 2: fetch raw + adjusted ----
echo [2/7] update --all >> "%LOG%"
"%PYTHON%" main.py update --all >> "%LOG%" 2>&1

REM ---- Step 3: signals 各帳戶 ----
echo [3/7] signals (Takeshi / Katie / research) >> "%LOG%"
"%PYTHON%" main.py signals --list Takeshi  >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list Katie    >> "%LOG%" 2>&1
"%PYTHON%" main.py signals --list research >> "%LOG%" 2>&1

REM ---- Step 4: per_stock backtest reports (Markdown) ----
echo [4/7] build_per_stock_reports >> "%LOG%"
"%PYTHON%" scripts\build_per_stock_reports.py >> "%LOG%" 2>&1

REM ---- Step 5: README.md ----
echo [5/7] update_readme >> "%LOG%"
"%PYTHON%" scripts\update_readme.py >> "%LOG%" 2>&1

REM ---- Step 6: Web UI (HTML for mobile) ----
echo [6/7] build_html >> "%LOG%"
"%PYTHON%" scripts\build_html.py >> "%LOG%" 2>&1

REM ---- Step 7 [Phase B]: git commit + push ----
REM 取消下方 IF 區塊註解以啟用 Phase B
REM echo [7/7] git commit + push >> "%LOG%"
REM git add -A >> "%LOG%" 2>&1
REM git diff --cached --quiet
REM if errorlevel 1 (
REM     git commit -m "daily update %TODAY%" >> "%LOG%" 2>&1
REM     git push >> "%LOG%" 2>&1
REM     echo committed and pushed >> "%LOG%"
REM ) else (
REM     echo no changes to commit >> "%LOG%"
REM )

echo Done at %TIME% >> "%LOG%"
endlocal
