# 系統架構文件（2026-05-18 重構後）

本檔目的：**讓 Claude 或人類在最少時間找到要改哪個檔案**。每個功能對應到一個明確的模組，不再有單檔超過 1500 行的「神模組」。

---

## 模組總覽

```
D:\stock/
├── main.py                          # CLI 入口（fetch/signals/backtest/auto_iterate/...）
├── config/
│   ├── strategy.yaml                # 所有策略參數（不要 hardcode）
│   ├── watchlists.yaml              # 個人觀察清單 (gitignored)
│   └── per_stock_recommendations.yaml  # auto_iterate 產出的每檔最佳 template + tier
│
├── src/fetchers/                    # ★ 股價抓取（模組化 2026-05-19）
│   ├── __init__.py                  #   公開 API re-export
│   ├── metadata.py                  #   IPO 月份 + 市場別 YAML 管理
│   ├── twse.py                      #   上市單月抓取（純）
│   ├── tpex.py                      #   上櫃單月抓取（純，與 TWSE 平行）
│   ├── storage.py                   #   raw CSV 寫入 + 缺漏月份計算
│   └── coordinator.py               #   dispatch + auto-detect + batch pipeline
│   # 加新市場（例：興櫃）→ 只動 coordinator.MARKETS dict + 新增一個 fetcher 模組
│
├── src/fetcher.py                   # backward-compat thin shim（35 行）
│
├── src/strategy/
│   ├── indicators/                  # 純技術指標
│   │   ├── trend.py                 #   sma / ema / macd / adx
│   │   ├── momentum.py              #   rsi / roc / momentum_12_1
│   │   ├── volatility.py            #   atr / bollinger
│   │   └── volume.py                #   volume_ma / obv
│   │
│   ├── auto_iterate/                # 自動 retraining + tiering 系統
│   │   ├── templates/               # ★★ 策略模板（refactored 2026-05-18）
│   │   │   ├── __init__.py          #     公開 API：TEMPLATE_GENERATORS, SEARCH_SPACES, ...
│   │   │   ├── _common.py           #     共用 imports/helpers
│   │   │   ├── search_spaces.py     #     SEARCH_SPACES + sample_template_params
│   │   │   ├── core_t1_t9.py        #     T1-T9（9 個原始模板）
│   │   │   ├── reversal_dips.py     #     ~23 個 mean-reversion / dip 模板
│   │   │   ├── trend_breakouts.py   #     ~21 個 trend / breakout 模板
│   │   │   ├── composite_advanced.py#     chip_streak + monthly_revenue_event
│   │   │   └── ensembles.py         #     10 個 ensemble 策略（vote-based + regime-aware）
│   │   │
│   │   ├── runner.py                # auto_iterate 主流程（Optuna + backtest 編排）
│   │   ├── backtest_one.py          # 單一回測引擎（time-safe，T+1 entry）
│   │   ├── tiering.py               # Tier 規則 (S/A/B/C/D/F + Q5b-lite / C_HIGH_Q / D_LOW_N rescues)
│   │   ├── bootstrap.py             # PF bootstrap CI
│   │   ├── bnh.py                   # Buy-and-Hold metrics
│   │   ├── final_report.py          # 寫 final report / per_stock_recommendations.yaml
│   │   ├── merge_runs.py            # 合併多個 run dir 為 merged_*
│   │   ├── view_backtest.py         # CLI 工具：看個股回測細節
│   │   ├── chip_fetcher.py          # 三大法人籌碼資料
│   │   └── revenue_fetcher.py       # 月營收資料
│   │
│   ├── optimize/                    # Optuna 通用搜尋空間（T1 用）
│   ├── runner.py                    # 訊號模式 runner（signals 命令）
│   └── ...
│
├── scripts/                         # 命令列工具（auto_iterate 流程外）
│   ├── apply_retrain_upgrades.py    # 把 retrain 結果套用為個股升級（升級或加入新股）
│   ├── retier_recommendations.py    # tiering 規則改後重新評級 recommendations.yaml
│   ├── retier_run_dir.py            # 對 run dir 的 per_stock_best.yaml 重新評級
│   ├── rebuild_per_stock_best.py    # 多 process 共用 dir 時，從 template yaml 重建 psb
│   ├── refresh_bnh_evaluations.py   # 重算 F-tier 個股的 BNH (買進長持) 替代評估
│   ├── compare_recommendations.py   # 比較兩份 recommendations.yaml 差異
│   ├── audit_templates.py           # 限價單機制下 audit 其他 templates
│   ├── sync_positions_from_excel.py # 從 Excel 投資款.xlsx 同步交易記錄 (5/18 新增)
│   ├── inventory_analysis.py        # 個人庫存進出建議分析 (5/18 新增)
│   ├── build_per_stock_reports.py   # 產出 output/reports/per_stock/{sid}.md
│   ├── build_html.py                # 產出 stock/{sid}.html + index.html
│   ├── update_readme.py             # 產出 README.md 給手機 GitHub App
│   ├── fetch_via_finmind.py         # FinMind fallback fetcher（TWSE/TPEX 無資料時用）
│   ├── fetch_stock_ipo.py           # 抓 IPO 日期
│   ├── fetch_research_todo.py       # 自動 promote research_todo
│   └── daily_update.bat             # Windows 排程入口（每日 18:00）
│
└── output/
    ├── auto_iterate/<run_id>/       # 每次 auto_iterate run 的輸出
    │   ├── per_stock_best.yaml      #   每檔最佳 template + tier + 全部指標
    │   ├── <template>.yaml          #   每個 template 對所有 stock 的最佳參數
    │   ├── <template>.db            #   Optuna study database
    │   ├── comparison.csv           #   所有 (stock, template) pair 的比較表
    │   └── summary.md               #   人讀摘要
    ├── reports/
    │   ├── latest/                  #   永遠最新的 signals 報告
    │   ├── 2026/05/                 #   歷史歸檔
    │   └── per_stock/               #   個股回測 markdown
    └── errors/<date>.csv            # 錯誤紀錄（fetcher 等）
```

