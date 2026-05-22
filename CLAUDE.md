# 台股個股策略系統

> **修改程式前必讀**：`docs/ARCHITECTURE.md` — 模組地圖、資料流、「我要改 X 該編哪檔」查找表

## Token-efficient 修改路徑（Claude 用）

當被要求修改 X，先去 ARCHITECTURE.md 的「查找表」找對應檔案，不要全 repo 搜尋：

| 想做的事 | 載入哪些檔案 |
|---|---|
| 新增策略 template | `templates/<category>.py` + `templates/search_spaces.py` + `templates/__init__.py`（僅這 3 個） |
| 改 Tier 規則 | `tiering.py`（單檔，429 行） |
| 改 backtest 引擎 | `backtest_one.py`（單檔，187 行） |
| 改 BNH 評估 | `tiering.py` + `bnh.py` |
| 改 signals 輸出 | `src/strategy/runner.py` + `main.py.cmd_signals()` |
| 改 web UI | `scripts/build_html.py` |
| 改 markdown 報告 | `scripts/build_per_stock_reports.py` |
| 改 TWSE 抓取 | `src/fetchers/twse.py`（~90 行） |
| 改 TPEX 抓取 | `src/fetchers/tpex.py`（~130 行，2026-05 改新 endpoint） |
| 新增市場（如興櫃）| 新增 `src/fetchers/<market>.py` + `coordinator.MARKETS` 加一行 |
| 改 IPO / 市場別記錄 | `src/fetchers/metadata.py` |
| 改 fetch 編排 | `src/fetchers/coordinator.py` |
| 改 FinMind 籌碼 / 月營收 | `src/strategy/auto_iterate/chip_fetcher.py` / `revenue_fetcher.py` |
| Tier 規則改後重評現有 results | `scripts/retier_run_dir.py <run_id>` |
| 改 Excel 同步邏輯 | `scripts/sync_positions_from_excel.py` |
| 改庫存進出建議規則 | `scripts/inventory_analysis.py` |
| 抓 top-300 市值清單 | `scripts/fetch_top300_marketcap.py` |
| 全自動 top-300 pipeline | `scripts/auto_pipeline_top300.py`（每 20 檔 push 一次）|
| 啟動擴大歷史 retrain | `scripts/retrain_extended_history.py` 或 `.bat` |
| 24-hr heavy retrain (A/B/C) | `scripts/heavy_retrain_24hr.py` + `walk_forward_analysis.py` + `phase_c_coupling.py` |
| 看訓練紀錄索引 | `output/auto_iterate/INDEX.csv` 或 `INDEX.md`（`scripts/build_run_index.py` 產出）|

詳細工作流見 `docs/ARCHITECTURE.md`。

## 環境

**家裡 PC（D:\stock，目前位置）**：Python 3.13.13 from Microsoft Store，已在 PATH 中。
直接用 `python` 即可，不需指定絕對路徑（Microsoft Store Python 路徑含版本 hash 不穩定）。

**公司 PC（C:\TronFuture\lee\stock）舊設定（保留供參）**：
```
C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe
```

注意：Python 3.13 比 requirements.txt 推薦的 3.11/3.12 新，少數套件版本相容性需注意（特別是 optuna）。

**執行指令請用 Bash 工具，不要用 PowerShell 工具**：
- Bash 工具在 Windows 走 Git Bash，不會觸發 Windows 安全確認
- PowerShell 每次新指令都會跳確認鈕，干擾自動化
- 路徑用 forward slash 或單引號包覆 backslash 即可
- 範例：`'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py signals --list Takeshi`

## 專案定位

雙模式策略系統：訊號模式（Takeshi 用，每股給進出建議）+ 組合模式（Katie 用，top-N 配置）。
目標：7~10 年年化打贏 0050，MaxDD ≤ 30%。

## CLI 入口

```
python main.py screen | fetch | fetch-adjusted | fetch-revenue | update
              | positions [list/history/open/close]
              | signals | backtest | evaluate | optimize | auto_iterate
```
完整用法：`python main.py --help`

## 每日自動更新（家裡 PC）

`scripts/daily_update.bat` 是排程入口。流程：
```
[1] git pull                            ← Phase B 才啟用
[2] update --all                        ← fetch raw + adjusted
[3] signals --list Takeshi/Katie/universe
[4] build_per_stock_reports.py          ← 產 output/reports/per_stock/{sid}.md
[5] update_readme.py                    ← 產 README.md（手機 GitHub App 入口）
[6] build_html.py                       ← 產 docs/index.html + docs/stock/*.html（GitHub Pages 手機 web UI）
[7] git add commit push                 ← Phase B 才啟用
```

