# Handoff: Auto-Iterate — 5 模板 × 33 股 × per-stock 優化

> 開新 Sonnet session 用。**這是長時間自主任務（預估 2~5 小時），跑完寫終報告，中間不需 Opus 介入。**

---

## ⚠️ 修訂版（v3）— 從「打贏 0050」改成「大賺少賠」

### 為什麼又改

v2 把 benchmark 從 per-stock B&H 改成 0050，但 Opus 跟使用者討論後發現**整個方向還是錯的**：

1. **0050 在 2024-2026 = +18% CAGR（AI 大牛市異常高）**。用這當門檻會讓「景氣循環股」「區間震盪股」全部 FAIL，但這些股票其實適合擺盪策略。
2. **未來實際使用時不知道是牛/熊/震盪**。如果參數是用「贏 0050」優化出來的，AI 牛市結束後就不一定還好用。
3. **應該回到策略本身的品質**：每筆訊號出手是否「大賺少賠」？這個性質跟市場狀態無關。

### v3 評價架構：雙層篩選

**Tier 1（PASS 主軸，regime-independent）**
- `expectancy >= 5%`（每筆訊號淨值報酬，已扣費）
- `profit_factor >= 1.5`
- `max_drawdown <= 30%`
- `n_trades >= 5`

**Tier 2（純資訊，不參與 verdict）**
- `alpha_vs_0050`、`alpha_vs_bnh`、`cagr` — 排序與背景參考用

### 為什麼門檻設 +5% 而不是 +1%

單筆 round-trip 成本 = 0.3% slippage × 2 + 0.1425% commission × 2 + 0.3% sell tax = **1.185%**。
+1% expectancy = 淨損 0.185% / trade，根本不值得做。+5% 才是真有 edge。

範例「大賺少賠」結構（都能達到 +5% net expectancy）：
| 勝率 | 平均贏 | 平均輸 | expectancy |
|---|---|---|---|
| 50% | +13% | -3% | +5.0% |
| 40% | +18% | -3% | +5.4% |
| 60% | +10% | -3% | +4.8% |

把門檻拉高的副作用是好的：optuna 會自動偏好「少進場、讓利潤跑」，**自動解決過度交易問題**，不需要另外加頻率懲罰。

### v3 vs v2 vs v1 對照

| 版本 | Objective 主指標 | Verdict 主指標 | 預期 PASS 率 |
|---|---|---|---|
| v1 | PF | alpha vs per-stock B&H | 0% (都被 AI bull 壓死) |
| v2 | alpha vs 0050 | alpha vs 0050 | 10~20% (景氣循環股仍 FAIL) |
| **v3** | **expectancy + PF** | **expectancy + PF + DD + n** | **可能只 5~10%，但是真的 PASS** |

PASS 數量變少是好事——剩下的就是「不論市場狀態都值得用」的組合。

### 必須重跑 Phase A

舊的 run_id `20260423_143343` 不要 resume，objective 完全變了，整個重跑。執行步驟：

```bash
# 1. 確認 data/adjusted/0050.csv 存在（若不存在先抓，0050 在 v3 只當 informational）
ls data/adjusted/0050.csv

# 2. 重跑 Phase A（5 檔 smoke test）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py auto_iterate \
    --universe 2330,3017,6669,2454,2317 \
    --trials-per-pair 80 \
    --timeout-per-pair 300

# 3. 改寫 docs/AUTO_ITERATE_PHASE_A_REPORT.md 並貼回給 Opus
# 4. 等 Opus 綠燈後才跑 Phase B（--universe all）
```

---

---

## 任務一句話

對 universe 內每一檔個股，個別測試 5 種策略模板、用 optuna 找各檔最佳參數、做 walk-forward + hold-out 驗證，產出「每檔股票最適合哪個模板、用什麼參數」的完整對照。

---

## 兩階段執行（強制）

### Phase A：5 檔 smoke test（先跑這個，預估 30 分鐘）

universe 限定 **`2330,3017,6669,2454,2317`** 這 5 檔。

跑完 5 檔 × 5 模板 = 25 對後，**停下、不要繼續跑全套**。產出全部檔案到 `output/auto_iterate/{run_id}/`，並在終端印：

