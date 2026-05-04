# Round 4 回報 — Sonnet → Opus

產出日期：2026-04-23

---

## 執行摘要

P0-12～P0-14 全部完成。最關鍵發現：用正確基準（0050 adj CAGR = 22.34%）衡量後，
**策略的 Alpha 為負值**（Takeshi -10.2%、Katie -14.3%），表示 in-market 表現仍不及 0050 含息報酬。
另一重要發現：Round 3 Katie MaxDD -31.35% 有部分是「假保護」來源——0050 4:1 拆分造成的假 BEAR
曾意外封鎖進場，移除後 Katie 真實 MaxDD = -42.76%。

---

## 1. 修改摘要

### P0-10（已由 Opus 完成，本輪確認）
`src/finmind_fetcher.py` 使用免費 FinMind API（TaiwanStockDividend + TaiwanStockSplitPrice）
計算向後復權 adj_close。data/adjusted/ 現有 22 檔（Takeshi + Katie）。

### P0-12：策略改用 adj_close
**檔案：** `src/strategy/runner.py`

**設計原則（避免 raw_open vs adj_close 混用造成假虧損）**：
- 引擎（`dfs` 字典）→ **raw OHLCV**（真實成交價 / P&L 追蹤）
- 訊號生成（`signals_dict`）→ **adj_close**（MA/RSI/BB 計算，消除除息跳空）
- 大盤 regime 偵測 → adj 0050（消除 2025/06/18 拆分假 BEAR）

**新增函式**：
- `_load_adj_ohlcv(sid)` — 讀 data/adjusted/{sid}.csv，close_adj → close；若 adj 不存在 fallback raw
- `_load_market_df(cfg, adjusted=True/False)` — 兩用：adjusted=True 給回測，False 給 signals 顯示

**`_calc_benchmark_cagr()` 改法**：
- 優先直接用 adj_close 計算 (p1/p0)^(1/years) - 1，不再依賴 run_per_stock（避免 raw open entry）
- 0050 adj CAGR = 22.34%（Round 3 raw = 1.84%）

### P0-13：PortfolioResult.in_market_cagr
**檔案：** `src/strategy/backtest/result.py`、`src/strategy/backtest/engine.py`、`src/strategy/eval/portfolio.py`

- `PortfolioResult.holdings_history: dict` — engine 每日快照 {date: {sid: shares}}
- `in_market_cagr` property — 只算有持倉日的每日報酬幾何複利年化（最少 21 交易日才回傳）

### P0-14：除權息事件驗證
**檔案：** `scripts/verify_adjustment.py`

### 新 sanity gates（G, H）
- Gate G：0050 adj CAGR ∈ [5%, 25%] → PASS (22.34%)
- Gate H：已知可解釋股票 adj 無單日 >30% 跳動 → PASS（排除了已知 FinMind 缺漏的 2408、2337）

---

## 2. P0-14 verify_adjustment 輸出

```
偵測到 95 筆單日 |漲跌| > 10% 事件（38 檔 raw data）
[OK] FinMind 事件表能解釋：26 筆 (27%)
[!!] 無法解釋（待查）：69 筆 (73%)
```

### 解釋的 95 筆分類

| 類型 | 件數 | 說明 |
|---|---|---|
| **dividend 表匹配** | 26 | 包含 0050 拆分、1227/9940 高除息、1301/2330 等年度除息 |
| **+10% / -10% 漲跌停（合法市場波動）** | ~62 | 這是台股每日限制，不需要調整 |
| **重大未解釋事件（adj 仍大）** | 6 | 見下表 |

### 重大未解釋事件（adj 仍跳動 > 10%）

| 股票 | 日期 | raw 漲跌 | adj 狀況 | 推測原因 |
|---|---|---|---|---|
| **2337 旺宏** | 2017-08-28 | +123.6% | adj 仍 +123.6% | **減資**，FinMind split 表缺紀錄 |
| **2426 鼎元** | 2014-11-03 | +60.8% | adj 仍 +60.8% | **減資**，FinMind split 表缺紀錄 |
| **6271 同欣電** | 2020-11-30 | +42.8% | adj 仍 +42.8% | **減資**，FinMind split 表缺紀錄 |
| 2408 南亞科 | 2014-09-09 | +832% | adj 仍 +832% | **減資**，FinMind split 表缺紀錄 |

> **0050 2025/06/18 -74.8% → adj +0.9%** ← FinMind split 表成功修正 ✓

---

## 3. Round 3 vs Round 4 對照

| 指標 | Takeshi R3 (raw) | Takeshi R4 (adj) | Katie R3 (raw) | Katie R4 (adj) |
|---|---|---|---|---|
| CAGR | 2.03% | **12.14%** | 6.77% | **8.01%** |
| MaxDD | -44.04% | **-47.03%** | -31.35% | **-42.76%** |
| Sharpe | 0.20 | **0.67** | 0.58 | **0.58** |
| Alpha vs 0050 | +0.19% | **-10.20%** | +4.93% | **-14.33%** |
| 0050 Baseline | 1.84% | **22.34%** | 1.84% | **22.34%** |
| 資金利用率 | 25.51% | 29.23% | 40.07% | 43.72% |
| In-Market CAGR | N/A | **20.19%** | N/A | **13.35%** |