**Phase A vs Phase B 的差異**：
- Phase A：本地端跑 update + 產報告，**不 push GitHub**（手機暫時看不到，PC 本機可看 docs/index.html）
- Phase B：取消 daily_update.bat 中 [1] 與 [7] 的 REM 註解，加上 GitHub Pages 設定，手機就能看 `houyilee23.github.io/stock-strategy`

## 重要文件

### 設計規格（不要動，主要參考）
- `docs/ARCHITECTURE.md` — **★★ 系統架構文件（2026-05-18 重構後）★★**
  - 模組總覽、資料流圖、「我要改 X 該編哪個檔案」查找表
  - **修改程式前必讀** — 省下找檔案的 token
- `docs/SPEC_strategy_system.md` — 設計規格（single source of truth）
- `docs/SONNET_BUILD_PLAN.md` — 實作四階段計畫 + 自我驗證
- `docs/CHECKPOINTS.md` — Opus 審查節點

### 遷移與部署
- `docs/MIGRATION_GUIDE.md` — 從公司 PC 搬到家裡 PC + Windows 排程器設定 + GitHub Pages 啟用
- `docs/SESSION_HANDOFF_2026-05-04.md` — 5/4 整理 + web UI 那輪 session 的紀要（家裡 PC 第一次 Claude session 必讀）
- `docs/TODO_RETRAIN.md` — **待辦**：重訓 auto_iterate 用 2010+ 完整資料，重評 Tier
- `docs/TODO_AUDIT_TEMPLATES.md` — **待辦（先做這個）**：限價單機制下 audit 其他 templates 是否反勝目前 best
- `docs/LIMIT_ORDER_V0_1.md` — 限價單機制設計與實作（5/4 完成 7 templates）

### 配置
- `config/strategy.yaml` — 所有策略參數（不要 hardcode 數值）
- `config/per_stock_recommendations.yaml` — auto_iterate 產出的每檔最佳 template + tier
- `config/watchlists.yaml` — **個人觀察清單（gitignore，公開 repo 中不存在）**
- `config/watchlists.example.yaml` — 範本，家裡 PC 第一次設定要 copy 一份

### 工具腳本（5/15-5/17 新增）
- `scripts/apply_retrain_upgrades.py [--add-new] <run_id1> ...` — 將 auto_iterate run 的結果套用為個股升級（或加入新股）
- `scripts/retier_recommendations.py` — tiering 規則改後，對 recommendations.yaml 重新評級
- `scripts/retier_run_dir.py <run_id1> ...` — 對 auto_iterate run dir 的 per_stock_best.yaml 重新評級
- `scripts/rebuild_per_stock_best.py <run_id>` — 多 process 共用 dir 時，從 template yaml 重建 PSB
- `scripts/refresh_bnh_evaluations.py` — 重算所有 F-tier 個股的 BNH (買進長持) 替代評估

### 工具腳本（5/19-5/21 新增）
- `src/fetchers/` — 股價抓取模組化套件（取代原 540 行 `src/fetcher.py`）
  - `twse.py` / `tpex.py` / `metadata.py` / `storage.py` / `coordinator.py`
  - 加新市場只需新增一個 fetcher 模組 + `coordinator.MARKETS` 加一行
- `scripts/fetch_top300_marketcap.py` — 抓 TWSE + TPEX 官方 OpenAPI 計算市值，輸出 top 300
- `scripts/auto_pipeline_top300.py` — 全自動 pipeline：抓 raw → 加入 watchlist → 每 20 檔 build_html + push
- `scripts/retrain_extended_history.py` + `.bat` — 用 2010-2020 train 跑擴大歷史 retrain
- `scripts/heavy_retrain_24hr.py` — 24-hr Phase A→B→C controller
- `scripts/walk_forward_analysis.py` — Phase B 結束跨 fold robustness 報告
- `scripts/phase_c_coupling.py` — Phase C 多策略耦合 (top3_vote / equal_weight / pf_weighted / cascade)
- `scripts/build_run_index.py` — 掃 `output/auto_iterate/` 全部 run，產 `INDEX.csv` + `INDEX.md`