```
========================================================================
  Phase A SMOKE TEST 完成
========================================================================
  run_id: YYYYMMDD_HHMMSS
  耗時: X 分鐘
  25 對結果: PASS=N, WEAK=N, FAIL=N, DD_BREACH=N, INSUFFICIENT=N
  
  輸出檔案:
    - output/auto_iterate/{run_id}/comparison.csv
    - output/auto_iterate/{run_id}/per_stock_best.yaml
    - output/auto_iterate/{run_id}/summary.md
    - output/auto_iterate/{run_id}/{template}.yaml × 5
  
  請使用者 review 上述檔案。確認 OK 後，執行：
    python main.py auto_iterate --resume {run_id} --universe all
========================================================================
```

**寫到 docs/AUTO_ITERATE_PHASE_A_REPORT.md** 給 Opus 看，內容是上述終端輸出 + 任意 1 檔 1 模板的 detail（驗證流程跑通）。

### Phase B：全 universe（Phase A 通過後才跑）

使用者執行 `--resume {run_id} --universe all`，Sonnet 接續跑剩下的 28 檔（2330 等 5 檔已在 Phase A 跑過，DB 內已有結果，跳過）。

跑完寫 `docs/AUTO_ITERATE_REPORT.md`（最終終報告，覆蓋 Phase A 的）。

**Phase A 不通過 → 不要跑 Phase B，等 Opus 修規格。**

---

## 為什麼這樣做

過去 4 輪迭代都失敗（Style 1 universal 優化、Style 3 籌碼策略），原因是「universe heterogeneous，一套參數壓不住」。改成 **per-stock 個別優化** + **多模板比較**，每個 (stock, template) 是獨立小問題，更容易找到 working 組合。

---

## 5 個策略模板規格

每個模板的 entry / exit / 可調參數 spec 如下。**Sonnet 必須完全按 spec 實作，不要自由創作邏輯。**

### Template 1: `trend_pullback`（升級版 Style 1）

**已實作**：`src/strategy/signals/style1_pullback.py` 直接重用

**Entry（5 條件 AND）**：
- `close > MA(ma_long)` AND `MA(ma_short) > MA(ma_long)`
- 大盤 regime BULL
- `RSI < rsi_oversold` OR `close < bollinger_lower`
- `close > open` AND `close > prev_close`
- `volume > volume_ma × volume_min_ratio`

**Exit（4 條件 OR）**：
- `close < high_since_entry - atr_stop_k × ATR`
- `close < MA(ma_long)` 連續 `trend_break_days` 日
- `RSI > rsi_overbought` AND `close > bollinger_upper`
- `hold_days >= max_hold_days`

**Search space**：照現有 `src/strategy/optimize/search_space.py`

---

### Template 2: `donchian_breakout`（新建）

**檔案**：`src/strategy/signals/template_donchian.py`

**Entry（3 條件 AND）**：
- `close >= rolling_max(close, donchian_entry_n)`（N 日新高）
- `close > MA(trend_ma)`
- `volume > volume_ma(20) × volume_min_ratio`

**Exit（2 條件 OR）**：
- `close < rolling_min(close, donchian_exit_n)`（M 日新低）
- `close < high_since_entry - atr_stop_k × ATR(14)`

**Search space**：
```python
{
    "donchian_entry_n": {"type": "categorical", "choices": [20, 55, 120]},
    "donchian_exit_n":  {"type": "categorical", "choices": [10, 20, 55]},
    "trend_ma":         {"type": "categorical", "choices": [50, 100, 200]},
    "atr_stop_k":       {"type": "float", "low": 1.5, "high": 4.0, "step": 0.5},
    "volume_min_ratio": {"type": "float", "low": 0.5, "high": 1.5, "step": 0.25},
}
```

---

### Template 3: `momentum_hold`（新建）

**檔案**：`src/strategy/signals/template_momentum.py`

**Entry（2 條件 AND）**：
- 過去 `mom_lookback` 日報酬率 > `mom_entry_pct`（例：60 日 > 10%）
- `close > MA(trend_ma)`

**Exit（2 條件 OR）**：
- 過去 `mom_lookback` 日報酬率 < `mom_exit_pct`（例：< 0%）
- `close < MA(trend_ma)`