---

## 主要資料流（auto_iterate）

```
   universe (config/watchlists.yaml)
        │
        ▼
   runner.py.auto_iterate()
        │
        │   for each (sid, template):
        │     1. Optuna optimize  ── 從 SEARCH_SPACES 取參數空間
        │                            backtest_one() 評估
        │     2. bootstrap PF CI  ── bootstrap.py
        │     3. 三段 holdout     ── backtest_one() × 3 segments
        │     4. assign_tier()    ── tiering.py
        │
        ▼
   output/auto_iterate/<run_id>/
        │
        ▼
   final_report.write_recommendations()
        │
        ▼
   config/per_stock_recommendations.yaml
        │
        ▼
   signals / build_per_stock_reports / build_html
```

---

## 「我要改 X，應該編哪個檔案？」

| 想要改的東西 | 編這個檔案 |
|---|---|
| 改 Excel 同步邏輯 / 帳戶名稱 | `scripts/sync_positions_from_excel.py` |
| 改庫存進出建議規則 | `scripts/inventory_analysis.py`（`make_recommendation()` 函式） |
| 新增一個策略 template | `src/strategy/auto_iterate/templates/<category>.py` + `templates/search_spaces.py` + `templates/__init__.py`（加入 TEMPLATE_GENERATORS dict） |
| 修改 Tier 評級規則（升/降閾值、新 rescue rule） | `src/strategy/auto_iterate/tiering.py` |
| 修改 Optuna 搜尋邏輯 / 並行 | `src/strategy/auto_iterate/runner.py` |
| 修改 backtest 引擎（停損、進場時點） | `src/strategy/auto_iterate/backtest_one.py` |
| 修改 holdout 段定義 | `src/strategy/auto_iterate/tiering.py`（HOLDOUT_PERIODS） |
| 修改 BNH 評估規則 | `src/strategy/auto_iterate/tiering.py`（BNH_TIER_RULES）+ `bnh.py`（compute） |
| 修改 signals 輸出格式 | `src/strategy/runner.py` + `main.py.cmd_signals()` |
| 修改 web UI / 個股 HTML | `scripts/build_html.py` |
| 修改 markdown 報告 | `scripts/build_per_stock_reports.py` / `final_report.py` |
| 修改 README 自動生成 | `scripts/update_readme.py` |
| 新增工具腳本 | `scripts/<name>.py` |
| 新增技術指標 | `src/strategy/indicators/<category>.py` |
| 修改 TWSE 抓取 | `src/fetchers/twse.py`（單檔，~90 行）|
| 修改 TPEX 抓取 | `src/fetchers/tpex.py`（單檔，~130 行）|
| 新增市場（如興櫃）| 新增 `src/fetchers/<market>.py` + `coordinator.MARKETS` 加一行 |
| 修改 IPO / 市場別記錄 | `src/fetchers/metadata.py` |
| 修改 raw CSV 寫入邏輯 | `src/fetchers/storage.py` |
| 修改 fetch 編排（dispatch / batch）| `src/fetchers/coordinator.py` |
| 修改 FinMind 還原股價抓取 | `src/finmind_fetcher.py` |
| 修改 FinMind 月營收抓取 | `src/strategy/auto_iterate/revenue_fetcher.py` |
| 修改 FinMind 籌碼抓取 | `src/strategy/auto_iterate/chip_fetcher.py` |