### 策略系統（src/strategy/auto_iterate/templates/ package，65 個 templates，5/18 拆分）
- `core_t1_t9.py` (9 funcs)         — T1-T9 原始模板
- `reversal_dips.py` (23 funcs)     — mean-reversion / dip / oversold
- `trend_breakouts.py` (21 funcs)   — trend / breakout / momentum
- `composite_advanced.py` (2 funcs) — chip_streak / monthly_revenue_event
- `ensembles.py` (10 funcs)         — composite-vote 策略
  - Phase 1 (vote-based)：dip_vote, breakout_vote, oversold_vote, trend_confirm, dip_or_bounce
  - Phase 2 (regime-aware)：regime_dip, breakout_pullback, dual_momentum
  - Phase 3 (intersection)：triple_confirm, bullish_divergence
- `search_spaces.py`                — SEARCH_SPACES + sample_template_params
- `__init__.py`                     — 公開 API + TEMPLATE_GENERATORS registry

**新增 template 步驟**：見 `docs/ARCHITECTURE.md` 的「策略模板新增流程」

- **2 個 rescue rules** in tiering.py：
  - C_HIGH_Q_RESCUE: n∈[5,9] + raw_PF≥3 + exp≥5% + |DD|≤25% + no holdout FAIL → C
  - D_LOW_N_RESCUE: n∈[3,4] + raw_PF≥5 + exp≥5% + |DD|≤25% → D（容忍 holdout）

## 重要約束

1. **時間防穿越**：所有訊號只能用 T 日及之前資料；成交在 T+1 開盤
2. **不引入回測框架**（vectorbt/backtrader/zipline）— 用 pandas 自刻
3. **參數集中** `config/strategy.yaml`，禁止 hardcode magic number
4. **錯誤落** `output/errors/{date}.csv`（用 `src/utils.log_error()`），不要 silent fail
5. **CSV 編碼** 一律 `utf-8-sig`
6. **敏感資料 gitignore**：`watchlists.yaml`、`trades_*.csv`、`positions_snapshot_*.csv` 已被 .gitignore 排除，**不要嘗試把它們加進 git**
7. **股價來源**（2026-05-19 起確認）：
   - TWSE 上市 → `openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY`
   - TPEX 上櫃 → `www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock`（舊 endpoint `st43_result.php` 已 404，2026-05-19 改新版）
   - **絕對不用 FinMind 抓股價**。FinMind 只用於：除權息/拆分/減資/籌碼/月營收 事件資料
   - 新市場（興櫃...）→ 新增 `src/fetchers/<market>.py` 並在 `coordinator.MARKETS` 註冊一行

## 報告輸出結構

```
output/reports/
├── latest/                          ← 永遠最新的訊號（README + web UI 讀這裡）
│   └── signals_{account}.md
├── 2026/05/                         ← 歷史歸檔（年/月）
│   └── 04_signals_{account}.md
└── per_stock/                       ← 個股回測 markdown（手機 GitHub App 點進去看）
    └── {sid}.md

docs/                                ← GitHub Pages 入口（手機 web UI）
├── index.html                       ← 主頁（3 帳戶 tab + 訊號表 + 搜尋 + 排序）
└── stock/
    └── {sid}.html                   ← 個股頁（多時段績效 + 年度交易 + 最近 10 筆）
```

## 過往 bug 警告（必讀）

詳見 `~/.claude/projects/C--TronFuture-lee-stock/memory/bugs_fixed.md`，重點：
- ADX 計算：`wilder()` 不能用在最終 ADX 平滑（用 EMA 即可），否則值會 ~14× 放大
- Risk/Reward 用 entry 價而非 close 價
- 日期字串比較：`"today"` 字串不能直接和 `"YYYYMMDD"` 比
- **fetcher 增量更新漏洞（2026-05-04 修）**：`get_missing_months()` 對歷史月份只看「該月是否有任何一天的資料」，會漏抓月底；現已加入「本地最後一筆所在月份」也納入 missing

## 使用者偏好

- 繁體中文回應
- 終端輸出簡潔，不要冗長 log
- 不會自動下單，所有訊號是給人手動執行
- watchlist 會擴張，但靠手動加，不要自動篩
- print 含 unicode 符號（✓/✗/✅）→ 在 Windows cp950 console 會壞，腳本要 `sys.stdout.reconfigure(encoding="utf-8")`
- markdown / HTML 表頭的 CJK 字元寬度問題：用 `unicodedata.east_asian_width` 算 padding，不要靠 Python `:<6` 字元數