**Search space**：
```python
{
    "mom_lookback":  {"type": "categorical", "choices": [30, 60, 120, 250]},
    "mom_entry_pct": {"type": "float", "low": 0.05, "high": 0.30, "step": 0.05},
    "mom_exit_pct":  {"type": "float", "low": -0.10, "high": 0.05, "step": 0.025},
    "trend_ma":      {"type": "categorical", "choices": [50, 100, 200]},
}
```

---

### Template 4: `chip_momentum`（新建，用籌碼當輔助）

**檔案**：`src/strategy/signals/template_chip_momentum.py`

**前置**：需要 `data/chips/{sid}.csv`。Sonnet 第一步要建 `fetch_chip_data()` 抓 33 檔籌碼資料（一次性，存盤）。

**Entry（3 條件 AND）**：
- 過去 `mom_lookback` 日報酬率 > `mom_entry_pct`
- 過去 `chip_window` 日「外資+投信」累計買超 > 0（用 T-1 籌碼防穿越）
- `close > MA(trend_ma)`

**Exit（2 條件 OR）**：
- 過去 `chip_window` 日「外資+投信」累計買超 < 0
- `close < high_since_entry - atr_stop_k × ATR(14)`

**Search space**：
```python
{
    "mom_lookback":   {"type": "categorical", "choices": [30, 60, 120]},
    "mom_entry_pct":  {"type": "float", "low": 0.05, "high": 0.20, "step": 0.05},
    "chip_window":    {"type": "categorical", "choices": [20, 60, 120]},
    "trend_ma":       {"type": "categorical", "choices": [50, 100, 200]},
    "atr_stop_k":     {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
}
```

---

### Template 5: `mean_reversion`（新建，與 Template 1 不同的回檔定義）

**檔案**：`src/strategy/signals/template_mean_reversion.py`

**Entry（3 條件 AND）**：
- `close > MA(trend_ma)`（長線多頭）
- `close < MA(short_ma) × (1 - pullback_pct)`（短期跌破短均 X%）
- `RSI(rsi_period) < rsi_oversold`

**Exit（3 條件 OR）**：
- `RSI(rsi_period) > rsi_overbought`
- `close > MA(short_ma) × (1 + take_profit_pct)`
- `hold_days >= max_hold_days`

**Search space**：
```python
{
    "trend_ma":         {"type": "categorical", "choices": [100, 150, 200]},
    "short_ma":         {"type": "categorical", "choices": [10, 20, 30]},
    "pullback_pct":     {"type": "float", "low": 0.02, "high": 0.10, "step": 0.01},
    "rsi_period":       {"type": "categorical", "choices": [7, 14, 21]},
    "rsi_oversold":     {"type": "int", "low": 20, "high": 35, "step": 5},
    "rsi_overbought":   {"type": "int", "low": 60, "high": 80, "step": 5},
    "take_profit_pct":  {"type": "float", "low": 0.03, "high": 0.15, "step": 0.02},
    "max_hold_days":    {"type": "categorical", "choices": [30, 60, 120]},
}
```

---

## 資料切分（嚴守，所有模板都用同一個切法）

```
Train:    2017-01-01 ~ 2023-12-31  (7 年, 用來 optuna 優化)
Hold-out: 2024-01-01 ~ 2026-04-22  (2.3 年, 完全不參與優化, 只用一次)
```

**重要**：optuna 的 objective 只看 train 段。Hold-out 段在每個 (stock, template) 找到 best_params 後，**只跑一次**做最終驗證。

不做 cross-validation（per-stock 樣本太小，CV 不穩）。直接 train/test 兩段切。

---

## Per-stock 優化流程（每檔每模板）

```python
for sid in universe:
    for template in [T1, T2, T3, T4, T5]:
        # 1. 載入該股 OHLCV (data/adjusted/{sid}.csv)
        df = load_adjusted(sid)
        if len(df_train_period) < 250:   # 資料不足 1 年的跳過
            log "skip"; continue
        
        # 2. Optuna 優化（單股 train 段）
        study = create_study(
            storage=f"sqlite:///output/auto_iterate/{run_id}/{template}.db",
            study_name=f"{template}_{sid}",
            load_if_exists=True,
        )
        study.optimize(
            objective=lambda trial: backtest_single_stock(sid, template, trial.params, train_period),
            n_trials=80,                  # per (stock, template)
            timeout=300,                  # 5 分鐘上限防卡死
        )
        
        # 3. Hold-out 驗證
        best_params = study.best_params
        train_metrics = backtest(sid, template, best_params, train_period)
        test_metrics  = backtest(sid, template, best_params, test_period)
        
        # 4. 記錄
        result[sid][template] = {
            "best_params": best_params,
            "train": train_metrics,
            "test":  test_metrics,
            "verdict": classify(test_metrics),
        }
```

