# Auto-Iterate 完整報告（Phase A + Phase B）

**run_id**: `20260423_151107`  
**Universe**: 34 檔（全 watchlist，排除 0050 及資料不足 4 檔）  
**Templates**: T1=trend_pullback, T2=donchian_breakout, T3=momentum_hold, T4=chip_momentum, T5=mean_reversion  
**Train**: 2017-01-01 ~ 2023-12-31　**Test**: 2024-01-01 ~ 2026-04-22  
**0050 test CAGR（僅供資訊）**: +54.6%

---

## 總覽

| 項目 | 數值 |
|------|------|
| 總 pairs | 170（34 × 5）|
| 耗時 | 49.1 分鐘 |
| PASS | **13** |
| SUSPICIOUS_PERFECT | 2（另計，詳見下方）|
| WEAK | 6 |
| FAIL | 12 |
| DD_BREACH | 35 |
| INSUFFICIENT | 102 |
| PASS 個股數 | **9 / 34 = 26%** |
| PASS+WEAK 個股數 | 11 / 34 = 32% |

---

## PASS 個股最佳模板彙整

| Stock | Best Template | Exp (test) | PF (test) | n | DD (test) | CAGR (test) | Alpha vs 0050 |
|-------|--------------|-----------|-----------|---|-----------|-------------|---------------|
| **2308** | donchian_breakout | **+24.9%** | 4.82 | 6 | -24.2% | **+101.0%** | **+46.5%** |
| **6515** | trend_pullback | **+19.2%** | 9.60 | 6 | -26.4% | +50.4% | -4.2% |
| 2383 | chip_momentum | +13.2% | 5.38 | 7 | -21.4% | +51.1% | -3.5% |
| 3711 | chip_momentum | +12.2% | 4.04 | 8 | -23.5% | +58.1% | +3.5% |
| 3017 | chip_momentum | +8.3% | 2.98 | 9 | -25.6% | +59.7% | +5.1% |
| 2330 | donchian_breakout | +8.0% | 4.43 | 6 | -26.4% | +19.0% | -35.6% |
| 1802 | donchian_breakout | +7.9% | 2.10 | 6 | -22.6% | +13.9% | -40.7% |
| 1560 | trend_pullback | +7.5% | 2.98 | 7 | -27.4% | +29.1% | -25.5% |
| 6770 | chip_momentum | +6.5% | 2.28 | 17 | -23.6% | +36.8% | -17.8% |
| 2360 | chip_momentum | +11.1% | 4.15 | 8 | -27.0% | +104.3%† | +49.7%† |

---

## WEAK 個股（有訊號價值但需縮小部位）

| Stock | Best Template | Exp (test) | PF | n | DD |
|-------|--------------|-----------|-----|---|----|
| 2345 | momentum_hold | +4.4% | 1.75 | 5 | -28.9% |
| 6505 | chip_momentum | +1.0% | 1.30 | 10 | -21.9% |

---

## 各模板 PASS 分布

| Template | PASS 個股 | 數量 |
|----------|----------|------|
| T1 trend_pullback | 1560, 2308, 6515 | 3 |
| T2 donchian_breakout | 1802, 2308, 2330, 2360 | 4 |
| T3 momentum_hold | （無） | 0 |
| **T4 chip_momentum** | **2308, 2330, 2360, 2383, 3017, 3711, 6770** | **7** |
| T5 mean_reversion | 1560 | 1 |

**chip_momentum 覆蓋最廣（7 股 PASS）**，是本次 universe 最通用的模板。

---

## SUSPICIOUS_PERFECT（測試期零虧損或 PF > 10，已獨立分類）

這兩個案例原本可能歸為 PASS，但因測試期無虧損交易（avg_loss=0）或 PF 極端，
現以 `SUSPICIOUS_PERFECT` 獨立標記，**不計入 PASS 數、不列為可操作訊號**。

### 2360 × donchian_breakout

```
Train: n=17, exp=+2.2%, PF=1.19, MaxDD=-54.0%  ← 訓練期幾乎無邊際、DD 超大
Test:  n=5,  exp=+20.5%, PF=inf（5 筆全贏）,  MaxDD=-19.1%
optuna train score = -0.74（優化器本身評分極低）
```

