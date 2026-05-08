# TIERING REPORT — 20260504_203450

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 4 | 50% | STRONG：可用，建議 50% 部位 |
| B | 7 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 18 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 50 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 30 / 80**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1802 | low_vol_pullback | +7.6% | 24.57 | 9 | -14.0% | 5.00 | X | X | X | PF_lower=5.00 ≥ 2.0, exp=+7.6% ≥ 5%, n=9≥8, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥3.0 自動晉升 |

### Tier A — 部位上限 50% （共 4 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3017 | gap_continuation | +13.1% | 14.06 | 12 | -29.1% | 2.70 | X | X | X | PF_lower=2.70 ≥ 1.5, exp=+13.1% ≥ 3%, n=12≥6, holdout=[A_new=NA B=X C=X], gate=PF_lower≥2.0 自動晉升 |
| 1303 | gap_continuation | +11.5% | 7.68 | 9 | -22.7% | 1.63 | X | O | X | PF_lower=1.63 ≥ 1.5, exp=+11.5% ≥ 3%, n=9≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 2317 | gap_continuation | +11.1% | inf | 6 | -13.0% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+11.1% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥2.0 自動晉升 |
| 1301 | gap_continuation | +5.6% | inf | 6 | -9.3% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+5.6% ≥ 3%, n=6≥6, holdout=[A_new=NA B=X C=NA], gate=PF_lower≥2.0 自動晉升 |

### Tier B — 部位上限 30% （共 7 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2454 | monthly_revenue_event | +8.7% | 11.00 | 10 | -12.1% | 1.37 | X | X | X | PF_lower=1.37 ≥ 1.0, exp=+8.7% ≥ 2%, n=10≥5, holdout=[A_new=NA B=NA C=NA] |
| 2383 | donchian_breakout | +8.4% | 3.28 | 26 | -28.6% | 1.03 | X | X | O | PF_lower=1.03 ≥ 1.0, exp=+8.4% ≥ 2%, n=26≥5, holdout=[A_new=NA B=X C=O] |
| 3189 | chip_momentum | +5.9% | 3.04 | 24 | -34.8% | 1.10 | X | X | X | PF_lower=1.10 ≥ 1.0, exp=+5.9% ≥ 2%, n=24≥5, holdout=[A_new=NA B=NA C=NA] |
| 6770 | low_vol_pullback | +4.6% | 9.19 | 9 | -20.9% | 1.77 | X | X | X | PF_lower=1.77 ≥ 1.0, exp=+4.6% ≥ 2%, n=9≥5, holdout=[A_new=NA B=NA C=NA] |
| 6515 | gap_continuation | +3.9% | 3.44 | 27 | -19.3% | 1.14 | X | X | O | PF_lower=1.14 ≥ 1.0, exp=+3.9% ≥ 2%, n=27≥5, holdout=[A_new=NA B=NA C=O] |
| 1326 | low_vol_pullback | +3.5% | 7.31 | 8 | -8.3% | 1.48 | X | O | X | PF_lower=1.48 ≥ 1.0, exp=+3.5% ≥ 2%, n=8≥5, holdout=[A_new=NA B=O C=X] |
| 2882 | low_vol_pullback | +3.4% | 5.46 | 5 | -6.4% | 1.09 | X | O | O | PF_lower=1.09 ≥ 1.0, exp=+3.4% ≥ 2%, n=5≥5, holdout=[A_new=NA B=O C=O] |

