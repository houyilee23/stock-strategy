# 台股個股策略系統 - 技術文檔（ChatGPT 版）

> **修改程式前必讀**：`docs/ARCHITECTURE.md` — 模組地圖、資料流、檔案速查表

本文檔移除了 Claude Code 特異部分，適合所有開發環境。

---

## 專案定位

雙模式策略系統：
- **訊號模式**（Takeshi）：每股給進出建議
- **組合模式**（Katie）：top-N 配置

目標：7~10 年年化打贏 0050，MaxDD ≤ 30%

---

## 環境

**開發環境**：Windows 11，Python 3.13（Microsoft Store）

**執行指令**：用 PowerShell 或 Git Bash，路徑支援正斜線和反斜線：
```bash
cd D:\stock
python main.py signals --list Takeshi
```

---

## CLI 入口

完整命令列用法：
```bash
python main.py --help
```

主要命令：
```
python main.py fetch                        # 抓股價 (TWSE/TPEX)
python main.py fetch-adjusted               # 抓除權息調整因子
python main.py fetch-revenue                # 抓月營收 (FinMind)
python main.py update --all                 # fetch + fetch-adjusted + fetch-revenue

python main.py signals --list Takeshi       # 產 Takeshi 帳戶訊號
python main.py signals --list Katie         # 產 Katie 帳戶訊號
python main.py signals --list universe      # 掃全 watchlist

python main.py positions [list/history/open/close]  # 查詢持倉

python main.py backtest <stock_id> <template>      # 單股回測
python main.py evaluate <stock_id> <template>      # 詳細評估
python main.py optimize <stock_id> <template>      # 參數優化 (Optuna)
python main.py auto_iterate                        # 全自動訓練

python main.py journal validate             # 驗證昨日成交
python main.py journal view                 # 查詢交易日誌
python main.py journal report               # 績效報表
```

---

## 每日自動更新流程

`scripts/daily_update.bat` 是 Windows 排程入口，流程：

```
[1] git pull                            ← Phase B 才啟用
[2] python main.py update --all         ← fetch raw + adjusted + revenue
[3] python main.py journal validate     ← 驗證昨日掛單成交
[4] python main.py signals --list Takeshi/Katie/universe
[5] python scripts/build_per_stock_reports.py
[6] python scripts/update_readme.py
[7] python scripts/build_html.py        ← GitHub Pages 用
[8] python scripts/sync_positions_from_excel.py  ← 從 Excel 同步
[9] git add commit push                 ← Phase B 才啟用
```

### Phase A vs Phase B

**Phase A**（預設）：
- 本地跑 update 和產報告
- **不推送 GitHub**
- 手機上看不到，PC 本機可看 `docs/index.html`

**Phase B**：
- 取消 `daily_update.bat` 中 [1] 和 [7] 的註解
- 啟用 GitHub Pages
- 手機能看 `houyilee23.github.io/stock-strategy`

---

## 核心設計

### 重要約束

1. **時間防穿越**：訊號只能用 T 日及之前資料；成交在 T+1 開盤
2. **參數集中**：`config/strategy.yaml`，禁止 hardcode
3. **錯誤落**：`output/errors/{date}.csv`，用 `src/utils.log_error()`
4. **CSV 編碼**：一律 `utf-8-sig`
5. **敏感資料 gitignore**：`watchlists.yaml`、`trades_*.csv`
6. **股價來源**（2026-05-19 確認）：
   - TWSE 上市 → `openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY`
   - TPEX 上櫃 → `www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock`
   - **絕對不用 FinMind 抓股價**（只用於除權息/籌碼/月營收）
   - 新市場 → 新增 `src/fetchers/<market>.py` + 在 `coordinator.MARKETS` 加一行

### 策略系統

