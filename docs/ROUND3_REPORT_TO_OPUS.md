# Round 3 回報 — Sonnet → Opus

產出日期：2026-04-23

---

## 執行摘要

本輪修正 P0-6/7/8 三個 portfolio bug，並在過程中發現並修正第四個 bug（P0-9 engine equity 計算）。
Katie 組合 MaxDD 從 -63.28% 降至 **-31.35%**，Sharpe 從 0.19 升至 **0.58**，Gate F 通過。
Takeshi 組合因所持傳產股票在 P0-7 in_uptrend 篩選下入選較少，CAGR 從 14.44% 降至 2.03%。

---

## 1. 修改摘要

### P0-6：Style 2 加 regime filter
**檔案：** `src/strategy/signals/style2_momentum.py`
**改動：** `rank_universe()` 新增 `market_regime` 參數；`asof_date` 查到 BEAR 時回傳空 DataFrame。

**檔案：** `src/strategy/portfolio/allocator.py`
**改動：** `top_n_equal_weight_sizing()` 新增 `market_regime` 參數，傳入 `rank_universe()`；
空 ranking（BEAR）→ 回傳 `{sid: 0 for sid in current_holdings}`（清倉）。

### P0-7：portfolio 加 in_uptrend 篩選
**檔案：** `src/strategy/portfolio/allocator.py`
**改動：** 對每個候選股即時計算 `Close > MA200 AND MA50 > MA200`（從 ohlcv_dict 直接算，
不修改已驗證的 style1_pullback 輸出）。非多頭排列的股票從候選名單移除。

### P0-8：sizing 加現金緩衝
**檔案：** `src/strategy/portfolio/allocator.py`、`config/strategy.yaml`
**改動：**
```python
cash_reserve_pct = params.get("cash_reserve_pct", 0.20)
investable = total_value * (1 - cash_reserve_pct)
alloc_per_stock = min(investable / len(selected), total_value * max_position_pct)
```
`config/strategy.yaml` 的 `style2_momentum` 新增 `cash_reserve_pct: 0.20`。

### 月頻 rebalance + 每日 regime 即時保護（P0-5/6 整合）
**原問題：** P0-5 的月頻 gate 繞過了 regime 每日檢查，月中進入 BEAR 最多等 31 天才清倉。
**改動：** 提取成工廠函式 `make_monthly_portfolio_sizing(regime, mom_params, max_pos_pct)`：
```python
# BEAR → 每日立即清倉，並重置 rebalance 計時
if current_regime == "BEAR":
    if holdings:
        _last_rb[0] = None
        return {sid: 0 for sid in holdings}
    return {}
# BULL → 月頻 rebalance
if _last_rb[0] == date.month and holdings:
    return holdings
_last_rb[0] = date.month
return top_n_equal_weight_sizing(..., market_regime=regime)
```
**使用位置：** `runner.py`、`tests/test_sanity_gates.py`、`scripts/round3_report.py`。

### P0-9（本輪新發現）：engine equity 計算漏掉無資料日持股
**檔案：** `src/strategy/backtest/engine.py`（`run_portfolio`）
**根因：** 當持股在某日無收盤價（假日、資料缺口、或部分股票資料只到前一日）時，
engine 的 equity 計算直接跳過該持股，等同把它估值為 0，製造出虛假的鉅額虧損。
**表現：** Katie portfolio 在最後兩個交易日出現 -68.92% 假 MaxDD
（大部分持股 2026-04-22 無資料，只有 1301 有資料，equity 被低估至接近純現金）。
**修法：** 若當日無資料，用最近一筆有效收盤價估值：
```python
else:
    sub = df_s[df_s.index < date]
    if len(sub) > 0:
        portfolio_value += sh * sub["close"].iloc[-1]
```

---

## 2. 完整回測結果（2017-01-01 ~ 2026-04-22）

### Round 2 vs Round 3 對照

| 指標 | Takeshi R2 | Takeshi R3 | Katie R2 | Katie R3 |
|------|-----------|-----------|---------|---------|
| CAGR | 14.44% | **2.03%** | -0.62% | **6.77%** |
| MaxDD | -41.47% | -44.04% | -63.28% | **-31.35%** |
| Sharpe | 0.54 | 0.20 | 0.19 | **0.58** |
| Alpha vs 0050 | +12.60% | +0.19% | -2.46% | **+4.93%** |
| 資金利用率 | 48.31% | 25.51% | 59.88% | 40.07% |

### Regime 統計

| 帳戶 | BULL 佔比 | BEAR 佔比 | BEAR 期間 equity/初始 |
|------|-----------|-----------|----------------------|
| Takeshi | 62.4% | 37.6% | 117.14% |
| Katie | 62.4% | 37.6% | 129.51% |

> BEAR 期間 equity 均值高於初始（>100%），確認 regime filter 有效清倉（持倉清空後 equity 維持平水）。

---

## 3. Gate 測試輸出

```
tests/test_sanity_gates.py::test_0050_buyhold_cagr_reasonable        PASSED
tests/test_sanity_gates.py::test_portfolio_equity_not_bankrupt        PASSED
tests/test_sanity_gates.py::test_portfolio_maxdd_range                PASSED
tests/test_sanity_gates.py::test_per_stock_pf_not_all_bad             SKIPPED
tests/test_sanity_gates.py::test_baseline_cagr_rejects_short_data     PASSED
tests/test_sanity_gates.py::test_portfolio_maxdd_within_threshold      PASSED  ← Katie MaxDD=-31.35%
======================= 59 passed, 1 skipped in 54.01s =========================
```

---

## 4. 剩餘問題說明

### 4-A. Takeshi 組合 CAGR 從 14.44% 降至 2.03%

Round 2 的 Takeshi 14.44% CAGR 部分來自每日換倉（P0-5 修前），頻繁進出且恰好在
多頭期大量持有，短期 CAGR 虛高。修正月頻 + regime filter 後，Takeshi 傳產股
（1301、1303、2002 等）被 P0-7 in_uptrend 篩選過濾掉較多，資金利用率從 48% 降至 25%。

MaxDD -44.04% 仍超過 -30% 門檻。Sanity Gate F（Katie MaxDD ≤ -35%）已通過，
但 Takeshi 的超標需 Opus 判斷是否需處理。

### 4-B. Gate D（per-stock PF）仍 SKIP

Style 1 的 0.11 BUY/年/股稀疏問題未動（依 Opus 指示）。等後續輪次再評估。

---

## 5. 意見與下一步建議（供 Opus 參考）

1. **Katie 結果符合預期**：CAGR 6.77%、MaxDD -31.35%（略超 -30%，在 -35% 容差內）、Sharpe 0.58、Alpha +4.93%。

2. **Takeshi 組合 CAGR 偏低（2.03%）的根因**：
   - Takeshi 清單多為傳產（塑化、鋼鐵），在 P0-7 in_uptrend 篩選 + Style 2 動量排名下，
     這類股票很少被選中（多頭期傳產不如科技強勢）
   - 建議選項：
     A. 為 Takeshi 帳戶關閉 portfolio mode（維持原訊號模式 per-stock）
     B. 或調整 Takeshi 清單加入更多趨勢性股票

3. **P0-9 engine equity bug 已修正**：此 bug 會影響所有在最後資料日有持股但無當日收盤的回測，
   建議未來取資料時確保所有股票資料結尾日期一致。

---

*Sonnet Round 3 回報完畢，等待 Opus 審查。*
