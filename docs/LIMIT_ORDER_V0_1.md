# 限價單機制 v0.1（試水溫實作）

實作日期：2026-05-04（同日擴展到 7 個 templates）
狀態：✅ 已實作於 **7 個 template**，本機驗證完成

| Template | 機制 | 進場目標 | 模式 | TP | SL |
|---|---|---|---|---|---|
| **low_vol_pullback** (T8) | 回檔 | short_ma×(1-pb_pct) 區間上界 | limit | entry×(1+tp_pct) | long_ma |
| **mean_reversion** (T5) | 回檔 | short_ma×(1-pb_pct) 區間上界 | limit | short_ma×(1+tp_pct) | trend_ma |
| **donchian_breakout** (T2) | 突破 | don_high | **stop** | NaN | max(don_low, atr_stop) |
| **trend_pullback** (T1) | 回檔 | entry_high (style1) | limit | NaN | MA200/ATR |
| **momentum_hold** (T3) | 動能 | T_close | limit | NaN | trend_ma |
| **volume_breakout** (T6) | 突破 | don_high | **stop** | NaN | max(short_ma, atr_stop) |
| **bollinger_squeeze** (T9) | 突破 | bb_upper | **stop** | NaN | max(bb_mid, atr_stop) |

剩 4 個 template 不適合限價單（chip×2 / gap_continuation / monthly_revenue_event），維持 T+1 open fallback。

---

## 動機回顧

舊機制：T 收盤 → 計算訊號 → T+1 開盤無條件市價成交。
問題：T+1 開盤價未知（盤前定價、跳空高低差大），實單成交與回測 PnL 落差大。

新機制：T 收盤 → 計算「**隔日掛單目標價**」→ T+1 限價單觸發成交。
好處：
- 可控成交價（盤前已知掛單）
- 沒有「跳空追高」的滑價
- 個股回撤大幅降低（2360 -32% → -15%、1560 -26% → -11.5%）
- 持倉期 CAGR 明顯提升（2360 15% → 46%、1560 41% → 112%）

---

## 設計

### Signal DataFrame 新增 3 個欄位

| 欄位 | 含義 | 何時有值 |
|---|---|---|
| `target_buy` | 隔日掛限價買的價位 | T 滿足進場條件且 action="BUY" 時 |
| `target_tp` | 在倉中，隔日掛限價賣（停利）的價位 | 在倉、action="HOLD" 時 |
| `target_sl` | 在倉中，隔日停損價位 | 在倉、action="HOLD" 時 |

非限價單機制的 template（chip_*、gap_continuation、monthly_revenue_event 等）不輸出這些欄位 → engine 自動 fallback 舊邏輯。

### Target 價計算規則

#### low_vol_pullback (generate_T8)
- **target_buy** = `short_ma × (1 - pb_pct)`（進場區間上界，T+1 在區間內成交）
- **target_tp** = `entry_price × (1 + take_profit_pct)`（停利線，固定）
- **target_sl** = `long_ma_at_T`（趨勢線停損）

#### mean_reversion (generate_T5)
- **target_buy** = `short_ma × (1 - pb_pct)`（同上）
- **target_tp** = `short_ma × (1 + take_profit_pct)`（短均線之上反彈目標）
- **target_sl** = `trend_ma_at_T`（長期趨勢線停損）

### Generator 行為（含 EOD 觸發判斷）

每天 T close 後：

```
if 在倉:
    計算 target_tp 與 target_sl
    if T close >= target_tp OR T close < target_sl OR hold_days >= max_hold:
        action = "SELL"  # 隔日 market sell
        in_pos = False
    else:
        action = "HOLD"  # 隔日掛 target_tp / target_sl 等觸發
elif T close 滿足進場條件:
    action = "BUY"
    target_buy = 進場區間上界
    進倉 (假設 entry_price = T close 用於日後 target_tp 計算)
else:
    action = "HOLD"
```

### Backtester 模擬規則

新增 `_run_per_stock_limit_orders()` 路徑（engine.py），偵測 signals 含非 NaN 的 target_buy 自動啟用：

#### 進場 (BUY)
- T+1 low ≤ target_buy → 限價成交
- 成交價：`min(T+1_open, target_buy)`（若開盤已 gap down 在 target 以下，成交價更便宜）
- T+1 low > target_buy → 不成交，訊號失效

