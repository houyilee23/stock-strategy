# Round 2 回報 — Sonnet → Opus

產出日期：2026-04-23

---

## 1. 資料概況

| 項目 | 值 |
|------|----|
| `data/raw/0050.csv` 列數 | **3988 列** |
| 日期範圍 | 2010-01-04 ~ 2026-04-22 |
| 可用年數（2017+） | ~9.3 年 |

---

## 2. 本輪修改摘要

### P0-1：portfolio mode per-stock equity_curve 共用 bug
**檔案：** `src/strategy/backtest/engine.py`  
**改動：** 移除了把 portfolio_equity_curve 塞進每個 StockResult 的壞程式碼。  
**效果：** 各股 MaxDD 不再全部等於 -99.97%，各自獨立計算。

### P0-2：baseline CAGR 爆炸（1211%）
**檔案：** `src/strategy/runner.py`（`_calc_benchmark_cagr`）  
**改動：** 加入年數檢查，資料不足 1 年 raise ValueError 防止短期年化爆炸。  
**效果：** Sanity Gate E 驗證通過。

### P0-4：新增 Sanity Gates
**檔案：** `tests/test_sanity_gates.py`（全新）  
新增 5 個關卡：  
- A. 0050 buy-and-hold CAGR 在合理範圍（0.5%~20%）  
- B. portfolio equity 最終 > 初始 30%（未破產）  
- C. MaxDD 在 (-1, 0] 範圍內  
- D. per-stock PF 不全 < 0.5（目前 SKIP，因交易數不足）  
- E. 短資料 < 1 年時 ValueError 正確拋出  

### P0-5：portfolio mode 每日換倉 bug（本輪新發現）
**檔案：** `src/strategy/runner.py`  
**根因：** `top_n_equal_weight_sizing` 注釋寫「月頻 rebalance」，但 runner.py
在 sizing_fn 閉包裡**每日**呼叫 allocator，造成每天換倉。Katie 回測
-67.9% total loss 即由此而來（手續費/稅日日累積）。  
**改動：** 在 sizing_fn 閉包加月頻 gate：

```python
_last_rebalance = [None]
def sizing_fn(date, sig_dict, cash, ohlcv_dict, holdings):
    if _last_rebalance[0] == date.month and holdings:
        return holdings          # 非月初 → 維持現有持倉
    _last_rebalance[0] = date.month
    return top_n_equal_weight_sizing(...)
```

**效果：** Takeshi 組合 CAGR 4.31% → 14.44%；Katie -11.50% → -0.62%。

### P1-1：訊號報表趨勢欄拆分
**檔案：** `src/strategy/runner.py`、`src/strategy/eval/reporter.py`  
**改動：** 原「趨勢」欄拆為「個股趨勢」（Close>MA200 AND MA50>MA200）
與「市場Regime」（0050 BULL/BEAR）兩欄，9 欄輸出。  
**同時：** console 表格也更新為同樣兩欄。

### P1-2：entry_price 語意錯誤
**檔案：** `src/strategy/signals/style1_pullback.py`  
**改動：** 出場條件 #4 從「持倉 N 日未獲利」改為「持倉 N 日逾期出場」
（無條件出場）。因為 `entry_price=e_low` 是限價單建議，
不等於 T+1 實際成交開盤價，用它判斷「未獲利」語意錯誤。

### in_market_cagr 幾何複利修正
**檔案：** `src/strategy/backtest/result.py`  
**改動：** 改用幾何複利計算 + 加入最少 21 交易日保護（短期避免 CAGR 爆炸）。

---

## 3. Sanity Gates 全部通過證據

測試指令：`python -m pytest tests/test_sanity_gates.py -v`

```
tests/test_sanity_gates.py::test_0050_buyhold_cagr_reasonable  PASSED
tests/test_sanity_gates.py::test_portfolio_equity_not_bankrupt PASSED
tests/test_sanity_gates.py::test_portfolio_maxdd_range         PASSED
tests/test_sanity_gates.py::test_per_stock_pf_not_all_bad      SKIPPED (有效股票不足 3 檔)
tests/test_sanity_gates.py::test_baseline_cagr_rejects_short_data PASSED
======================== 4 passed, 1 skipped in 6.86s =========================
```

