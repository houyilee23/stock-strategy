# Session Handoff — 2026-05-04 整理 + Web UI

> 給「家裡 PC 上第一次開啟 Claude」的開場 prompt。
> 把這份和 `CLAUDE.md` 一起讀完，可以無縫接上前一個 session 在公司 PC 上做的事。

---

## 這一輪做了什麼（簡短版）

1. **修了一個 fetcher bug**：`get_missing_months()` 對歷史月份只判斷「該月有沒有任何一天的資料」就 skip，導致月底剛沒抓滿時後幾天永遠補不回來。修法：把「本地最後一筆所在月份」也納入 missing。
2. **修了 signals 終端輸出表格 CJK 字元對齊**：用 `unicodedata.east_asian_width` 算 padding，不靠 Python `:<6` 字元數。
3. **整個專案大瘦身 + 重組**：
   - 刪 `archive/2026-04-23/`、`trash/`、`__pycache__/`、`.pytest_cache/`
   - 把 `scripts/` 8 個舊腳本移到 `archive/scripts/`（保留追溯，不刪）
   - 刪 `output/auto_iterate/` 中 12 個舊 timestamped run（只留 `merged_20260426_120034`）
   - 全清 `output/backtest/`、`output/optimize/`、`output/logs/`、`logs/` timestamped 檔
   - 整體 130 MB → 43 MB（push 上 GitHub 的部分）
4. **設計新的 reports 結構**：
   ```
   output/reports/latest/         ← 永遠最新（README + web UI 讀這裡）
   output/reports/{YYYY}/{MM}/    ← 年/月歷史歸檔
   output/reports/per_stock/      ← 個股回測 markdown
   ```
   並修改 `src/strategy/eval/reporter.py:save_daily_signals_md()` 配合新路徑。
5. **保護敏感資料**（為了 Public repo）：
   - `.gitignore` 擋住 `config/watchlists.yaml`、`data/trades_*.csv`、`data/positions_*.csv`、`output/positions_snapshot_*.csv`
   - 建 `config/watchlists.example.yaml` 作為範本
6. **每日自動化腳本**：
   - `scripts/build_per_stock_reports.py` — 對每檔產回測 markdown
   - `scripts/update_readme.py` — 產 README.md（手機 GitHub App 入口）
   - `scripts/build_html.py` — 產 GitHub Pages 用的手機 web UI（核心 v1）
   - `scripts/daily_update.bat` — Windows 排程入口（目前是 Phase A 模式，git push 已用 REM 註解掉）
7. **新文件**：
   - `requirements.txt`
   - `README.md`（自動生成）
   - `docs/MIGRATION_GUIDE.md` — 完整搬遷 + 排程設定步驟
   - `docs/SESSION_HANDOFF_2026-05-04.md` — 這份

---

## 你（家裡 PC Claude）會收到的狀態

User 會在家裡桌機把整包資料夾 `C:\TronFuture\lee\stock` 透過 USB / 雲端硬碟手動搬過來。所以你看到的目錄狀態應該跟整理後完全一樣。

**第一次跑要做什麼**（user 會手動執行）：
1. 確認 Python 路徑（家裡 PC 的 Anaconda 路徑可能不同）→ 更新 `CLAUDE.md` 與 `scripts/daily_update.bat` 中的 PATH
2. `pip install -r requirements.txt`
3. 從備份還原 `config/watchlists.yaml`（gitignore 不會跟著搬上來，要從公司 PC 另外帶過來）
4. 從備份還原 `data/trades_*.csv`（如果他自己有持倉）
5. 跑一次 `scripts/daily_update.bat` 手動驗證流程通

---

## v1 Web UI 規格（已實作，未來可能要擴充）

### 已實作
- 首頁 `docs/index.html`：摘要 banner + 3 帳戶 tab + 訊號表 + 搜尋 + 排序（Alpine.js）
- 個股頁 `docs/stock/{sid}.html`：策略推薦 + 多時段績效（半年/1y/2y/3y/5y/10y/全期）+ 年度交易 + 最近 10 筆
- 響應式（手機優先 max-width 600px 切換）
- Pico.css + Alpine.js + 純 inline JSON（CDN）