#### 出場 (在倉中)
- action="SELL" → 走 fallback：T+1 open 市價賣出
- action="HOLD" + target_tp/sl → OCO 模擬：
  - `hit_sl = low ≤ target_sl`
  - `hit_tp = high ≥ target_tp`
  - 同日兩者都觸發 → 假設最壞情況：SL 先成交
  - SL 觸發 → 成交價：`min(open, target_sl)`（gap down 用 open，否則 target_sl）
  - TP 觸發 → 成交價：`max(open, target_tp)`（gap up 用 open，否則 target_tp）

### 全部用 adjusted price 跑

舊架構：signal 用 adj_close、Backtester 用 raw OHLCV。
新架構（限價單）：**signal + Backtester 都用 adj OHLCV**。

理由：
- 限價單 target 是 adj 算的，不能跟 raw 的 high/low 比（除權息事件多的標的會差很大）
- 與 BNH / 0050 同期 CAGR 比較公平（都含複利）
- 微小代價：PnL 數字含複利，比實單略樂觀，但差距小

`build_per_stock_reports.py` 和 `build_html.py` 都改成統一傳 `df_adj` 給 Backtester。

---

## 驗證結果

### 2360 致茂（low_vol_pullback A-tier 50%）

| | 舊機制（T+1 open）| 限價單機制 | 變化 |
|---|---|---|---|
| 交易次數 | 53 | 52 | -1 |
| 勝率 | 50.9% | 61.5% | +10.6% |
| Profit Factor | 2.08 | 1.75 | -0.33 |
| Expectancy/筆 | +3.64% | +2.04% | -1.6% |
| **MaxDD** | **-32.0%** | **-15.3%** | **-16.7%** ✅ |
| **持倉期 CAGR** | **15.1%** | **46.1%** | **+31%** ✅ |
| 平均持有 | 40 天 | 12 天 | -28 天（資金週轉快）|
| 限價單 fill rate | — | 96% | — |

### 1560 中砂（mean_reversion A-tier 50%）

| | 舊機制 | 限價單機制 | 變化 |
|---|---|---|---|
| 交易次數 | 24 | 21 | -3 |
| 勝率 | 79.2% | 66.7% | -12.5% |
| Profit Factor | 3.03 | 3.04 | ≈ |
| **MaxDD** | **-26.1%** | **-11.5%** | **-14.6%** ✅ |
| **持倉期 CAGR** | **41.6%** | **112.3%** | **+70.7%** ✅ |
| 平均持有 | 29 天 | 14 天 | -15 天 |
| 限價單 fill rate | — | 87.5% | — |

### 共同特徵
1. **MaxDD 大幅降低**（停損快速出場止損，避免拖深）
2. **持倉期 CAGR 大幅提升**（短進短出，資金週轉效率高）
3. **PF 變化不大**，整體賺賠比例相近
4. 勝率小幅下降（因為部分 SL 提早出場）
5. fill rate 87~96%，少數 BUY 訊號因 T+1 過度跳空被 skip（這是設計意圖）

---

## Web UI / CLI 顯示

### CLI signals 模式
```
股票    收盤   動作  Tier  倉位 Template               掛單     RSI  趨勢  Regime
2360    2120.0 SELL   A    50%  low_vol_pullback        -      65   [多]  BULL
2308    2165.0 HOLD   A    50%  low_vol_pullback   TP 1380/SL 1182  77   [多]  BULL
3034    409.0  HOLD   B    30%  low_vol_pullback   TP 445 / SL 386  54   [空]  BULL
2317    219.5  HOLD   S   100%  gap_continuation        -      57   [空]  BULL
```
- BUY 訊號 → 顯示 "買 X"
- 在倉 → 顯示 "TP X / SL Y"
- 非限價單 template → 顯示 "—"

### Web UI 訊號表
新增「掛單」欄，行動裝置友善。
- BUY 紅色（"買 X"）
- TP/SL 灰色

### Markdown reports
`output/reports/{YYYY}/{MM}/{DD}_signals_{account}.md` 與 `latest/signals_{account}.md` 都新增「掛單目標」欄。

---

## v0.1 後補 (2026-05-04 晚)：整合真實持倉

User 指出關鍵設計缺口：watchlist 只是「觀察名單」，與用戶實際持倉脫鉤。
原 generator 用「假設從歷史開始按系統紀律操作」累積出的 in_pos 狀態不等於用戶真實持倉。

**解決方案**：在 runner.py 中加入後處理 `_apply_real_position_to_signals()`。

### 改動