---

## 策略模板新增流程（最常見）

新增一個 template `xyz_strategy`：

1. **寫 generator** 在 `templates/<category>.py`（選 reversal_dips / trend_breakouts / composite_advanced / ensembles）
   ```python
   def generate_xyz_strategy(df, params, regime=None, chip_data=None) -> pd.DataFrame:
       """XYZ strategy: ...."""
       # signal logic
       return pd.DataFrame({"action": ..., "target_buy": ..., "target_tp": ..., "target_sl": ...}, index=df.index)
   ```

2. **加 search space** 在 `templates/search_spaces.py`，在 SEARCH_SPACES dict 內：
   ```python
   "xyz_strategy": {
       "param1": {"type": "int", "low": 5, "high": 30, "step": 5},
       "param2": {"type": "float", "low": 0.02, "high": 0.1, "step": 0.01},
       # ...
   },
   ```

3. **註冊 generator** 在 `templates/__init__.py`：
   - 加入 import 列表的 `<category>` block
   - 加入 TEMPLATE_GENERATORS dict： `"xyz_strategy": generate_xyz_strategy,`

4. **跑 smoke test**：
   ```bash
   python main.py auto_iterate --templates xyz_strategy --universe 2330 --trials-per-pair 10
   ```

5. **如果成功** → 跑完整 retrain on F/D-tier：
   ```bash
   python main.py auto_iterate --templates xyz_strategy --universe <F_or_D_stock_list> --trials-per-pair 80
   python scripts/retier_run_dir.py <run_id>     # 套用最新 tier rules
   python scripts/apply_retrain_upgrades.py <run_id>   # 找升級
   ```

---

## 工作流：日常更新（已自動化）

`scripts/daily_update.bat` 每日 18:00 跑：
1. `git pull`
2. `python main.py update --all`     # fetch raw + adjusted
3. `python main.py signals --list Takeshi/Katie/universe`
4. `python scripts/build_per_stock_reports.py`
5. `python scripts/update_readme.py`
6. `python scripts/build_html.py`
7. `python main.py inventory`        # sync Excel + 庫存進出分析 (5/18 新增)
8. `git add commit push`

---

## 工作流：庫存（Excel 同步）

使用者在 `D:\Users\houyi\OneDrive\文件\投資款.xlsx` 的「交易紀錄」sheet
維護實際買賣交易，系統自動同步並給進出建議：

**Excel 預期格式**（sheet[1] = 「交易紀錄」）：
| 列 | 欄位 | 範例 |
|---|---|---|
| 1 | 日期 | 2026-04-02 |
| 2 | 動作 | Buy / Sell |
| 3 | 代號 | 4958 |
| 4 | 名稱 | 臻鼎-KY |
| 5 | 股數 | 5 |
| 6 | 現金流 | -1073 (買入為負) |
| 7 | 餘額 | 10708 |
| 8 | 平均成本 | 214.6 (現金流/股數，已含手續費/稅) |
| 14 | 備註 | (option) |

只匯入 Buy/Sell。其他動作（股利、轉帳、利息）自動略過。

**指令**：
```bash
# 一次完整：sync Excel + 跑分析
python main.py inventory

# 分開操作
python main.py inventory --sync-only       # 只同步
python main.py inventory --analyze-only    # 只分析（用既有 trades CSV）

# 換帳戶名稱
python main.py inventory --account Personal2
```

**輸出**：
- `data/trades_Personal.csv` (gitignored — 持倉私資料)
- `output/reports/inventory_advice_Personal.md` (gitignored — 手機看)
- `output/reports/inventory_advice_Personal.csv`

**進出建議邏輯**（按優先順序）：
1. **STOP_LOSS** 🛑 — 嚴重虧損（弱策略 < -15%，強策略 < -25%）
2. **REDUCE** ⬇️ — Tier F 或 倉位超過 tier 推薦上限 × 1.5
3. **TAKE_PROFIT** 💰 — 弱策略大幅獲利 > 30%（落袋為安）
4. **TRIM** ✂️ — 強策略過度獲利 > 50%（適度減碼）
5. **ADD** ➕ — 倉位過小（<推薦倉位 30%）+ Tier S/A/B + 近 20 日內拉回 >5%
6. **BNH_HOLD** 💎 — Tier F 但 BNH 評估可長持
7. **HOLD** ✋ — 維持