### User 確認過的後續可加項（v2 以後再說）
- ❌ 篩選按鈕（user 說「等以後再說」）
- ❌ K 線圖（暫不做）
- ❌ 年度績效柱狀圖
- ❌ Equity curve 曲線
- ❌ PWA 加主畫面
- ❌ Dark mode
- ❌ 兩層使用者清單（watchlists.yaml + localStorage Star）

---

## 排程切到 Phase B 的步驟（未來 user 跑順 1~2 週後做）

1. 在 GitHub 建 public repo：`stock-strategy`（user 已決定 public）
2. 家裡 PC 跑：
   ```bash
   git init && git add . && git commit -m "initial migration"
   git branch -M main
   git remote add origin https://github.com/houyilee23/stock-strategy.git
   git push -u origin main
   ```
3. 推之前驗證敏感檔沒被推：
   ```bash
   git ls-files | grep -E "watchlists.yaml|trades_|positions_"
   ```
   應無輸出。
4. 開啟 GitHub Pages：repo Settings → Pages → Source: `main` / `/docs` → 等 1 分鐘
5. 確認 `https://houyilee23.github.io/stock-strategy/` 顯示首頁
6. 編輯 `scripts/daily_update.bat`，把 `[Phase B]` 標記的兩段 REM 註解拿掉
7. 從此每天 21:00 排程自動 push 到 GitHub，手機開網址就能看當天訊號

---

## User 的偏好風格

- 繁體中文回應
- 終端輸出簡潔（不要冗長 log）
- 個性：先討論概念再動工（除非他明確說「直接做」或 auto mode 啟動）
- 喜歡漸進、可驗證、可回溯的方式（這就是為什麼選 Phase A → Phase B 而不是一步到位）

---

## 重要技術細節

### Python stdout UTF-8 強制
Windows cp950 console 不支援 ✓✗✅ 等 unicode。新腳本一律加：
```python
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
```

### CJK 字元終端對齊
`reporter.py` 已改用 `unicodedata.east_asian_width` 計算視覺寬度。Python 原生 `:<6` 用字元數對 CJK 不準。

### auto_iterate 結果路徑
`config/per_stock_recommendations.yaml` 是 `merged_20260426_120034` 的成品。實際 best_params YAML 在：
```
output/auto_iterate/merged_20260426_120034/{template}.yaml
↓
top-level keys: per_stock, template, generated_at, ...
per_stock.{stock_id}.best_params  ← 結構從這裡進去
```

### 多時段績效計算
`scripts/build_html.py:trailing_returns_strategy()` 從 `equity_curve` 切片計算 CAGR，不重新跑回測（節省時間）。各時段視 equity start/end 算 geometric CAGR。

### Backtester start_date / end_date
`config/strategy.yaml` 中設定。實際資料只到 `data/adjusted/{sid}.csv` 的 max date（目前 20260430，user 在 5/4 盤中）。

---

## 已完成（補記）：限價單機制 v0.1（**5/4 晚下班前最終狀態**）

📋 **詳見 [docs/LIMIT_ORDER_V0_1.md](LIMIT_ORDER_V0_1.md)**

5/4 一整天完成的事：
1. ✅ **2 個 template 試水溫**：low_vol_pullback、mean_reversion
2. ✅ **整合真實持倉**（讀 trades_{account}.csv）
3. ✅ **「中性訊號 + 持倉註記」設計**（給家人/觀察都看得到 BUY 訊號）
4. ✅ **擴展到 7 個 templates**：再加 donchian_breakout、trend_pullback、momentum_hold、volume_breakout、bollinger_squeeze
5. ✅ **engine 支援 buy_mode（limit/stop）**：突破型用 buy-stop，回檔型用 buy-limit
6. ✅ **Web UI 加「掛單」欄 + 「在倉」欄 + 「📖 符號說明」摺疊區塊**
7. ✅ **CLI signals 加「掛單」「在倉」欄**
8. ✅ **驗證**：HOLD 日 intraday OCO 觸發完整在 backtest 中模擬（9 年 2360 共 34 個 TP + 18 個 SL 觸發）

