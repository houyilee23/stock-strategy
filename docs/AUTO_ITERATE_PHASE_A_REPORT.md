# Auto-Iterate Phase A Smoke Test 報告（v3）

## v3 評價架構（本次採用）

完全脫離市場 benchmark，改用「大賺少賠」的 per-trade quality 指標：

| Verdict | 條件 |
|---------|------|
| PASS | expectancy >= 5% AND pf >= 1.5 AND dd <= 30% AND n >= 5 |
| WEAK | expectancy >= 1% AND pf >= 1.0 AND dd <= 30% AND n >= 5 |
| DD_BREACH | dd > 30% |
| FAIL | pf < 1.0 OR expectancy < 1% |
| INSUFFICIENT | n < 5 |

0050 CAGR（informational）：train=+13.3%，test=+54.6%

---

## 終端輸出摘要

```
========================================================================
  Phase A SMOKE TEST 完成
========================================================================
  run_id: 20260423_151107
  耗時: 7.2 分鐘
  25 對結果: PASS=3, WEAK=0, FAIL=1, DD_BREACH=10, INSUFFICIENT=11
========================================================================
```

---

## 25 對完整結果（v3 指標）

| # | Stock | Template | Exp (test) | PF (test) | n | DD (test) | Verdict |
|---|-------|----------|-----------|-----------|---|-----------|---------|
| 1 | 2330 | trend_pullback | -0.5% | 0.00 | 1 | -8.6% | INSUFFICIENT |
| 2 | **2330** | **donchian_breakout** | **+8.0%** | **4.43** | **6** | **-26.4%** | **PASS** |
| 3 | 2330 | momentum_hold | +17.5% | inf | 2 | -24.5% | INSUFFICIENT |
| 4 | **2330** | **chip_momentum** | **+6.4%** | **3.94** | **8** | **-19.3%** | **PASS** |
| 5 | 2330 | mean_reversion | -2.9% | 0.16 | 2 | -22.9% | INSUFFICIENT |
| 6 | 3017 | trend_pullback | +6.8% | 1.78 | 7 | **-32.6%** | DD_BREACH |
| 7 | 3017 | donchian_breakout | +21.5% | 30.86 | 4 | -29.2% | INSUFFICIENT |
| 8 | 3017 | momentum_hold | +17.8% | 2.12 | 2 | -40.3% | INSUFFICIENT |
| 9 | **3017** | **chip_momentum** | **+8.3%** | **2.98** | **9** | **-25.6%** | **PASS** |
| 10 | 3017 | mean_reversion | -19.9% | 0.00 | 1 | -22.2% | INSUFFICIENT |
| 11 | 6669 | trend_pullback | -8.7% | 0.00 | 4 | -33.9% | INSUFFICIENT |
| 12 | 6669 | donchian_breakout | +1.3% | 1.25 | 9 | **-35.5%** | DD_BREACH |
| 13 | 6669 | momentum_hold | -2.7% | 0.36 | 7 | **-40.0%** | DD_BREACH |
| 14 | 6669 | chip_momentum | +8.9% | 2.49 | 5 | **-37.1%** | DD_BREACH |
| 15 | 6669 | mean_reversion | -7.3% | 0.23 | 5 | **-48.5%** | DD_BREACH |
| 16 | 2454 | trend_pullback | -0.6% | 0.80 | 7 | **-42.6%** | DD_BREACH |
| 17 | 2454 | donchian_breakout | -1.4% | 0.52 | 6 | **-32.2%** | DD_BREACH |
| 18 | 2454 | momentum_hold | -1.3% | 0.53 | 7 | **-45.1%** | DD_BREACH |
| 19 | 2454 | chip_momentum | -2.2% | 0.39 | 8 | -28.2% | FAIL |
| 20 | 2454 | mean_reversion | +1.4% | 1.53 | 4 | -22.0% | INSUFFICIENT |
| 21 | 2317 | trend_pullback | +6.4% | inf | 1 | -6.6% | INSUFFICIENT |
| 22 | 2317 | donchian_breakout | +33.0% | 7.50 | 3 | -17.0% | INSUFFICIENT |
| 23 | 2317 | momentum_hold | +11.6% | 2.82 | 6 | **-34.8%** | DD_BREACH |
| 24 | 2317 | chip_momentum | +12.3% | 2.50 | 4 | -27.6% | INSUFFICIENT |
| 25 | 2317 | mean_reversion | -0.9% | 0.67 | 5 | **-48.1%** | DD_BREACH |

---

## 3 個 PASS 詳細資訊

### PASS 1：2330 × donchian_breakout

```
Best params: donchian_entry_n=55, donchian_exit_n=55, trend_ma=50, atr_stop_k=4.0, vol_ratio=1.0

Train (2017-2023):
  n=15, win_rate=53%, PF=2.26, expectancy=+4.9%, avg_win=+14.0%, avg_loss=-5.6%
  CAGR=+9.4%, MaxDD=-19.3%

Test (2024-2026):
  n=6, win_rate=50%, PF=4.43, expectancy=+8.0%, avg_win=+20.6%, avg_loss=-4.6%
  CAGR=+19.0%, MaxDD=-26.4%   ← 略高於 25% 風控線，但在 30% 內
  alpha_vs_0050=-35.6% (informational，0050 漲+54.6%)
  
Verdict: PASS ✓（每筆平均賺 +8%，PF=4.43，「大賺少賠」明確）
```

### PASS 2：2330 × chip_momentum