### Tier C — 部位上限 15% （共 18 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2376 | momentum_hold | +35.7% | 11.97 | 5 | -32.9% | 0.85 | X | X | X | PF_lower=0.85 ≥ 0.7, exp=+35.7% ≥ 1%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 2408 | chip_momentum | +16.9% | 8.22 | 10 | -34.8% | 0.99 | X | X | X | PF_lower=0.99 ≥ 0.7, exp=+16.9% ≥ 1%, n=10≥5, holdout=[A_new=NA B=X C=NA] |
| 00919 | momentum_hold | +14.1% | 7.04 | 3 | -11.0% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=7.04 ≥ 3.0, exp=+14.1% ≥ 5%, |DD|=11% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2883 | mean_reversion | +10.1% | 7.40 | 4 | -7.6% | N/A | X | O | O | LOW_N_RESCUE：n=4, raw_PF=7.40 ≥ 3.0, exp=+10.1% ≥ 5%, |DD|=8% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 4958 | gap_continuation | +8.7% | 4.48 | 7 | -18.1% | 0.79 | X | X | O | PF_lower=0.79 ≥ 0.7, exp=+8.7% ≥ 1%, n=7≥5, holdout=[A_new=NA B=X C=O] |
| 006208 | bollinger_squeeze | +8.0% | 13.79 | 4 | -6.7% | N/A | X | O | X | LOW_N_RESCUE：n=4, raw_PF=13.79 ≥ 3.0, exp=+8.0% ≥ 5%, |DD|=7% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 1560 | mean_reversion | +7.1% | 6.93 | 7 | -11.1% | 0.97 | X | X | X | PF_lower=0.97 ≥ 0.7, exp=+7.1% ≥ 1%, n=7≥5, holdout=[A_new=NA B=NA C=X] |
| 8046 | mean_reversion | +5.6% | 3.88 | 6 | -15.6% | 0.83 | X | X | X | PF_lower=0.83 ≥ 0.7, exp=+5.6% ≥ 1%, n=6≥5, holdout=[A_new=NA B=X C=X] |
| 2337 | low_vol_pullback | +5.4% | 4.12 | 5 | -8.6% | 0.74 | X | X | X | PF_lower=0.74 ≥ 0.7, exp=+5.4% ≥ 1%, n=5≥5, holdout=[A_new=NA B=X C=NA] |
| 2353 | donchian_breakout | +5.3% | 3.09 | 8 | -16.2% | 0.73 | X | X | X | PF_lower=0.73 ≥ 0.7, exp=+5.3% ≥ 1%, n=8≥5, holdout=[A_new=NA B=NA C=X] |
| 4904 | momentum_hold | +5.2% | 13.16 | 3 | -18.4% | N/A | X | X | O | LOW_N_RESCUE：n=3, raw_PF=13.16 ≥ 3.0, exp=+5.2% ≥ 5%, |DD|=18% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |
| 5871 | mean_reversion | +5.1% | 3.44 | 4 | -10.8% | N/A | X | O | X | LOW_N_RESCUE：n=4, raw_PF=3.44 ≥ 3.0, exp=+5.1% ≥ 5%, |DD|=11% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 3008 | mean_reversion | +3.9% | 3.72 | 6 | -7.0% | 0.77 | X | O | X | PF_lower=0.77 ≥ 0.7, exp=+3.9% ≥ 1%, n=6≥5, holdout=[A_new=NA B=O C=NA] |
| 2369 | low_vol_pullback | +3.6% | 3.90 | 7 | -13.4% | 0.77 | X | X | X | PF_lower=0.77 ≥ 0.7, exp=+3.6% ≥ 1%, n=7≥5, holdout=[A_new=NA B=NA C=X] |
| 2382 | low_vol_pullback | +3.0% | 2.09 | 16 | -18.4% | 0.76 | X | X | X | PF_lower=0.76 ≥ 0.7, exp=+3.0% ≥ 1%, n=16≥5, holdout=[A_new=NA B=X C=X] |
| 1402 | low_vol_pullback | +2.7% | 5.07 | 6 | -5.5% | 0.77 | X | O | X | PF_lower=0.77 ≥ 0.7, exp=+2.7% ≥ 1%, n=6≥5, holdout=[A_new=NA B=O C=X] |
| 3711 | low_vol_pullback | +2.0% | 1.83 | 24 | -35.0% | 0.75 | X | X | X | PF_lower=0.75 ≥ 0.7, exp=+2.0% ≥ 1%, n=24≥5, holdout=[A_new=NA B=NA C=NA] |
| 2330 | gap_continuation | +1.1% | 1.55 | 42 | -29.2% | 0.72 | X | O | X | PF_lower=0.72 ≥ 0.7, exp=+1.1% ≥ 1%, n=42≥5, holdout=[A_new=NA B=O C=X] |