> Gate D（SKIP）：real data 中 Takeshi 清單只有 2382 達到 5 筆以上交易，
> 不足 3 檔有效樣本觸發評估。待 P0-3 改善訊號量後預期轉為 PASS。

全套測試（含 indicators / signals / backtest / cli）：44 passed, 1 skipped。

---

## 4. 回測完整結果（2017-01-01 ~ 2026-04-22）

### 4-A. Takeshi 個股回測（per-stock mode，初始資金 10 萬，全倉單股）

| 股票 | N | CAGR | MaxDD | PF | WR | AvgHold |
|------|---|------|-------|----|----|---------|
| 1301 | 1 | N/A | -1.72% | 0.00 | 0.0% | 4d |
| 1326 | 0 | N/A | — | ∞ | N/A | — |
| 6505 | 0 | N/A | — | ∞ | N/A | — |
| 1303 | 2 | **10.33%** | -4.95% | 3.65 | 50.0% | 44d |
| 1809 | 0 | N/A | — | ∞ | N/A | — |
| 2002 | 0 | N/A | — | ∞ | N/A | — |
| 6271 | 1 | N/A | -8.20% | 0.00 | 0.0% | 15d |
| 4958 | 2 | N/A | -11.24% | 0.00 | 0.0% | 9d |
| 2382 | 6 | -5.02% | -22.65% | 0.89 | 16.7% | 21d |
| 2337 | 3 | 5141%† | -26.98% | 3.16 | 66.7% | 16d |
| 2408 | 3 | N/A | -26.46% | 0.07 | 33.3% | 7d |
| 6770 | 0 | N/A | — | ∞ | N/A | — |

> †2337 CAGR=5141% 係異常值，見第 6 節說明。

### 4-B. Takeshi 組合回測（portfolio mode，初始資金 100 萬，max_pos 25%）

| 指標 | 數值 | 門檻 | 結果 |
|------|------|------|------|
| 組合 CAGR | **14.44%** | > 0050 (1.84%) | PASS |
| MaxDD | -41.47% | ≥ -30% | **FAIL** |
| Sharpe | **0.54** | ≥ 0.5 | PASS |
| Alpha vs 0050 | **+12.60%** | > 0% | PASS |
| 資金利用率 | 48.31% | — | — |
| 初始 equity | 1,000,000 | — | — |
| 最終 equity | 3,506,255 (+250.6%) | — | — |

### 4-C. Katie 個股回測（per-stock mode）

| 股票 | N | CAGR | MaxDD | PF | WR | AvgHold |
|------|---|------|-------|----|----|---------|
| 2330 | 3 | **74.90%** | -5.82% | 8.63 | 66.7% | 27d |
| 2303 | 5 | **34.56%** | -20.79% | 2.01 | 60.0% | 22d |
| 2426 | 1 | 139.41%† | -9.22% | ∞ | 100.0% | 23d |
| 1560 | 0 | N/A | — | ∞ | N/A | — |
| 9940 | 3 | -19.47% | -8.75% | 0.30 | 33.3% | 15d |
| 1227 | 2 | 3.35% | -9.76% | 1.09 | 50.0% | 22d |
| 1301 | 1 | N/A | -1.72% | 0.00 | 0.0% | 4d |
| 2324 | 4 | **95.11%** | -11.06% | 43.60 | 50.0% | 28d |
| 2344 | 0 | N/A | — | ∞ | N/A | — |

> †2426 僅 1 筆交易，統計意義低。

### 4-D. Katie 組合回測（portfolio mode，初始資金 100 萬，max_pos 25%）

| 指標 | 數值 | 門檻 | 結果 |
|------|------|------|------|
| 組合 CAGR | **-0.62%** | > 0050 (1.84%) | FAIL |
| MaxDD | -63.28% | ≥ -30% | **FAIL** |
| Sharpe | 0.19 | ≥ 0.5 | FAIL |
| Alpha vs 0050 | -2.46% | > 0% | FAIL |
| 資金利用率 | 59.88% | — | — |
| 最終 equity | 943,410 (-5.66%) | — | — |

