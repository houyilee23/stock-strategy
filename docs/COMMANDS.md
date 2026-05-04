# 指令備忘錄（直接複製貼上即可執行）

> 所有指令前綴用完整 Python 路徑，避免系統 `python` 指錯解譯器。
> Windows 下用 **Bash 工具 / Git Bash 終端機**執行（PowerShell 會跳安全確認）。

---

## 快速複製：Python 路徑

```
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe'
```

以下所有指令的 `PY` 都是這條路徑。

---

## 🔵 一、抓資料

### ⭐ 1-0. 一條搞定：raw + 還原（每天用這條）

```bash
# 全部 80 檔
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py update --all

# 只更新某帳戶
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py update --list Katie
```
**它會做兩件事**：
1. STEP 1/2 → TWSE/TPEX 抓 raw（自動跳過已快取的月份，只抓當月）
2. STEP 2/2 → FinMind 抓事件 + 算 adj close

每天例行用這條最方便。下面 1-1、1-2 是 debug 時要分開跑用的。

### 1-1. 抓 raw 股價（TWSE / TPEX 直連）

```bash
# 指定股票代號
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch 1301 2330

# 抓某帳戶清單（Takeshi / Katie / research）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch --list Takeshi
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch --list Katie
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch --list research

# 抓全部 80 檔（watchlist 三組合併，去 exception）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch --all
```
**輸出**：`data/raw/{sid}.csv`（OHLCV，**未還原權息**）

### 1-2. 抓還原股價事件 + 算 adj close（FinMind 免費）

```bash
# 抓單檔（測試用）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch-adjusted 0050

# 抓某帳戶清單
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch-adjusted --list Katie

# 抓全部 80 檔（推薦：第一次跑用這個）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch-adjusted --all

# 增量更新（已抓過的跳過，省時間）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch-adjusted --all --skip-existing

# 指定區間
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch-adjusted --all --start 2015-01-01 --end 2025-12-31
```
**輸出**：
- `data/dividends/{sid}.csv` — 除權息事件原始資料
- `data/splits/{sid}.csv` — 拆分 / 減資事件原始資料
- `data/adjusted/{sid}.csv` — 還原股價（含 `close_adj` 欄位）

**前置**：要先有 `data/raw/{sid}.csv`（adj close 是用 raw close + 事件算的）

---

## 🟢 二、跑訊號 / 回測

### 2-1. 今日訊號（手動下單前看這個）

```bash
# Takeshi 清單今日進出建議
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py signals --list Takeshi

# Katie 清單今日訊號
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py signals --list Katie
```
**輸出**：`output/reports/{date}_signals_{帳戶}.md`

### 2-2. 歷史回測

```bash
# 訊號模式回測（Takeshi 該用這個）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py backtest --list Takeshi

# 組合模式回測（Katie 該用這個）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py backtest --list Katie --portfolio

# 指定區間
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py backtest --list Katie --portfolio --start 2020-01-01 --end 2024-12-31
```
**輸出**：`output/backtest/` 下會有 timestamp 命名的 `per_stock_*.csv`、`portfolio_*.csv`、`equity_*.csv`、`*_summary.md`

### 2-3. 重算指標 / 產報表

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py evaluate --run-id 20260423_100233
```
（`run-id` 是上一條 backtest 印出的 timestamp）

### 2-4. 一鍵跑兩個帳戶並比對（Round 3 報告 script）

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' scripts/round3_report.py
```

### 2-5. 0050 還原股價驗證實驗（驗證 adj 演算法）

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' scripts/test_0050_adjustment.py
```

---

## 🟡 三、持倉管理

### 3-1. 查持倉

```bash
# 預設 Takeshi
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions list

# 切換帳戶
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions list --account Katie

# 看歷史已實現損益
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions history
```

### 3-2. 開倉 / 平倉（手動下單後記錄）

```bash
# 開倉：1301 @ 82.5 買 1000 股
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions open 1301 82.5 1000

# 指定日期
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions open 1301 82.5 1000 --date 2026-04-18

# 平倉（自動取最新收盤價）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions close 1301

# 平倉指定價格
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions close 1301 95.0

# 部分平倉
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py positions close 1301 --shares 500
```

> 也可以**直接編輯** `data/trades_{帳戶}.csv` 手動加交易記錄（流水帳格式）。

---

## 🟣 四、測試

### 4-1. Sanity gate（驗證沒有結構性 bug）

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' -m pytest tests/test_sanity_gates.py -v
```

### 4-2. 全測試

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' -m pytest -v
```

### 4-3. 單一測試檔

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' -m pytest tests/test_indicators.py -v
```

---

## ⚪ 五、其他工具

### 5-1. 股票清單篩選（用 screener）

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py screen
```

### 5-2. 看主程式所有指令

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py --help
```

---

## 📋 典型工作流（新手第一次 / 新研究週期）

### A. 第一次設定（資料齊全）

```bash
PY='C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe'

# 1. 一條搞定 raw + 還原（首次跑大概 30-60 分鐘，主要是 raw 慢）
$PY main.py update --all

# 2. 跑回測看指標
$PY scripts/round3_report.py

# 3. 看訊號做下單決策
$PY main.py signals --list Takeshi
$PY main.py signals --list Katie
```

### B. 每天例行（已經設定好）

```bash
PY='C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe'

# 1. 一條搞定更新今天的資料（raw 增量 + 還原重抓 ~5 分鐘）
$PY main.py update --all

# 2. 看今日訊號
$PY main.py signals --list Takeshi
$PY main.py signals --list Katie

# 3. 看持倉
$PY main.py positions list --account Takeshi
$PY main.py positions list --account Katie
```

### C. 新增 / 改動策略後

```bash
PY='C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe'

# 1. 跑 sanity gate
$PY -m pytest tests/test_sanity_gates.py -v

# 2. 全部回測
$PY scripts/round3_report.py

# 3. 對照新舊指標決定是否上線
```

---

## 🔧 編輯設定的位置

| 內容 | 檔案 |
|---|---|
| 策略參數（門檻、週期等）| `config/strategy.yaml` |
| 帳戶清單 | `config/watchlists.yaml` |
| 帳戶配置（資金、模式）| `config/strategy.yaml` 的 `accounts:` |
| FinMind token（若要用）| `config/secrets.yaml`（要建立 + 加 .gitignore）|
| 持倉流水帳 | `data/trades_{帳戶}.csv` |

---

## 🚨 Bash 小技巧（Git Bash 環境）

```bash
# 設變數簡化
PY='C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe'
$PY main.py signals --list Takeshi

# 把輸出存檔
$PY scripts/round3_report.py > output/reports/round3_$(date +%Y%m%d).log 2>&1

# 看最新一筆 backtest
ls -t output/backtest/*_summary.md | head -1 | xargs cat
```