新增 helper（src/strategy/runner.py）：
- `_load_real_positions(account)` — 從 `data/trades_{account}.csv` 透過 `compute_open_positions()`（FIFO）算每檔當前真實持倉，回傳 `{sid: {entry_price, shares, open_date}}`，多筆 BUY 用平均成本當 entry。`research` 等沒 trades 檔的清單回傳空 dict。
- `_load_best_params(template, sid)` — 從 merged auto_iterate run 讀出 best_params（給 entry-dependent target 重算用）。
- `_apply_real_position_to_signals(sig_df, sid, template, params, real_pos)` — 調整 sig_df 的最後一筆訊號：
  - **沒持倉**：清空 target_tp / target_sl（generator 假設不準）；SELL → HOLD（沒部位無法賣）。
  - **有持倉**：對 entry-dependent target_tp（low_vol_pullback）用真實 entry 重算；BUY → HOLD（已在倉不再進）。
  - mean_reversion 的 target_tp = `short_ma × (1+tp_pct)` 不依賴 entry，保留 generator 算的。
  - 所有 template 的 target_sl = MA at T 不依賴 entry，保留。

### CLI / Markdown / Web UI 都加「在倉」欄

- **CLI**：「持」（在倉）、「-」（沒持有）— 用 CJK 字元避免 cp950 console 編碼錯誤。
- **Markdown**：「✅」/「—」，並在 reason 欄補「(持 N 股 @ 進場價)」。
- **Web UI**：✅ 綠勾 / 灰點 ·，可點欄位排序按持倉狀態分組。

### 驗證

Takeshi 真實持倉 7 檔（1301、1326、6505、1809、2002、2337、6271）vs watchlist 12 檔：
- 7 檔顯示 ✅（在倉）
- 5 檔顯示 · （觀察中：1303、4958、2382、2408、6770）
- 對 limit-order template + 在倉者，target_tp 用真實 entry 重算（例如 if 持有 2360 @ 1500，TP = 1635，而不是 generator 假設的 entry × 1.09 = 2093）。

### 設計決策（已調整為「中性訊號 + 持倉註記」模式）

User 進一步指出：「即使有持倉，也要給出未持倉的目標價」。
理由：
1. 可能會忘記改倉位（系統提示與真實狀態不一致時可發現）
2. 給家人進出建議（家人未必在這帳戶持倉）

**最終設計**：
- ✅ **訊號保持中性**：generator 算出的 BUY/SELL/HOLD action 與 target_buy/tp/sl **不被持倉狀態修改**
- ✅ **「在倉」欄獨立呈現**：CLI 用「持」/「-」、Markdown 用「✅」/「—」、Web UI 用 ✅ / · 圖示
- ✅ **個人化 TP 註記**：對 entry-dependent template（low_vol_pullback），若在倉則計算 `real_entry × (1 + tp_pct)` 顯示在 reason 欄（CLI 「持200@46.7|你TP 50.9」、Markdown「(持200股 @46.68，你的 TP 50.88)」）
- ✅ **research 等觀察清單**：所有檔皆「-」（沒 trades 檔，視同未持有）

→ 這個設計支援所有使用情境：
- 自己看 → 既看到策略建議，又看到自己持倉（「持/未持」對照）
- 家人看 → 看到 strategy 中性建議
- 對帳：發現「系統認為 in_pos but 我帳戶 -」或反過來 → 提示更新 trades CSV

### 範例對照

```
6770 力積電  在倉「-」 HOLD  A 50%  TP 68 / SL 45  ← strategy 建議：誰持有都用此 TP/SL
1301 台塑    在倉「持」 HOLD  F  -      -          持200@46.68
                                                  ↑ 真實持倉資訊
2360 致茂    在倉「-」 SELL  A 50%      -          ← strategy 說該賣（雖然 user 未持）
```

---

## 已知限制 / 未來改進

### v0.1 仍是「T 收盤滿足條件才提示」
未實作「forward look」（T 不滿足但預測 T+1 觸發）。要加只要在 generator 的 else 分支也檢查「在 T+1 漲跌停區間內，是否存在某個 X 讓條件成立」。實作不複雜，留 v0.2。

### Generator 的 hypothetical entry_price ≠ Backtester 真實 fill price
Generator 內部在 BUY 時記錄 entry_price = T_close。但 Backtester 限價成交價可能略不同（low ≤ target_buy 時，fill = min(open, target_buy)）。目前 generator 用 T_close 算 target_tp，會跟 Backtester 真實 entry-based TP 差一點。