**Universe**：`data/adjusted/` 全部（約 33 檔）

**Objective function**（給 optuna 最大化）：

**v3 主指標 = expectancy（每筆訊號淨值報酬）+ PF**。完全脫離市場 benchmark，回到策略本身的「大賺少賠」品質。

```python
def objective(metrics):
    """
    metrics: 該股 train 段 backtest 結果（已扣費）
    需要的 keys: n_trades, profit_factor, expectancy, max_drawdown
    """
    if metrics["n_trades"] < 5:
        return -10.0   # 樣本不足重罰
    
    pf = metrics["profit_factor"]
    if pf is None or pf <= 0:
        return -5.0
    if pf == float("inf") or pf > 5.0:
        pf = 5.0   # 統一 cap 防小樣本 PF 膨脹（修正 Phase A 發現的 bug）
    
    expectancy = metrics["expectancy"]   # 已扣費的淨值（小數，例 0.05 = +5%）
    dd_penalty = max(0, abs(metrics["max_drawdown"]) - 0.30) * 5
    
    # 大賺少賠 score：expectancy 為主、PF 為輔
    return expectancy * 10 + pf * 0.2 - dd_penalty
```

**權重直覺**：
- expectancy +5% → +0.5
- PF 5.0 (cap) → +1.0
- 兩者同量級，避免單一指標主導
- DD > 30% 才開始扣分（30% 內 free）

**前置作業**：載入 0050 算 train/test 段 CAGR，存進 metrics 當 `alpha_vs_0050` 欄位（**僅供報表參考，不參與 score / verdict**）。如果 `data/adjusted/0050.csv` 不存在，先抓：

```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py fetch --sids 0050
```

**重要**：`backtest_one.py` 目前 metrics dict 只有 `n_trades / profit_factor / max_drawdown / win_rate / cagr / bnh_cagr`。**Sonnet 必須補上 `expectancy / avg_win / avg_loss`**（backtest result 已有這些 properties，只是沒輸出到 dict）。

---

## verdict 分類規則

**v3 完全用 Tier 1（per-trade quality）判 verdict，不看 0050、不看 per-stock B&H**。
那些 alpha 數值在 yaml/csv 內保留為 informational 欄位，給人看的、不影響判定。

```python
def classify(test_metrics) -> str:
    """
    test_metrics: 該股 hold-out (test) 段的 backtest 結果（已扣費）
    需要的 keys: n_trades, profit_factor, expectancy, max_drawdown
    """
    n          = test_metrics["n_trades"]
    pf         = test_metrics["profit_factor"]
    expectancy = test_metrics["expectancy"]   # 已扣費的淨值（小數）
    dd         = abs(test_metrics["max_drawdown"])
    
    if n < 5:
        return "INSUFFICIENT"     # 測試期樣本太少
    if dd > 0.30:
        return "DD_BREACH"        # 違反風控
    if pf is None or pf < 1.0 or expectancy < 0.01:
        return "FAIL"             # 賠錢或邊緣到無感（< +1% net）
    if expectancy >= 0.05 and pf >= 1.5:
        return "PASS"             # 大賺少賠：每筆淨賺 5%+ 且 PF >= 1.5
    return "WEAK"                 # +1% ~ +5% expectancy 之間
```

**門檻設計理由**：
- `expectancy >= 5%`：扣完 1.185% round-trip 成本後，每筆訊號淨賺 5%+
- `pf >= 1.5`：贏的總和是輸的 1.5 倍以上，sanity check
- `dd <= 30%`：CLAUDE.md 風控底線
- `n_trades >= 5`：統計顯著（v2 是 3，v3 拉嚴）
- 拿掉 alpha 比較 → 跟市場狀態完全脫鉤

---

## 輸出檔案結構