---

## 5. 個股前 5 筆 trade 明細（1301）

| 進場日 | 進場價 | 出場日 | 出場價 | 報酬 | 持倉 |
|--------|--------|--------|--------|------|------|
| 2017-09-30 | 92.00 | 2017-10-06 | 91.50 | -1.72% | 4d |

> 1301 在 2017-2026 年間只產生 1 筆交易，高度稀疏問題的縮影。

---

## 6. 特殊說明：2337 CAGR = 5141%

2337（旺宏電子）共 3 筆交易：

| 進場日 | 進場價 | 出場日 | 出場價 | 報酬 | 持倉 |
|--------|--------|--------|--------|------|------|
| 2017-07-19 | 15.25 | 2017-08-29 | 40.70 | **+163.74%** | 20d |
| 2017-12-11 | 40.50 | 2018-01-11 | 41.15 | +0.41% | 22d |
| 2020-03-05 | 34.10 | 2020-03-13 | 27.70 | -19.73% | 6d |

Compound = 2.126，持倉共 48 交易日（0.190 年）→ CAGR = 2.126^(1/0.190) − 1 = 5141%。

**根因：** 第 1 筆 20 天內股價漲 3 倍（2017 半導體多頭，資料未調整除權息）。
僅 3 筆交易，`sufficient_trades` 過濾後此股排除在「有效樣本」之外。
CAGR 數字計算正確，但樣本不足，無統計意義。

---

## 7. P0-3：訊號稀疏問題診斷（待 Opus 決定方向）

### 現象

- Takeshi 12 檔，2017-2026 (9.3年)，共 21 筆交易 = **0.11 次/年/股**
- 12 檔中有 **7 檔完全 0 交易**
- Sanity Gate D 因此 SKIP（有效股票 < 3 檔）
- 回測結果統計上無法判斷策略好壞

### 根因

進場需同時滿足 5 個條件，任一不符即不進場：

1. `MA50 > MA200 AND Close > MA200`（長期趨勢）
2. 大盤 BULL（0050 regime，佔 60.1% 時間）
3. `RSI < 40 OR Close < BollLower`（短期回檔）
4. `Close > Open AND Close > prev_Close`（反轉K棒）
5. `Volume > vol_ma × 0.8`（量能確認）

條件 3 + 4 + 5 同時成立的機率極低。即使前兩項已篩掉 40% 時段，
後三項同時成立估計不到 5% 的交易日。

**出場過快（whipsaw）：** 進場時 Close 僅略高於 MA200（例如 1301：
close=91.8, MA200=91.4），`trend_break_days=2` 日 <MA200 即觸發出場，
4 天後就被震出（1301 平均持倉 4 天）。

### 建議選項（請 Opus 決定）

| 選項 | 改動 | 預期效果 |
|------|------|---------|
| A | Close > MA200 × 1.02（加 2% 緩衝） | 減少 whipsaw，進場品質更高 |
| B | `trend_break_days` 2 → 4 天 | 持倉延長，減少噪音出場 |
| C | `rsi_oversold` 40 → 35 | 更嚴格的回檔才進場，提高進場精準度 |
| D | A + B 組合 | 同時提升品質與抗震能力 |
| E | 進一步放寬 `volume_min_ratio` 或移除反轉K棒條件 | 增加訊號量（但可能降低品質） |

---

## 8. 剩餘待解問題

| 問題 | 狀態 | 說明 |
|------|------|------|
| P0-3 訊號稀疏 | **待 Opus 決定** | 參數方向需確認後 Sonnet 實作 |
| Katie MaxDD -63.28% | **待 Opus 決定** | 可能需調整清單或加 MaxDD 過濾 |
| Gate D (per-stock PF) | SKIP → 待 P0-3 修正 | 交易數足夠後自動恢復 |
| 2337 樣本外異常 | 已說明，不處理 | sufficient_trades 已可過濾 |

---

*Sonnet 回報完畢，等待 Opus 審查與 P0-3 方向指示。*