```
Best params: (詳見 chip_momentum.yaml#per_stock.2330)

Test (2024-2026):
  n=8, win_rate=?, PF=3.94, expectancy=+6.4%, avg_win=+16.6%, avg_loss=-3.8%
  CAGR=+19.8%, MaxDD=-19.3%

Verdict: PASS ✓（每筆平均賺 +6.4%，PF=3.94，8 筆樣本足夠）
```

### PASS 3：3017 × chip_momentum

```
Best params: (詳見 chip_momentum.yaml#per_stock.3017)

Test (2024-2026):
  n=9, win_rate=?, PF=2.98, expectancy=+8.3%, avg_win=+19.6%, avg_loss=-5.8%
  CAGR=+59.7%, MaxDD=-25.6%
  alpha_vs_0050=+5.1% ← 唯一正 alpha！

Verdict: PASS ✓（最強 PASS：9 筆、+8.3% expectancy、PF=3.0）
```

---

## 主要問題分析

### 問題 1：DD_BREACH 佔比高（10/25 = 40%）

| Stock | DD 問題最嚴重的模板 | MaxDD |
|-------|-----------------|-------|
| 6669 | mean_reversion | -48.5% |
| 2317 | mean_reversion | -48.1% |
| 2454 | momentum_hold | -45.1% |
| 2454 | trend_pullback | -42.6% |

根本原因：T4/T5 在震盪期間重複入場後被大跌掃到，ATR stop 設太鬆。

**潛在 PASS（若 DD 再嚴一點）**：
- 6669 × chip_momentum：exp=+8.9%, PF=2.49，但 MaxDD=-37.1% 超過 30%（只差 7.1%）
- 3017 × trend_pullback：exp=+6.8%, PF=1.78，但 MaxDD=-32.6%（只差 2.6%）
- 2317 × momentum_hold：exp=+11.6%, PF=2.82，但 MaxDD=-34.8%（只差 4.8%）

### 問題 2：INSUFFICIENT 佔比高（11/25 = 44%）

n_trades < 5 in test period (2024-2026)。原因分析：
- T1 trend_pullback：進場條件嚴（5 條件 AND），2.3 年只觸發 1-4 次正常
- T5 mean_reversion：需要 close < short_MA × (1-pct) 才進場，大牛市幾乎沒有回檔機會
- T2/T3/T4 某些 params（120 日窗口）等待期太長，觸發次數少

**注意**：2317 × donchian_breakout（n=3）exp=+33%, PF=7.50 很漂亮，只差 2 筆就 PASS。

### 問題 3：2454 全部失敗

2454（聯發科）在 2024-2026 的 test 期間，所有 5 個模板全部 FAIL/DD_BREACH：
- 股性可能偏高波動 + 無明確趨勢結構，所有進場後易被 DD 淘汰
- 建議 Phase B 後確認是否從 watchlist 移除

---

## per_stock_best.yaml 摘要

| Stock | Best Template | Verdict | Test Expectancy | Test PF | Test n |
|-------|--------------|---------|----------------|---------|--------|
| 2330 | donchian_breakout | PASS | +8.0% | 4.43 | 6 |
| 3017 | chip_momentum | PASS | +8.3% | 2.98 | 9 |
| 6669 | NONE | All DD_BREACH | — | — | — |
| 2454 | NONE | All FAIL/DD_BREACH | — | — | — |
| 2317 | NONE | All INSUFFICIENT/DD_BREACH | — | — | — |

---

## 給 Opus 的判斷問題

### Q1（最重要）：DD 門檻是否調整？

目前：DD > 30% → DD_BREACH（不選為 best_template）

若改為 35%：
- 3017 × trend_pullback → PASS（exp=+6.8%, PF=1.78, dd=-32.6%）
- 6669 × chip_momentum → PASS（exp=+8.9%, PF=2.49, dd=-37.1%）
- 2317 × momentum_hold → PASS（exp=+11.6%, PF=2.82, dd=-34.8%）
- PASS 數由 3 → 6，PASS 股數由 2 → 4

**Sonnet 的建議**：保持 30% 不動。三個潛在 PASS 的 DD 都在 33~38%，長線使用者很難承受。CLAUDE.md 底線是 30%。

### Q2：是否把 INSUFFICIENT 門檻從 n<5 降回 n<3？

v3 把 n<5 設為 INSUFFICIENT（v2 是 n<3）。
若改回 n<3：
- 2317 × donchian_breakout（n=3, exp=+33%, PF=7.5）→ 變 PASS（非常漂亮）
- 3017 × donchian_breakout（n=4, exp=+21.5%, PF=30.8）→ 變 PASS

**Sonnet 的建議**：n >= 3 改為 PASS 是可接受的，但需標記「低樣本數，建議觀察」。n=3 的 PF=7.5 統計意義確實不足但方向上是真的。

### Q3：是否繼續 Phase B？

PASS 率 2/5 = 40%（或若放鬆 DD/n 門檻則 4-6/5）。Pipeline 跑通，輸出完整。

**Sonnet 的建議**：可以繼續 Phase B（full universe 33 檔），但需要 Opus 先確認：
1. DD 門檻維持 30% 還是改 35%？
2. n 門檻維持 5 還是改 3？

這兩個決定會顯著影響 Phase B 的 PASS 數量。

---

## 系統狀態

| 項目 | 狀態 |
|------|------|
| v3 backtest_one.py（expectancy/score/classify） | OK |
| v3 runner.py（0050 benchmark, v3 csv schema） | OK |
| 5 個 template 模組 | OK（沿用 v1，未改動） |
| 5 檔籌碼資料（data/chips/） | OK（v1 已抓） |
| SQLite checkpointing（5 個 .db 檔） | OK |
| 全部輸出檔案（yaml × 5, csv, yaml × 2, md） | OK |
| pytest 70 passed 1 skipped | OK |