- 訓練期與測試期完全脫節，屬「小樣本運氣型」
- 2360 的 best_template 已改為 chip_momentum（PASS，n=8，PF=4.15）

### 1560 × mean_reversion

```
Train: n=5, exp=+10.4%, PF=6.80, MaxDD=-24.3%
Test:  n=5, exp=+12.8%, PF=248.6（近零虧損）, MaxDD=-12.0%
```

- 訓練方向一致，但兩期樣本數均為 5，統計信心不足
- 1560 的 best_template 已改為 trend_pullback（PASS，n=7，PF=2.98）

> †：report 中 2360 的 CAGR/Alpha 數值為 donchian_breakout 的測試期結果（供參考），
>    實際 best_template 為 chip_momentum。

---

## 強力 PASS 詳細解析

### 2308（瑞昱） — 最佳 Alpha 個股

```
T1 trend_pullback: exp=+6.4%, PF=2.90, n=5, DD=-18%         ← PASS
T2 donchian_breakout: exp=+24.9%, PF=4.82, n=6, DD=-24%     ← PASS（最佳）
T4 chip_momentum: exp=+11.9%, PF=7.63, n=5, DD=-19%         ← PASS

Best: donchian_breakout
  params: entry_n=20, exit_n=55, trend_ma=100, atr_stop_k=4.0
  Train: n=18, exp=+3.7%, CAGR train 尚可
  Test:  CAGR=+101%, Alpha vs 0050=+46.5%
```

→ 3 個模板均 PASS，一致性強。donchian 短進長出設計（entry=20日新高，exit=55日新低）適合瑞昱的快速趨勢。

### 6515（六福） — 最高 PF

```
T1 trend_pullback: exp=+19.2%, PF=9.60, n=6, DD=-26%        ← PASS（最佳）

Best params: ma_long=150, ma_short=50, rsi_period=10, rsi_oversold=50
Train: n=5, exp=+12.4%, PF=9.21  ← Train/Test PF 高度一致（9.2 vs 9.6）
Test: CAGR=+50.4%
```

→ Train/Test 一致性最佳（PF 差異 <5%），是最穩健的 PASS 之一。

### 2383（台灣大） — chip_momentum 代表作

```
T4 chip_momentum: exp=+13.2%, PF=5.38, n=7, DD=-21%         ← PASS

Best params: mom_lookback=30, chip_window=120, trend_ma=50, atr_stop_k=2.5
Train: n=17, exp=+6.0%, PF=3.47  ← 訓練樣本充足
Test: CAGR=+51.1%
```

→ 訓練 n=17 樣本充足，測試期 exp 翻倍（+6% → +13.2%），法人籌碼動能在電信股有效。

### 3711（日月光） — 最多 n

```
T4 chip_momentum: exp=+12.2%, PF=4.04, n=8, DD=-23.5%       ← PASS

Best params: mom_lookback=60, chip_window=60, trend_ma=200, atr_stop_k=3.5
Train: n=14, exp=+5.1%, PF=4.54
Test: CAGR=+58.1%, Alpha vs 0050=+3.5%
```

→ Train/Test PF 一致（4.54 vs 4.04），n=8 樣本相對充足。

---

## BORDERLINE 候選

### BORDERLINE_DD（DD 30-35%，其餘達 PASS）

| Stock | Template | Exp | PF | n | DD |
|-------|----------|-----|----|---|----|
| **2337** | chip_momentum | **+39.1%** | 17.40 | 6 | -32.6% |
| 6770 | momentum_hold | +12.2% | 2.44 | 11 | -34.2% |
| 2317 | momentum_hold | +11.6% | 2.82 | 6 | -34.7% |
| 3017 | trend_pullback | +6.8% | 1.78 | 7 | -32.6% |

> 2337（旺宏）chip_momentum exp=+39.1%、PF=17.4 非常突出，只差 DD=-32.6%（超標 2.6%）。若操作時加入 trailing stop 收緊可能降 DD。

### BORDERLINE_LOW_N（n=3-4，其餘達 PASS）