剩 4 個 template 天生不適合限價單（chip×2、gap_continuation、monthly_revenue_event）— 維持 fallback。

家裡 PC Claude 看到這條訊息時，應該知道：
1. 用戶已用過這套機制看過手機 UI
2. 接下來建議「跑 1~2 週驗證 → audit 其他 templates → 重訓」
3. **不要主動建議「移除限價單機制」**（這是 user 主動提的需求）

---

## 待辦：Audit 其他 templates（**5/4 下班前 user 提出，待家裡 PC 處理**）

📋 **詳見 [docs/TODO_AUDIT_TEMPLATES.md](TODO_AUDIT_TEMPLATES.md)**

User 5/4 下班前的關鍵 question：「那有檢查其他原本沒被選中的策略嗎？說不定在限價單功能加入後，其他策略會更好？」

簡述：
- 目前 per_stock_recommendations.yaml 的 best_template 是 4/26 用**舊機制**選的
- 限價單機制改變了行為，可能讓「之前沒被選中」的 template 變更好
- 需要對 71 檔 × 7 limit-order templates 跑 audit（10~20 分鐘）
- 若 best_template 大幅改變 → 排完整重訓
- 若改變不大 → 繼續用 current params

家裡 PC Claude 看到這條時，主動問 user：「要先做 audit 嗎？只要 10~20 分鐘」。

## 待辦：重新訓練 auto_iterate（重要、需家裡 PC 處理）

📋 **詳見 [docs/TODO_RETRAIN.md](TODO_RETRAIN.md)**

簡述：當前 `config/per_stock_recommendations.yaml` 中的 Tier 是用 2017+ train、2023+ test 跑出來的；2026-05-04 把回測延長到 2010 後發現多檔在 2010-2015 表現不佳，**目前的 Tier 是「近期樂觀 fit」未通過長期 robustness check**。

User 的決定：「等回家再處理」。家裡 PC Claude 看到這條訊息時，請主動詢問 user 是否要排這個重訓工作。

預估時間：2~5 小時（一個週末晚上能跑完）。
Phase A 跑順 1~2 週後再做即可，**不急**。

## 已知尚未處理的小事

1. **Tab 按鈕 active 狀態視覺差異不明顯** — 三個 tab 都是同樣藍色，得從 aria-pressed 判讀。可加更明顯的 styling。
2. **README.md 與 web UI 中的「名稱」欄部分為空** — `signals_{account}.md` 中 name 欄需要 stock_names map，但 runner.py 沒傳。可從 `per_stock_recommendations.yaml` 補。
3. **個股頁的 trend_break / max_hold 出場原因沒區分** — `Backtester` 只記錄 SELL，沒記原因。要做的話要修 `engine.py` 加 reason 欄位。
4. **2360 4/24 Buy 是基於 4/24 那天的「不完整」資料，但全量回測時也算入** — 這個其實沒錯，因為 fetcher bug 已修，本地資料完整到 4/30，回測重跑會用完整資料。

---

## 給家裡 PC Claude 的 Reminder

如果 user 沒提這些，**主動提醒**：
- 第一次跑 daily_update.bat 之前，**先確認 Python 路徑與 PATH 已更新**
- 跑之前確認 `config/watchlists.yaml` 已從公司 PC 備份還原（否則程式會找不到清單）
- daily_update.bat 目前 Phase A，git push 是註解掉的；別自作主張取消註解（user 還沒準備好 push）
- web UI 是純前端，可在家裡 PC 用瀏覽器打開 `file:///C:/TronFuture/lee/stock/docs/index.html` 預覽