```
output/auto_iterate/{YYYYMMDD_HHMMSS}/
  
  # 每模板一個 yaml，存所有股票的 best_params
  trend_pullback.yaml
  donchian_breakout.yaml
  momentum_hold.yaml
  chip_momentum.yaml
  mean_reversion.yaml
  
  # 5 個 optuna 的 SQLite (checkpoint 用)
  trend_pullback.db
  donchian_breakout.db
  ...
  
  # 跨模板對照
  comparison.csv            # 33 行 × 多欄位
  per_stock_best.yaml       # 每股推薦最佳模板
  summary.md                # 人類可讀總結
```

### `{template}.yaml` 結構
```yaml
template: trend_pullback
generated_at: "2026-04-23T15:00:00"
train_period: "2017-01-01~2023-12-31"
test_period:  "2024-01-01~2026-04-22"

# Benchmark 0050（informational，不參與 verdict）
benchmark_0050:
  train_cagr: 0.08
  test_cagr:  0.18

per_stock:
  "2330":
    best_params:
      ma_long: 200
      ma_short: 50
      rsi_oversold: 35
      ...
    train:
      n_trades: 18
      win_rate: 0.5
      profit_factor: 2.1
      expectancy: 0.06           # +6% net per trade（主指標）
      avg_win: 0.13
      avg_loss: -0.04
      cagr: 0.15
      max_drawdown: -0.12
    test:
      n_trades: 6
      win_rate: 0.5
      profit_factor: 1.8
      expectancy: 0.058          # +5.8% net per trade（用來判 verdict）
      avg_win: 0.12
      avg_loss: -0.04
      cagr: 0.23
      max_drawdown: -0.08
      # 以下三欄 informational only
      bnh_cagr: 0.74
      alpha_vs_0050: 0.05
      alpha_vs_bnh: -0.51
    verdict: PASS    # expectancy=5.8% >= 5% AND pf=1.8 >= 1.5
  "3017":
    ...
```

### `comparison.csv` 結構

主排序欄位 = `expectancy`（每模板）。`alpha_vs_0050` 與 `bnh_cagr` 保留供人看，不參與排名。

```
stock_id, bnh_test_cagr, benchmark_0050_test_cagr,
  T1_verdict, T1_n_trades, T1_pf, T1_expectancy, T1_avg_win, T1_avg_loss, T1_dd, T1_cagr, T1_alpha_vs_0050,
  T2_verdict, T2_n_trades, T2_pf, T2_expectancy, T2_avg_win, T2_avg_loss, T2_dd, T2_cagr, T2_alpha_vs_0050,
  T3_..., T4_..., T5_...,
  best_template, best_expectancy
```

「best_template」選擇邏輯（按優先順序）：
1. 任一模板 PASS → 選 expectancy 最高的 PASS 模板
2. 全 WEAK → 選 expectancy 最高的 WEAK 模板（但要記 verdict=WEAK）
3. 全 FAIL/DD_BREACH/INSUFFICIENT → `best_template = NONE`

### `per_stock_best.yaml` 結構
```yaml
benchmark_0050_test_cagr: 0.18      # informational

"2330":
  best_template: T2_donchian_breakout
  verdict: PASS
  test_expectancy: 0.058             # 主指標：每筆訊號淨賺 5.8%
  test_pf: 1.8
  test_n_trades: 6
  test_max_dd: -0.08
  test_cagr: 0.23                    # informational
  test_alpha_vs_0050: 0.05           # informational
  params_ref: "donchian_breakout.yaml#per_stock.2330"

"<某 WEAK 檔>":
  best_template: T1_trend_pullback
  verdict: WEAK
  test_expectancy: 0.025             # +2.5%，剛好 WEAK 區間
  recommendation: "可用，但建議縮小部位（expectancy 未達 5% 門檻）"
  params_ref: "trend_pullback.yaml#per_stock.xxxx"

"<某全 FAIL 檔>":
  best_template: NONE
  verdict: All FAIL/DD_BREACH/INSUFFICIENT
  recommendation: "訊號模式不適用，建議走組合模式（Katie）或直接買 0050"
```

### `summary.md` 結構

至少包含這 6 段：

1. **Run metadata**：run_id, 耗時, 跑了幾個 (stock, template) 對
2. **PASS / WEAK / FAIL / DD_BREACH 統計**（每模板的分布）
3. **每模板的 PASS 個股清單**（哪些股適合哪個模板）
4. **沒有任何模板能 PASS 的個股**（建議從 watchlist 移除或改用 B&H）
5. **Top 10 alpha 個股**（不分模板）
6. **給 Opus 的關鍵發現**：
   - 哪個模板覆蓋最多個股？
   - 哪類股票（成長/權值/景氣）對應哪個模板？
   - 整體 watchlist 有多少 % 能找到 PASS 模板？