**65 個策略模板**，分組：
- `core_t1_t9.py` (9 個)         — T1-T9 原始模板
- `reversal_dips.py` (23 個)     — mean-reversion / dip / oversold
- `trend_breakouts.py` (21 個)   — trend / breakout / momentum
- `composite_advanced.py` (2 個) — chip_streak / monthly_revenue_event
- `ensembles.py` (10 個)         — composite-vote 策略

### Tier 規則

- **S/A/B**：高績效（優先選）
- **C/D**：中等績效（附條件選用）
- **F**：低績效（備用選項）

2 個救援規則（見 `src/strategy/auto_iterate/tiering.py`）：
- `C_HIGH_Q_RESCUE`：高品質但參數少 → 升 C
- `D_LOW_N_RESCUE`：低參數但高績效 → 升 D

---

## 檔案速查表

| 想做的事 | 編輯哪些檔案 |
|---|---|
| 新增策略 template | `templates/<category>.py` + `templates/search_spaces.py` + `templates/__init__.py` |
| 改 Tier 規則 | `tiering.py`（429 行） |
| 改 backtest 引擎 | `backtest_one.py`（187 行） |
| 改 signals 輸出 | `src/strategy/runner.py` + `main.py.cmd_signals()` |
| 改 web UI | `scripts/build_html.py` |
| 改 markdown 報告 | `scripts/build_per_stock_reports.py` |
| 改 TWSE 抓取 | `src/fetchers/twse.py`（~90 行） |
| 改 TPEX 抓取 | `src/fetchers/tpex.py`（~130 行） |
| 新增市場 | 新增 `src/fetchers/<market>.py` + `coordinator.MARKETS` |
| 改 journal 欄位 | `src/journal/schema.py`（~70 行） |
| 改 journal 驗證 | `src/journal/validator.py` |
| 改 journal 報表 | `src/journal/reporter.py` |
| 重評 Tier | `scripts/retier_run_dir.py <run_id>` |

---

## 重要文件

### 設計規格（參考，不要動）
- `docs/ARCHITECTURE.md` — **架構文檔**（改程式前必讀）
- `docs/SPEC_strategy_system.md` — 完整設計規格
- `docs/SIGNAL_JOURNAL.md` — 訊號日誌 + 績效報表

### 部署與遷移
- `docs/MIGRATION_GUIDE.md` — Windows 排程器設定 + GitHub Pages 啟用

### 配置
- `config/strategy.yaml` — 所有策略參數
- `config/per_stock_recommendations.yaml` — auto_iterate 產出的最佳 template + tier
- `config/watchlists.yaml` — 個人觀察清單（gitignored）
- `config/watchlists.example.yaml` — 範本

---

## 報告輸出結構

```
output/reports/
├── latest/                          ← 永遠最新的訊號
│   └── signals_{account}.md
├── 2026/05/                         ← 歷史歸檔
│   └── 04_signals_{account}.md
└── per_stock/                       ← 個股回測 markdown
    └── {sid}.md

docs/                                ← GitHub Pages 入口
├── index.html                       ← 主頁（tab + 訊號表 + 搜尋）
└── stock/
    └── {sid}.html                   ← 個股頁
```

---

## 過往 bug 警告

- **ADX 計算**：`wilder()` 不能用在最終 ADX 平滑（用 EMA 即可），否則值會 ~14× 放大
- **Risk/Reward**：用 entry 價而非 close 價
- **日期比較**：`"today"` 字串不能直接和 `"YYYYMMDD"` 比
- **fetcher 漏洞**（已修）：`get_missing_months()` 對歷史月份會漏抓月底；現加入本地最後一筆所在月份

---

## 使用者偏好

- 繁體中文回應
- 終端輸出簡潔
- 不會自動下單（訊號給人手動執行）
- watchlist 靠手動加（不自動篩）
- print 含 unicode（✓/✗/✅）→ Windows console 需 `sys.stdout.reconfigure(encoding="utf-8")`
- CJK 字元寬度 → 用 `unicodedata.east_asian_width` 算 padding

---

**最後更新**：2026-07-18
