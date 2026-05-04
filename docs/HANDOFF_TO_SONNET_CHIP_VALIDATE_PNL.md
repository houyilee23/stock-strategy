# Handoff: Style 3 階段 1.5 — 加 PnL 統計

> 開新 Sonnet session 用。**接續階段 1，擴充同一個腳本算 PnL，不要建模組。**

---

## 任務一句話

把 `scripts/validate_chip_signals.py` 擴充成 mini-backtest：把連續訊號 collapse 成單筆 trade、加對稱出場、算 PnL，印出每檔的績效統計，**讓使用者看到具體報酬數字**。

---

## 為什麼

階段 1 印出 820 個「訊號日」誤導性大 — 那其實是「持有期間每天 holding signal」。真正的進場應該是「叢集首日」，整個叢集對應**一筆 trade**。

不算 PnL 我們無從判斷策略好壞。在花時間正式建模組（階段 2）前，要先看到「2330 5 年來這策略賺幾趴、幾筆 trade、win rate 多少」這種具體數字。

---

## 範圍（嚴守）

| 做 | 不做 |
|---|---|
| **修改** `scripts/validate_chip_signals.py`（同一檔擴充） | 不要建新 .py 檔 |
| 加 cluster collapsing 邏輯 | 不要建 `src/strategy/signals/style3_*.py` |
| 加簡單對稱出場邏輯 | 不要動 `src/strategy/backtest/` |
| 加 PnL 計算（含手續費 + 證交稅 + 滑價） | 不要做 walk-forward 或 optuna |
| 印每檔績效統計表 | 不要寫測試（探索腳本不需要） |
| 還是只跑 5 檔（2330/3017/6669/2454/2317） | 不要擴充到全 universe |

---

## 實作細節

### 1. 進場邏輯：叢集首日

把現在的 `signal_today` 改成「上日為 False、今日為 True」的轉換點：
```python
signal_today = (c1 & c2 & c3 & c4)            # 4 個原條件 AND
entry_signal = signal_today & ~signal_today.shift(1).fillna(False)
```

`entry_signal == True` 的日期才是真正的進場觸發。

### 2. 出場邏輯（任一觸發）

進場後 in_position=True，每日檢查：

```python
# 條件 X1：5 日「外資 + 投信」累計轉負
chip_5d_neg = chip_5d_sum < 0

# 條件 X2：close < MA60 連續 1 日（先用最簡單的，之後可改 2 日）
ma60_break = close < ma60

# 條件 X3：持倉 > 60 個交易日強制出場（防呆）
hold_too_long = hold_days >= 60

exit_signal = chip_5d_neg | ma60_break | hold_too_long
```

進場與出場用 **T+1 開盤價**：
- T 日 entry_signal 為 True → T+1 open 買進
- T 日 exit_signal 為 True → T+1 open 賣出

注意：T+1 不一定是次一個 row（中間可能跳假日），用 `iloc[i+1]` 就好，不用查日曆。

### 3. PnL 計算

讀 `config/strategy.yaml` 的 `fees` 區段：
```python
buy_commission = 0.001425
sell_commission = 0.001425
sell_tax = 0.003
slippage = 0.003
```

每筆 trade：
```python
buy_price_eff  = entry_open  * (1 + slippage) * (1 + buy_commission)
sell_price_eff = exit_open   * (1 - slippage) * (1 - sell_commission - sell_tax)
trade_return = sell_price_eff / buy_price_eff - 1
```

### 4. 每檔績效統計

對每檔印一張表：
```
======================================================================
  2330 台積電
======================================================================
  期間: 2013-01-03 ~ 2026-04-22 (13.3 年)
  
  進場次數         : N
  年化進場次數     : X.X
  平均持倉天數     : X.X 個交易日
  
  Win rate         : XX.X%
  平均贏 / 平均輸  : +X.X% / -X.X%
  Profit factor    : X.XX
  Expectancy       : +X.XX%
  
  累計報酬         : +XXX.X%
  年化報酬 (CAGR)  : +XX.X%
  最大回撤         : -XX.X%
  
  Buy-and-hold 對照：
    累計報酬       : +XXX.X%
    年化報酬       : +XX.X%
    最大回撤       : -XX.X%
  
  超額年化報酬     : +X.X%   (策略 - B&H)
```

### 5. 訊號明細（前 5 + 後 5 trades）

```
  日期         action  price    chip5d   exit_reason       hold  pnl%
  2013-01-03   BUY     71.21   +30,823       —            —    —
  2013-04-25   SELL   118.50    -2,150  chip轉負          82  +63.2%
  ...
```

### 6. 總結表

最後印：
```
======================================================================
  總結（5 檔對照）
======================================================================
  Stock  Trades  WinRate  PF    Expectancy  Strategy  B&H    Alpha
  2330   N       XX.X%    X.XX  +X.X%       +XX.X%    +XX.X% +X.X%
  3017   ...
  ...
  
  --- median ---
  Trades:    N
  WinRate:   XX.X%
  PF:        X.XX
  Strategy CAGR: +XX.X%
  B&H CAGR:      +XX.X%
  Alpha:         +XX.X%
```

---

## 給使用者的判斷指引（腳本最後 print）

```
======================================================================
  下一步
======================================================================
  請看上方總結表，判斷：
  
  A. 策略 CAGR 中位數 > B&H CAGR + 5% → 概念成立，進階段 2
  B. 策略 CAGR 中位數 ≈ B&H ± 5%       → 改規則重跑 (例如加 RSI 過濾)
  C. 策略 CAGR 中位數 < B&H - 5%       → 概念不對，重新討論方向
  
  另外注意：
  - 5 檔之間 PF 分散度（標準差大代表 universal 仍不適用）
  - MaxDD 是否 < 30%
  - 訊號頻率是否在 1~5 次/年/股 的合理區間
======================================================================
```

---

## 完成標準

- [ ] 腳本能跑通，5 檔都有完整輸出
- [ ] cluster collapsing 邏輯正確（手算對照 2 個叢集驗證）
- [ ] 出場邏輯正確（chip 轉負或破 MA60 都會觸發）
- [ ] PnL 含手續費 + 證交稅 + 滑價
- [ ] B&H 對照計算正確
- [ ] 總結表 5 檔對照清楚

---

## 不要做的事

1. **不要動 `src/`** — 純 `scripts/` 擴充
2. **不要寫到 `data/chips/`** — 還是每次重抓
3. **不要寫測試** — 探索腳本
4. **不要把腳本拆成多檔** — 一個檔搞定
5. **不要超過 300 行** — 簡潔優先
6. **不要 silent fail** — 任何 stock 算不出來要噴錯
7. **不要去動策略參數的「優化」** — 純驗證概念，固定參數

---

## 卡關時

寫 `docs/BLOCKED_chip_validate_pnl.md`，貼出：
- 卡在哪裡
- console 已輸出的部分
- 你猜可能原因

---

## 給 Opus 的回報

不用寫 markdown 報告。**直接把總結表 + 5 檔績效表整段貼回來**。Opus 看數字判斷下一步。

---

開始吧。

執行：`'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' scripts/validate_chip_signals.py`