---

## CLI 整合

```bash
python main.py auto_iterate \
    --trials-per-pair 80 \
    --timeout-per-pair 300 \
    --train-end 2023-12-31 \
    --test-start 2024-01-01 \
    [--universe all|<sids>] \
    [--templates T1,T2,T3,T4,T5] \
    [--resume <run_id>]
```

預設 universe=all、templates=T1,T2,T3,T4,T5

---

## Checkpoint & Resume

每個 `(template, sid)` 對 = 一個 optuna study（study_name = `f"{template}_{sid}"`）。
全部 165 個 study 共用 5 個 SQLite db（每模板一個）。
中途中斷 → `--resume {run_id}` 自動從未完成的 study 接續。

進度顯示（每完成一個 study 印一次）：
```
[42/165] 2330 × T2_donchian_breakout: best_score=2.31  test_cagr=+18%  verdict=PASS  (耗時 1m23s)
```

---

## 完成標準

### Phase A（5 檔 smoke test）完成標準
- [ ] 5 個 template 模組都實作完成
- [ ] `fetch_chip_data` 抓完 5 檔籌碼存到 `data/chips/`（T4 用）
- [ ] 25 個 (stock, template) 對全部跑完
- [ ] 5 個 template yaml 寫出，每個都有 5 檔的完整 per_stock 區段
- [ ] `comparison.csv`, `per_stock_best.yaml`, `summary.md` 全部產出
- [ ] `python -m pytest tests/ -x -q` 全綠（不要破壞既有功能）
- [ ] `docs/AUTO_ITERATE_PHASE_A_REPORT.md` 寫好
- [ ] **停下等 Opus 看，不要繼續 Phase B**

### Phase B（全 universe）完成標準（Opus 給綠燈後才執行）
- [ ] 剩餘 28 檔籌碼抓完
- [ ] 28 × 5 = 140 對額外跑完，總共 165 對
- [ ] 全部輸出檔案更新
- [ ] `docs/AUTO_ITERATE_REPORT.md`（覆蓋 Phase A 報告）寫好

---

## 不要做的事

1. **不要直接改 `config/strategy.yaml`** — 結果寫到 `output/auto_iterate/`，由人決定要不要套用
2. **不要動 `config/watchlists.yaml`**
3. **不要在 objective 內偷看 test 段** — train 段優化、test 段只驗證一次
4. **不要 silent skip** — 個股跳過要寫 `summary.md` 的「skipped」清單
5. **不要重新發明指標** — RSI/MA/ATR/Bollinger 用 `src/strategy/indicators/` 既有實作
6. **超出 timeout 不要繼續** — 5 分鐘跑不完一個 (stock, template) 就停下用 best-so-far
7. **不要寫複雜的 fallback** — 規格寫什麼就做什麼，遇到問題寫 BLOCKED 文件

---

## 卡關協議

任一以下情況停下，寫 `docs/BLOCKED_auto_iterate.md`：
- 任一 template 的 backtest 噴錯且無法 30 分鐘內排除
- 整體耗時超過 8 小時還沒跑完一半
- 發現某 template 100% 個股 INSUFFICIENT（規格可能有 bug）
- 籌碼資料抓不到（FinMind API 變動或 quota 用完）

---

## 給 Opus 的最終回報

寫到 `docs/AUTO_ITERATE_REPORT.md`，內容：

```markdown
# Auto-Iterate 報告

## TL;DR
- run_id: ...
- 耗時: X 小時
- 165 個 (stock, template) 對  → PASS: N, WEAK: N, FAIL: N, DD_BREACH: N, INSUFFICIENT: N

## 跨模板覆蓋率
| Template | PASS 數 | 平均 alpha | 適合的股票類型 |
|---|---|---|---|

## Watchlist 重整建議
（基於 per_stock_best 的結論）

## 開放問題給 Opus 判斷
（任何 Sonnet 不確定的設計決策）
```

---

開始吧。

## v3 重跑 Checklist（Phase A 已跑過 v1，模組都建好了，這次只需改評分邏輯）