dedup 邏輯：用 (date, sid, action, shares) 作 key，重跑 sync 不會產重複交易。

---

## 工作流：retraining（手動觸發）

```bash
# 1. 跑 retrain
python main.py auto_iterate --templates <template> --universe <stocks> --trials-per-pair 80

# 2. 若有改 tiering 規則：先 retier 結果
python scripts/retier_run_dir.py <run_id>

# 3. 套用升級
python scripts/apply_retrain_upgrades.py <run_id1> <run_id2> ...

# 4. 跑日常 pipeline（signals + reports + html）
python main.py signals --list Takeshi
python scripts/build_per_stock_reports.py
python scripts/update_readme.py
python scripts/build_html.py

# 5. push
git add -u && git commit && git push
```

新股加入流程：

```bash
# 1. 編 watchlists.yaml，加入 universe 列表
# 2. 抓資料 (FinMind fallback 通常較穩)
python scripts/fetch_via_finmind.py <sid1> <sid2> ...
python main.py fetch-adjusted <sid1> <sid2> ...

# 3. baseline retrain（pick 4-6 個最強 templates）
python main.py auto_iterate --templates low_vol_pullback --universe <new_sids>
python main.py auto_iterate --templates gap_continuation --universe <new_sids>
# ... 並行 4-6 個

# 4. 用 --add-new flag 加入 recommendations
python scripts/apply_retrain_upgrades.py --add-new <run_id1> <run_id2> ...
```

---

## Tier 規則速查（tiering.py）

| Tier | 條件（主要） | pos_max |
|------|---|---|
| **S** | PF_lower≥2.0 + Exp≥5% + n≥8 + (holdout PASS 或 PF_lower≥3.0) | 100% |
| **A** | PF_lower≥1.5 + Exp≥3% + n≥6 + (holdout PASS 或 PF_lower≥2.0) | 50% |
| **B** | PF_lower≥1.0 + Exp≥2% + n≥5 | 30% |
| **C** | PF_lower≥0.7 + Exp≥1% + n≥5 | 15% |
| Q5b-lite C_RESCUE | n∈[3,4] + raw_PF≥3 + exp≥5% + |DD|≤25% + 無 holdout FAIL | 15% |
| **C_HIGH_Q_RESCUE** | n∈[5,9] + raw_PF≥3 + exp≥5% + |DD|≤25% + 無 holdout FAIL | 15% |
| **D** | PF_lower≥0.5 + Exp≥0% + n≥5 | 10% |
| **D_LOW_N_RESCUE** | n∈[3,4] + raw_PF≥5 + exp≥5% + |DD|≤25%（holdout 容忍） | 10% |
| **F** | 其他 | 0% |

BNH 平行評估（給 F-tier）：BNH_S / BNH_A / BNH_B（CAGR vs 0050 比較 + 股息）。

---

## 重要約束（永遠不要違反）

1. **時間防穿越**：所有訊號只能用 T 日及之前資料；成交在 T+1 開盤
2. **不引入回測框架**（vectorbt/backtrader/zipline）— 用 pandas 自刻
3. **參數集中** `config/strategy.yaml`，禁止 hardcode magic number
4. **錯誤落** `output/errors/{date}.csv`（用 `src/utils.log_error()`），不要 silent fail
5. **CSV 編碼** 一律 `utf-8-sig`
6. **敏感資料 gitignore**：`watchlists.yaml`、`trades_*.csv`、`positions_snapshot_*.csv`
7. **Windows print Unicode** → script 開頭 `sys.stdout.reconfigure(encoding="utf-8")`

---

## 過往重大重構紀錄

- **2026-05-18**：`templates.py` (4337 行) 拆為 `templates/` package 7 個模組
- **2026-05-17**：加入 5 個 Phase 2 ensemble (regime-aware + intersection 變種)
- **2026-05-16**：加入 5 個 Phase 1 ensemble (vote-based)，引入 ensemble 概念
- **2026-05-15**：加入 C_HIGH_Q_RESCUE + D_LOW_N_RESCUE tier rules；watchlist-based name lookup
- **2026-05-04**：限價單機制 v0.1（7 templates 改用 target_buy / target_tp / target_sl）
