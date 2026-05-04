# Sonnet 修正回合 #3 — Portfolio Mode 嚴重 Bug

> Round 2 解了大部分問題，但 Katie -63% MaxDD 暴露 portfolio mode 的根本漏洞。
> 本輪聚焦三個 portfolio bug，**先不動 Style 1 訊號參數**（其品質實際上很好）。

---

## 為什麼不動 Style 1？

Round 2 結果顯示：
- 21 筆交易 PF 普遍 > 2（1303=3.65、2330=8.63、2324=43.6、2303=2.01）
- 訊號**品質高、頻率低**——這是好事，不是問題
- Takeshi 組合 CAGR 14.4% / Alpha +12.6% 已贏 0050

P0-3「訊號稀疏」是表象。真正讓 Katie 爆掉的不是訊號頻率，是 portfolio mode 漏實作 SPEC §5.2 規定的 regime filter，導致整套策略在熊市裸奔。

修完本輪三個 bug 再評估 Style 1 是否需動。

---

## 必修問題

### 🔴 P0-6：Style 2 缺 regime filter（SPEC §5.2 step 2）

**位置**：`src/strategy/signals/style2_momentum.py` 的 `rank_universe()`

**SPEC 原文**：
> 1. 對 watchlist 每檔計算 12-1 月動量
> 2. 套用 regime filter (5.1 #2)；**regime FAIL 時整體現金**
> 3. 取動量排名前 N 檔

**現況**：實作只做了 1 和 3，跳過 2。

**修法**：
1. `rank_universe()` 新增參數 `market_regime: pd.Series`（與 0050 對齊）
2. 在 `asof_date` 查 regime，若 == "BEAR" 直接回傳空 DataFrame（代表整體現金）
3. `runner.py` 計算 0050 regime 後傳入 allocator
4. `allocator.top_n_equal_weight_sizing()` 收到空 ranking 時，回傳 `{sid: 0 for sid in current_holdings}`（清倉）

### 🔴 P0-7：portfolio mode 的 SELL 篩選太寬鬆

**位置**：`src/strategy/portfolio/allocator.py:36-43`

**現況**：
```python
last_action = sig_sub["action"].iloc[-1]
if last_action != "SELL":
    selected.append(sid)
```

問題：Style 1 大多數日子 `action=HOLD`，意思是「沒有事件發生」，不是「該持有」。這個過濾相當於沒過濾。

**修法**：改成「需要看是否處於『style1 進場條件可成立』狀態」。具體實作：
- 在 sigals_dict 裡每檔股票多算一個欄位 `in_uptrend`（= `Close > MA200 AND MA50 > MA200`）
- allocator 篩選條件改為：`in_uptrend.loc[date] == True` AND `last_action != "SELL"`
- 這樣 portfolio 只買「個股本身在多頭排列中」的標的

如果改起來介面變動太大，退而求其次：直接在 allocator 裡讀 ohlcv 即時計算 `Close > MA200`，不依賴 signals_dict 新增欄位。

### 🔴 P0-8：sizing 公式造成 100% 滿倉，沒有現金緩衝

**位置**：`src/strategy/portfolio/allocator.py:54`

**現況**：`alloc_per_stock = min(total/N, total*max_position_pct)` — top_n=5 時 20% × 5 = 100% 滿倉。

**修法**：保留現金緩衝。改為：
```python
# config 新增 cash_reserve_pct，預設 0.20（保留 20% 現金）
investable = total_value * (1 - params.get("cash_reserve_pct", 0.20))
alloc_per_stock = min(investable / len(selected), total_value * max_position_pct)
```

並在 `config/strategy.yaml` 的 `style2_momentum` 區段加：
```yaml
cash_reserve_pct: 0.20
```

---

## 同時要做的驗證強化

### 加新 sanity gate

```python
# tests/test_sanity_gates.py 加一條
def test_portfolio_maxdd_within_threshold():
    """組合 MaxDD 必須 ≤ 35%（門檻 30%，留 5% 容差）"""
    # 對 Katie 跑一次組合回測
    result = run_katie_portfolio_backtest()
    assert result.max_drawdown >= -0.35, \
        f"Katie 組合 MaxDD={result.max_drawdown:.1%} 超過 35% 門檻"
```

### 加 regime 統計輸出

每次 portfolio 回測完，print 出：
- BULL 期間佔比 / BEAR 期間佔比
- BEAR 期間是否真的清倉（資金利用率應為 0%）

---

## 執行順序

1. **修 P0-6**（regime filter） — 最重要
2. **修 P0-7**（in_uptrend 篩選） — 次要
3. **修 P0-8**（cash reserve） — 細修
4. 重跑 Takeshi + Katie portfolio 回測
5. 驗證 sanity gates 全過

---

## 預期結果（修完應達到）

| 指標 | Takeshi 目前 | Takeshi 預期 | Katie 目前 | Katie 預期 |
|---|---|---|---|---|
| CAGR | 14.4% | 維持或略降 | -0.6% | > 0%（至少打平 0050） |
| MaxDD | -41.5% | **降到 -30% 內** | -63.3% | **降到 -30% 內** |
| Sharpe | 0.54 | 維持 | 0.19 | > 0.5 |
| Alpha vs 0050 | +12.6% | 維持 | -2.5% | 接近 0 或正 |

**注意**：CAGR 可能因為加 regime filter 在熊市清倉、加現金緩衝而下降，這是正常的。重點是 MaxDD 必須符合門檻。

---

## 不要做的事

- ❌ **不要動 Style 1 的 ma_long / atr_stop_k / trend_break_days / rsi 任何參數**（除非修完上面三個 bug 後 MaxDD 還超標）
- ❌ 不要動 `config/watchlists.yaml`
- ❌ 不要為了讓 sanity gate 過而把門檻調寬
- ❌ 不要為了補訊號量改 Style 1 進場條件
- ❌ 不要修現有的 indicator/Style 1/backtest engine（這些已驗證過）

---

## 回報格式

修完後提供：

1. P0-6/7/8 各自改了什麼檔案、什麼行（diff 摘要）
2. Takeshi + Katie portfolio 完整指標表（用上面的預期表格格式）
3. Regime 統計：BULL/BEAR 期間佔比、BEAR 期間實際資金利用率
4. 新增 sanity gate 的測試輸出
5. 若 Katie MaxDD 仍 > -30%，主動列出可能原因（不要硬調參數）