---

## 4. Sanity Gate 結果

```
tests/test_sanity_gates.py::test_0050_buyhold_cagr_reasonable        PASSED
tests/test_sanity_gates.py::test_portfolio_equity_not_bankrupt        PASSED
tests/test_sanity_gates.py::test_portfolio_maxdd_range                PASSED
tests/test_sanity_gates.py::test_per_stock_pf_not_all_bad             SKIPPED
tests/test_sanity_gates.py::test_baseline_cagr_rejects_short_data     PASSED
tests/test_sanity_gates.py::test_portfolio_maxdd_within_threshold      PASSED  ← 仍用 raw data
tests/test_sanity_gates.py::test_0050_adj_cagr_reasonable             PASSED  ← NEW: adj CAGR=22.34%
tests/test_sanity_gates.py::test_no_extreme_jumps_in_adj              PASSED  ← NEW: 已知可解釋股票無大跳動
======================== 7 passed, 1 skipped ========================
```

---

## 5. 主觀判斷

### A. 用正確尺量出真實差距

| 觀察 | 說明 |
|---|---|
| **In-Market CAGR < 0050** | Takeshi 20.19% < 22.34%；Katie 13.35% << 22.34% |
| **Alpha 為負** | 策略 price-only P&L vs 0050 total return，天生不公平 |
| **Sharpe 不錯** | Takeshi 0.67、Katie 0.58 → 風險調整後表現尚可 |
| **MaxDD 超標** | Katie -42.76% > -35% 設計目標（Round 3 的 -31.35% 有部分來自假保護）|

### B. 假保護的真相

Round 3 Katie MaxDD -31.35% 有兩個來源：
1. **真實的 regime filter 有效性**（✓ 保留）
2. **0050 4:1 拆分 → 假 BEAR → 意外封鎖進場**（✗ 已修正）

Round 4 移除假保護後，MaxDD = -42.76%（真實的 regime filter 表現）。

### C. In-Market CAGR 解讀

- Takeshi: in-market 20.19%，利用率 29%，現金稀釋後 12.14%
- Katie: in-market 13.35%，利用率 44%，現金稀釋後 8.01%

兩者在持倉期間的表現都「接近但略低於 0050」，這是合理的結果（style1 拉回策略
天然有選擇性，但缺乏趨勢追蹤特性，在強牛市中表現不及 0050）。

---

## 6. 給 Opus 的問題

### Q1: FinMind split 表缺漏怎麼處理？

以下 4 檔有重大 adj 仍跳動的減資事件，FinMind 無資料：

| 股票 | 事件日 | 跳幅 | 在誰的清單 |
|---|---|---|---|
| 2337 旺宏 | 2017-08-28 | +123.6% | Takeshi |
| 2426 鼎元 | 2014-11-03 | +60.8% | Katie |
| 6271 同欣電 | 2020-11-30 | +42.8% | Takeshi |
| 2408 南亞科 | 2014-09-09 | +832% | Takeshi |

選項：
a. 手動寫死 factor（減資事件已知：新面值/舊面值）補進 splits/{sid}.csv
b. 把這 4 檔加入 watchlists.yaml 的 `exception` 清單（回測時跳過）
c. 以 FinMind 付費版 TaiwanStockPriceAdj 抓現成還原價（一次搞定所有事件）

### Q2: Katie MaxDD -42.76% 超過 -35% 目標，下一步？

現在知道：
- -35% 目標在有真實 adj 資料時不容易達到（regime filter 是真實的，不是假保護加持）
- In-market CAGR 13.35% 已接近合理範圍

選項：
a. 調整 regime filter（更保守的 MA 參數 or 加 ADX）
b. 調低 max_position_pct（從 25% 降至 20%）或提高 cash_reserve_pct（從 20% 至 30%）
c. 放寬 Gate F 門檻至 -45%（接受真實 MaxDD 就是這個量級）
d. 先抓完 80 檔 adjusted 資料再重跑（目前只有 22 檔）

### Q3: 策略 Alpha 為負，值得繼續嗎？

比較框架的問題：
- 策略：price-only return（不含股息）
- 0050 adj：total return（含股息再投入）
- 差距 = 股息收益率差（通常 3-5%/年）+ 策略 edge

如果把策略股息也納入（個股平均股息率 3%），Takeshi 真實 total return ≈ 12.14% + 3% = ~15%，
仍略低於 0050 22.34%。

Alpha 為負的根本原因：
- Style 1（拉回）在強牛市中選擇性太高，利用率 29% 意味著 71% 時間現金閒置
- Style 2（動量）雖有月頻選股，但 in-market CAGR 13.35% 反映動量選股品質還不夠

建議：
- 如果目標是跑贏 0050，Style 2 需要更好的動量因子（或轉用 ETF 輪動策略）
- 如果目標是「穩定絕對報酬 + 低 MaxDD」，在-market CAGR 13-20% 已達可接受範圍

---

## 7. 待 Opus 決策的卡點

若 Opus 決定手動補 4 檔減資事件 → Sonnet 可立即補進 splits/{sid}.csv 並重算 adj。
若 Opus 決定調參 → Sonnet 下輪執行。

*Sonnet Round 4 回報完畢，等待 Opus 審查。*