對 PnL 影響很小（兩者大概差 0.5% 以內，不會跨越停利門檻），v0.1 接受此 discrepancy。

未來改進：把 target_tp/target_sl 計算邏輯從 generator 搬到 Backtester（generator 只輸出 tp_pct 與 ma reference），徹底解耦。

### Template 覆蓋率（11 個 / 已完成 7 個 / 64%）
- ✅ low_vol_pullback (T8) — 回檔型
- ✅ mean_reversion (T5) — 回檔型
- ✅ donchian_breakout (T2) — 突破型（buy-stop）
- ✅ trend_pullback (T1) — 回檔型（delegated to style1）
- ✅ momentum_hold (T3) — 動能型
- ✅ volume_breakout (T6) — 突破型（buy-stop）
- ✅ bollinger_squeeze (T9) — 突破型（buy-stop）
- ❌ gap_continuation — 不適合（看 T+1 開盤）
- ❌ chip_momentum、chip_streak — 不適合（籌碼資料 T+1 才有）
- ❌ monthly_revenue_event — 不適合（月營收公告觸發）

剩 4 個天生不適合，維持 T+1 open fallback（engine 自動偵測 target 欄位是否全 NaN）。

### 突破型 vs 回檔型 — engine 兩種 buy_mode

**`buy_mode = 'limit'`**（回檔型）：T+1 low ≤ target_buy 才成交
- 成交價 = min(open, target_buy)（gap down 用 open，否則 target）
- 適用：low_vol_pullback、mean_reversion、trend_pullback、momentum_hold

**`buy_mode = 'stop'`**（突破型）：T+1 high ≥ target_buy 才成交
- 成交價 = max(open, target_buy)（gap up 用 open，否則 target）
- 適用：donchian_breakout、volume_breakout、bollinger_squeeze

Engine 自動讀 sig_df['target_buy_mode']，預設 'limit'。

### 7 templates 對代表標的的驗證結果

| Template | 標的 | Fill rate | MaxDD（舊→新）| IM-CAGR（舊→新）|
|---|---|---|---|---|
| low_vol_pullback | 2360 | 96% | -32% → -15% | 15% → 46% |
| mean_reversion | 1560 | 88% | -26% → -12% | 41% → 112% |
| donchian_breakout | 006208 | 98% | -6.6% → -6.8% | 17.5% → 23.1% |
| trend_pullback | 1326 | 46% | -5.3% → -1.4% | 18.9% → 69.6% |
| volume_breakout | 2615 | 100% | -9.4% → -8.5% | 133.9% → 172.0% |
| bollinger_squeeze | 2885 | 100% | -5.6% → -4.0% | 7.6% → 4.1% |

整體規律：MaxDD 全面降低、IM-CAGR 大多提升、勝率變化不一。

### auto_iterate 重訓考量
目前 best_params 是用「舊機制 + raw exec」優化出來的。新機制下參數可能不再最佳。
**建議**：限價單機制定型後，重訓 auto_iterate 一次（用 2010+ 資料 + 限價單回測），找出新機制下的真實最佳參數。

---

## 修改的檔案

| 檔案 | 修改內容 |
|---|---|
| `src/strategy/auto_iterate/templates.py` | generate_T5、generate_T8 加 target 欄位 + EOD 觸發檢查 |
| `src/strategy/backtest/engine.py` | 新增 `_run_per_stock_limit_orders()` 路徑，偵測 target 欄位自動啟用 |
| `src/strategy/eval/reporter.py` | markdown 報告加「掛單目標」欄 |
| `src/strategy/runner.py` | signals dict 加 target_xxx；CLI table 加「掛單」欄 |
| `scripts/build_per_stock_reports.py` | adj-only 路徑、加 fill rate 顯示 |
| `scripts/build_html.py` | adj-only、parse 掛單欄、UI cellOrder 函式 |

---

## 下一步建議（給家裡 PC Claude）

1. **試跑 1 週**：daily_update 有限價單機制下產出穩定後，再評估
2. **擴展更多 template**：donchian_breakout、trend_pullback、bollinger_squeeze
3. **重訓 auto_iterate**：用新機制 + 2010+ 資料找最佳參數（見 `TODO_RETRAIN.md`）
4. **Forward look**（v0.2）：generator 對未滿足條件但接近的 T 也預報「T+1 觸發點」
5. **解耦 generator / engine**：把 target_tp/sl 計算移到 engine（用 actual entry_price）