### Tier F — 部位上限 0% （共 50 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2344 | momentum_hold | +80.1% | 12.64 | 4 | -26.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2881 | momentum_hold | +71.4% | inf | 1 | -12.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3231 | chip_momentum | +48.2% | 2.50 | 7 | -36.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+48.2%, n=7, holdout=[A_new=NA B=NA C=NA] |
| 3034 | momentum_hold | +43.9% | 12.47 | 2 | -14.8% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2356 | chip_momentum | +43.2% | inf | 1 | -10.2% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6505 | trend_pullback | +39.8% | inf | 1 | -5.7% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2002 | monthly_revenue_event | +26.5% | inf | 1 | -0.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3037 | monthly_revenue_event | +19.1% | inf | 1 | -2.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2615 | donchian_breakout | +17.9% | 3.47 | 7 | -26.2% | 0.44 | X | X | X | FAIL：PF_lower=0.44, exp=+17.9%, n=7, holdout=[A_new=NA B=NA C=NA] |
| 2308 | volume_breakout | +15.4% | 3.43 | 6 | -24.9% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+15.4%, n=6, holdout=[A_new=NA B=O C=X] |
| 3661 | bollinger_squeeze | +15.2% | 5.74 | 4 | -37.8% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9914 | bollinger_squeeze | +12.6% | inf | 2 | -9.7% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2885 | momentum_hold | +12.1% | 16.16 | 5 | -20.5% | 0.27 | X | X | X | FAIL：PF_lower=0.27, exp=+12.1%, n=5, holdout=[A_new=NA B=X C=NA] |
| 2891 | momentum_hold | +11.3% | 8.83 | 2 | -20.4% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1605 | bollinger_squeeze | +11.0% | 4.08 | 5 | -21.2% | 0.25 | X | X | X | FAIL：PF_lower=0.25, exp=+11.0%, n=5, holdout=[A_new=NA B=X C=NA] |
| 2603 | monthly_revenue_event | +10.9% | 13.33 | 2 | -5.3% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2426 | mean_reversion | +10.7% | 8.24 | 3 | -17.5% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2027 | gap_continuation | +8.4% | 2.30 | 4 | -31.7% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2345 | gap_continuation | +6.6% | 2.46 | 10 | -31.6% | 0.33 | X | X | O | FAIL：PF_lower=0.33, exp=+6.6%, n=10, holdout=[A_new=NA B=X C=O] |
| 4938 | mean_reversion | +6.5% | inf | 2 | -2.5% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2474 | mean_reversion | +6.0% | inf | 1 | -0.4% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6488 | mean_reversion | +5.8% | 2.09 | 6 | -17.1% | 0.27 | X | O | X | FAIL：PF_lower=0.27, exp=+5.8%, n=6, holdout=[A_new=NA B=O C=NA] |
| 2324 | chip_momentum | +5.5% | 2.97 | 11 | -18.4% | 0.48 | X | X | X | FAIL：PF_lower=0.48, exp=+5.5%, n=11, holdout=[A_new=NA B=X C=X] |
| 2886 | momentum_hold | +5.0% | 2.84 | 6 | -25.6% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+5.0%, n=6, holdout=[A_new=NA B=X C=X] |
| 6669 | monthly_revenue_event | +4.5% | inf | 1 | -1.4% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2892 | mean_reversion | +3.8% | inf | 1 | -3.2% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1809 | chip_momentum | +3.5% | 1.32 | 11 | -35.8% | 0.06 | X | X | X | FAIL：PF_lower=0.06, exp=+3.5%, n=11, holdout=[A_new=NA B=NA C=NA] |
| 2327 | donchian_breakout | +3.5% | 1.27 | 7 | -37.1% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+3.5%, n=7, holdout=[A_new=NA B=O C=NA] |
| 2360 | gap_continuation | +3.4% | 1.82 | 9 | -30.1% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+3.4%, n=9, holdout=[A_new=NA B=O C=X] |
| 2884 | gap_continuation | +3.4% | 3.69 | 6 | -9.2% | 0.38 | X | O | O | FAIL：PF_lower=0.38, exp=+3.4%, n=6, holdout=[A_new=NA B=O C=O] |
| 2618 | momentum_hold | +3.1% | 2.70 | 14 | -23.5% | 0.38 | X | X | O | FAIL：PF_lower=0.38, exp=+3.1%, n=14, holdout=[A_new=NA B=NA C=O] |
| 3045 | low_vol_pullback | +3.0% | 2.80 | 2 | -3.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5880 | donchian_breakout | +2.8% | 2.19 | 6 | -13.8% | 0.00 | X | O | O | FAIL：PF_lower=0.00, exp=+2.8%, n=6, holdout=[A_new=NA B=O C=O] |
| 00940 | momentum_hold | +2.7% | inf | 1 | -7.3% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9940 | low_vol_pullback | +2.7% | 2.55 | 3 | -7.3% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2379 | mean_reversion | +2.5% | 2.49 | 5 | -13.3% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+2.5%, n=5, holdout=[A_new=NA B=NA C=X] |
| 1102 | trend_pullback | +2.0% | inf | 1 | -3.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 0056 | donchian_breakout | +1.8% | 2.09 | 11 | -10.4% | 0.37 | X | X | X | FAIL：PF_lower=0.37, exp=+1.8%, n=11, holdout=[A_new=NA B=X C=X] |
| 2303 | chip_momentum | +1.5% | 1.42 | 20 | -29.8% | 0.25 | X | O | X | FAIL：PF_lower=0.25, exp=+1.5%, n=20, holdout=[A_new=NA B=O C=X] |
| 00878 | bollinger_squeeze | +1.3% | 1.96 | 10 | -11.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.3%, n=10, holdout=[A_new=NA B=NA C=X] |
| 2412 | mean_reversion | +1.3% | 3.80 | 5 | -8.4% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+1.3%, n=5, holdout=[A_new=NA B=O C=X] |
| 5347 | mean_reversion | +1.0% | 1.17 | 5 | -31.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.0%, n=5, holdout=[A_new=NA B=X C=NA] |
| 1216 | mean_reversion | +0.9% | 1.36 | 4 | -9.0% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1101 | low_vol_pullback | +0.6% | 1.15 | 3 | -8.7% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2105 | chip_momentum | +0.4% | 1.04 | 17 | -23.7% | 0.20 | X | X | X | FAIL：PF_lower=0.20, exp=+0.4%, n=17, holdout=[A_new=NA B=NA C=X] |
| 2912 | volume_breakout | +0.1% | 1.11 | 3 | -4.4% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2207 | chip_streak | -0.0% | 0.91 | 8 | -23.5% | 0.02 | X | X | X | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 9921 | chip_streak | -0.3% | 0.75 | 4 | -10.9% | N/A | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 1227 | monthly_revenue_event | -0.7% | 0.00 | 2 | -3.3% | N/A | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 6271 | trend_pullback | -1.0% | 0.00 | 1 | -5.1% | N/A | X | X | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