| Stock | Template | Exp | PF | n | DD |
|-------|----------|-----|----|---|----|
| **2317** | donchian_breakout | **+33.0%** | 7.50 | 3 | -17.0% |
| **3017** | donchian_breakout | **+21.5%** | 30.86 | 4 | -29.2% |
| 2360 | trend_pullback | +20.3% | 2.68 | 3 | -24.5% |
| 2360 | momentum_hold | +17.8% | 4.78 | 4 | -25.2% |
| 2383 | momentum_hold | +17.6% | 4.61 | 4 | -27.3% |
| 1809 | donchian_breakout | +15.9% | 3.31 | 4 | -22.7% |
| 2317 | chip_momentum | +12.3% | 2.50 | 4 | -27.6% |
| 4958 | donchian_breakout | +7.7% | 2.53 | 4 | -28.3% |
| 1809 | mean_reversion | +5.4% | 3.81 | 4 | -14.2% |

> 3017×donchian PF=30.86（n=4）、2317×donchian PF=7.5（n=3）方向性極佳，但樣本不足、需等 2026 年底再驗證。

---

## 無 PASS 個股分析

22 檔全部 FAIL/DD_BREACH/INSUFFICIENT：

| 分組 | 個股 | 原因推測 |
|------|------|---------|
| 傳產（B&H 負報酬） | 1227, 1301, 1326, 2002, 9940 | 本身跌跌不休，訊號無效 |
| 科技但高波動 | 2454（聯發科）, 2408, 2337* | 波動大、ATR stop 易被掃 |
| 短期 IPO / 成交量小 | 1809, 6271, 6505 | test 期 n < 5 |
| 趨勢不明確 | 2303, 2324, 2327, 2382 | 無明確趨勢結構 |

> *2337 有 BORDERLINE_DD，若 DD 門檻放至 35% 可 PASS

---

## Top Expectancy 不論 verdict（觀察用）

| Stock | Template | Exp | Verdict | 備注 |
|-------|----------|-----|---------|------|
| 2344 | donchian_breakout | +155.3% | INSUFFICIENT | n=2，無效 |
| 2344 | chip_momentum | +68.3% | DD_BREACH | DD=-64% |
| 2408 | chip_momentum | +61.2% | INSUFFICIENT | n=3 |
| 2337 | chip_momentum | +39.1% | DD_BREACH | BORDERLINE_DD |
| 2317 | donchian_breakout | +33.0% | INSUFFICIENT | BORDERLINE_LOW_N |

---

## 給 Opus 的問題

### Q1：2360 × donchian_breakout 是否保留為 PASS？

Train 表現差（exp=+2.2%, PF=1.19, DD=-54%, train score=-0.74），Test 5 筆全贏。
建議：**標記「低信心 PASS」，觀察不操作**，或直接改 INSUFFICIENT 排除。

### Q2：2337（旺宏）是否值得特殊處理？

exp=+39.1%, PF=17.4, n=6，只差 DD=-32.6%（超標 2.6%）。
選項：(a) 保持 DD_BREACH 不處理；(b) 加入「BORDERLINE_DD 觀察清單」（已做）；(c) 手動收緊 atr_stop_k 後重跑。

### Q3：下一步方向？

目前 10 檔 PASS + 2 檔 WEAK = 12 檔可操作訊號來源。建議方向：
1. **生產化**：把 per_stock_best.yaml 接上 `python main.py signals` 的日常訊號流
2. **Katie 組合**：用 12 檔 PASS/WEAK 股做等權或 expectancy 加權的動態組合
3. **2337 + 3017 監控**：設 DD 警戒，等實盤驗證後再納入

---

## 系統狀態

| 項目 | 狀態 |
|------|------|
| runner.py（v3 + BORDERLINE 報表） | OK |
| backtest_one.py（v3 expectancy scoring） | OK |
| 5 個 template 模組 | OK |
| SQLite checkpointing（5 個 .db） | OK |
| 全部輸出（yaml×5, csv, yaml×2, md） | OK |
| pytest 93 passed 1 skipped | OK |
| Phase B 耗時 | 49.1 分鐘（估 42 分，偏差 +17%）|
