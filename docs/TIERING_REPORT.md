# TIERING REPORT — 20260424_220634

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 6 | 50% | STRONG：可用，建議 50% 部位 |
| B | 5 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 5 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 22 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 17 / 39**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2317 | gap_continuation | +8.4% | 11.47 | 9 | -15.1% | 2.72 | X | X | O | PF_lower=2.72 ≥ 2.0, exp=+8.4% ≥ 5%, n=9≥8, holdout=[A_new=NA B=X C=O], gate=any holdout PASS |

### Tier A — 部位上限 50% （共 6 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2330 | donchian_breakout | +11.3% | 32.12 | 7 | -15.4% | 2.63 | X | O | X | PF_lower=2.63 ≥ 1.5, exp=+11.3% ≥ 3%, n=7≥6, holdout=[A_new=NA B=O C=X], gate=any holdout PASS |
| 1560 | mean_reversion | +9.7% | 110.72 | 7 | -13.4% | 5.00 | X | X | O | PF_lower=5.00 ≥ 1.5, exp=+9.7% ≥ 3%, n=7≥6, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |
| 2360 | low_vol_pullback | +7.2% | 7.07 | 18 | -32.0% | 1.96 | X | O | O | PF_lower=1.96 ≥ 1.5, exp=+7.2% ≥ 3%, n=18≥6, holdout=[A_new=NA B=O C=O], gate=any holdout PASS |
| 6770 | low_vol_pullback | +6.9% | 13.57 | 6 | -20.9% | 2.01 | X | X | X | PF_lower=2.01 ≥ 1.5, exp=+6.9% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥2.0 自動晉升 |
| 2308 | low_vol_pullback | +6.3% | 10.72 | 7 | -17.2% | 1.53 | X | O | X | PF_lower=1.53 ≥ 1.5, exp=+6.3% ≥ 3%, n=7≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 3017 | gap_continuation | +5.0% | inf | 6 | -11.6% | 5.00 | X | X | O | PF_lower=5.00 ≥ 1.5, exp=+5.0% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |

### Tier B — 部位上限 30% （共 5 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1303 | gap_continuation | +17.7% | 8.43 | 5 | -22.7% | 1.80 | X | O | X | PF_lower=1.80 ≥ 1.0, exp=+17.7% ≥ 2%, n=5≥5, holdout=[A_new=NA B=O C=NA] |
| 6515 | donchian_breakout | +16.7% | 9.15 | 13 | -36.7% | 1.13 | X | X | O | PF_lower=1.13 ≥ 1.0, exp=+16.7% ≥ 2%, n=13≥5, holdout=[A_new=NA B=NA C=O] |
| 2454 | mean_reversion | +13.9% | inf | 5 | -22.3% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.0, exp=+13.9% ≥ 2%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 1802 | low_vol_pullback | +11.2% | 16.37 | 5 | -9.1% | 1.83 | X | X | X | PF_lower=1.83 ≥ 1.0, exp=+11.2% ≥ 2%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 3034 | low_vol_pullback | +6.1% | 25.57 | 5 | -5.2% | 3.08 | X | X | X | PF_lower=3.08 ≥ 1.0, exp=+6.1% ≥ 2%, n=5≥5, holdout=[A_new=NA B=X C=X] |

### Tier C — 部位上限 15% （共 5 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2383 | chip_momentum | +18.5% | 9.12 | 6 | -19.6% | 0.90 | X | X | X | PF_lower=0.90 ≥ 0.7, exp=+18.5% ≥ 1%, n=6≥5, holdout=[A_new=NA B=X C=X] |
| 1809 | donchian_breakout | +15.9% | 3.31 | 4 | -22.7% | N/A | X | O | O | LOW_N_RESCUE：n=4, raw_PF=3.31 ≥ 3.0, exp=+15.9% ≥ 5%, |DD|=23% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 1326 | trend_pullback | +11.6% | 14.81 | 4 | -6.7% | N/A | X | O | X | LOW_N_RESCUE：n=4, raw_PF=14.81 ≥ 3.0, exp=+11.6% ≥ 5%, |DD|=7% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 3711 | chip_momentum | +9.7% | 3.83 | 4 | -17.7% | N/A | X | X | X | LOW_N_RESCUE：n=4, raw_PF=3.83 ≥ 3.0, exp=+9.7% ≥ 5%, |DD|=18% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2345 | low_vol_pullback | +5.7% | 3.43 | 9 | -15.5% | 0.81 | X | X | O | PF_lower=0.81 ≥ 0.7, exp=+5.7% ≥ 1%, n=9≥5, holdout=[A_new=NA B=X C=O] |

### Tier F — 部位上限 0% （共 22 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2344 | donchian_breakout | +155.3% | 19.27 | 2 | -24.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2337 | monthly_revenue_event | +46.8% | inf | 2 | -39.2% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2408 | bollinger_squeeze | +29.9% | inf | 1 | -27.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3037 | monthly_revenue_event | +28.7% | inf | 2 | -20.8% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6505 | trend_pullback | +19.6% | inf | 2 | -10.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2379 | monthly_revenue_event | +19.0% | inf | 1 | -1.3% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2303 | mean_reversion | +17.4% | inf | 1 | -9.3% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2327 | bollinger_squeeze | +15.5% | 6.68 | 4 | -15.7% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1301 | trend_pullback | +15.4% | inf | 1 | -13.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4958 | bollinger_squeeze | +14.7% | 5.03 | 4 | -26.1% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2412 | momentum_hold | +12.7% | inf | 1 | -8.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6669 | chip_momentum | +8.9% | 2.49 | 5 | -37.1% | 0.12 | X | X | O | FAIL：PF_lower=0.12, exp=+8.9%, n=5, holdout=[A_new=NA B=NA C=O] |
| 2426 | gap_continuation | +7.6% | 1.63 | 4 | -24.7% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9940 | low_vol_pullback | +5.2% | inf | 1 | -1.4% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3008 | gap_continuation | +4.9% | 1.67 | 2 | -19.5% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4938 | chip_momentum | +4.4% | 2.43 | 3 | -21.8% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6271 | mean_reversion | +3.7% | inf | 1 | -5.3% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2382 | monthly_revenue_event | +2.8% | inf | 1 | -2.5% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3231 | mean_reversion | +0.9% | 4.75 | 2 | -8.3% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2002 | mean_reversion | -0.6% | 0.63 | 2 | -17.2% | N/A | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 1227 | donchian_breakout | -1.0% | 0.44 | 2 | -8.3% | N/A | X | X | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2324 | chip_momentum | -1.6% | 0.20 | 5 | -14.7% | 0.00 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |

## 3. 對照舊 run（20260423_151107）

舊 run verdict 制（PASS/WEAK/NONE）映射為粗略 tier：
PASS→A_old, WEAK→C_old, 其他→F。

**升級個股**（共 6 檔，前 5）：

| Stock | 舊 | 新 | Δ |
|-------|----|----|---|
| 2317 | F | S | +4 |
| 3034 | F | B | +2 |
| 2454 | F | B | +2 |
| 1303 | F | B | +2 |
| 1809 | F | C | +1 |

**降級個股**（共 5 檔，前 5）：

| Stock | 舊 | 新 | Δ |
|-------|----|----|---|
| 2383 | A_old | C | -2 |
| 3711 | A_old | C | -2 |
| 1802 | A_old | B | -1 |
| 6505 | C_old | F | -1 |
| 6515 | A_old | B | -1 |