### 程式改動清單

1. **`src/strategy/auto_iterate/backtest_one.py`**
   - `_run_one_segment()` 的 metrics dict 加三個欄位：
     ```python
     "expectancy":  result.expectancy,
     "avg_win":     result.avg_win,
     "avg_loss":    result.avg_loss,
     ```
   - `score_single()` 改成 v3 公式：
     ```python
     def score_single(metrics: dict) -> float:
         if metrics.get("n_trades", 0) < 5:
             return -10.0
         pf = metrics.get("profit_factor", 0.0)
         if pf is None or (isinstance(pf, float) and np.isnan(pf)):
             return -5.0
         if isinstance(pf, float) and (np.isinf(pf) or pf > 5.0):
             pf = 5.0
         if pf <= 0:
             return -5.0
         expectancy = metrics.get("expectancy", 0.0)
         if expectancy is None or np.isnan(expectancy):
             expectancy = 0.0
         dd = metrics.get("max_drawdown", float("nan"))
         dd_ab = abs(dd) if not np.isnan(dd) else 0.0
         dd_penalty = max(0.0, dd_ab - 0.30) * 5.0
         return expectancy * 10 + pf * 0.2 - dd_penalty
     ```
   - `classify()` 改成 v3 公式（見上方「verdict 分類規則」段落）

2. **`src/strategy/auto_iterate/runner.py`**
   - 開跑前載入 `data/adjusted/0050.csv`，算 train/test 兩段 B&H CAGR，存成 `benchmark_0050_train_cagr` / `benchmark_0050_test_cagr`
   - 寫 yaml 時把 `benchmark_0050` 區段塞進每個 `{template}.yaml`
   - 算 `alpha_vs_0050 = test_cagr - benchmark_0050_test_cagr` 寫入 per_stock test 區
   - 算 `alpha_vs_bnh = test_cagr - bnh_cagr` 寫入 per_stock test 區
   - `comparison.csv` 欄位改成 v3 schema（見上方「`comparison.csv` 結構」段落）
   - `per_stock_best.yaml` 的 best_template 選擇邏輯：用 expectancy 排序而不是 alpha
   - 進度顯示改成：`[42/165] 2330 × T2: expectancy=+5.8% pf=1.8 n=6 dd=-8% verdict=PASS (1m23s)`

3. **`docs/AUTO_ITERATE_PHASE_A_REPORT.md`**
   - 重寫整份。第一段就講「v3 評價架構」，貼 25 對的 expectancy/PF/verdict 表，最後給 Opus 的判斷問題。

### 不要動的東西

- 5 個 template 模組（已實作好）
- chip 資料抓取（5 檔已存在 `data/chips/`）
- SQLite checkpointing（v1 已實作好）
- search space（不變）
- train/test 切分日期（不變）

### 執行指令（重跑 Phase A）

```bash
# 確認 0050 存在
ls data/adjusted/0050.csv

# 開新 run_id 跑 5 檔 smoke test（不要 --resume 舊 run_id，objective 不一樣）
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py auto_iterate \
    --universe 2330,3017,6669,2454,2317 \
    --trials-per-pair 80 \
    --timeout-per-pair 300

# 跑完寫 docs/AUTO_ITERATE_PHASE_A_REPORT.md，貼回給 Opus
# 等 Opus 綠燈才跑 Phase B
```

### 完成標準（v3 Phase A）

- [ ] `backtest_one.py` 的 metrics dict 有 expectancy/avg_win/avg_loss
- [ ] `score_single()` 用 v3 公式（expectancy*10 + pf*0.2 - dd_penalty）
- [ ] `classify()` 用 v3 公式（看 expectancy/pf/dd/n_trades，不看 alpha）
- [ ] 5 個 yaml 都有 `benchmark_0050` header
- [ ] yaml 內 train/test 區段都有 expectancy/avg_win/avg_loss
- [ ] yaml 內 test 區段有 alpha_vs_0050、alpha_vs_bnh（informational）
- [ ] comparison.csv 用 v3 欄位
- [ ] per_stock_best.yaml 用 expectancy 排序
- [ ] `python -m pytest tests/ -x -q` 全綠
- [ ] `docs/AUTO_ITERATE_PHASE_A_REPORT.md` 改寫好
- [ ] **停下等 Opus，不要跑 Phase B**
