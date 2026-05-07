# TIERING REPORT — 20260504_203450

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 3 | 50% | STRONG：可用，建議 50% 部位 |
| B | 3 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 11 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 27 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 18 / 45**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1802 | low_vol_pullback | +7.6% | 24.57 | 9 | -14.0% | 5.00 | X | X | X | PF_lower=5.00 ≥ 2.0, exp=+7.6% ≥ 5%, n=9≥8, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥3.0 自動晉升 |

### Tier A — 部位上限 50% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1303 | gap_continuation | +11.5% | 7.68 | 9 | -22.7% | 1.63 | X | O | X | PF_lower=1.63 ≥ 1.5, exp=+11.5% ≥ 3%, n=9≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 2317 | gap_continuation | +11.1% | inf | 6 | -13.0% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+11.1% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥2.0 自動晉升 |
| 1301 | gap_continuation | +5.6% | inf | 6 | -9.3% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+5.6% ≥ 3%, n=6≥6, holdout=[A_new=NA B=X C=NA], gate=PF_lower≥2.0 自動晉升 |

### Tier B — 部位上限 30% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2454 | monthly_revenue_event | +8.7% | 11.00 | 10 | -12.1% | 1.37 | X | X | X | PF_lower=1.37 ≥ 1.0, exp=+8.7% ≥ 2%, n=10≥5, holdout=[A_new=NA B=NA C=NA] |
| 2383 | donchian_breakout | +8.4% | 3.28 | 26 | -28.6% | 1.03 | X | X | O | PF_lower=1.03 ≥ 1.0, exp=+8.4% ≥ 2%, n=26≥5, holdout=[A_new=NA B=X C=O] |
| 1326 | low_vol_pullback | +3.5% | 7.31 | 8 | -8.3% | 1.48 | X | O | X | PF_lower=1.48 ≥ 1.0, exp=+3.5% ≥ 2%, n=8≥5, holdout=[A_new=NA B=O C=X] |

### Tier C — 部位上限 15% （共 11 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2376 | momentum_hold | +35.7% | 11.97 | 5 | -32.9% | 0.85 | X | X | X | PF_lower=0.85 ≥ 0.7, exp=+35.7% ≥ 1%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 2408 | chip_momentum | +16.9% | 8.22 | 10 | -34.8% | 0.99 | X | X | X | PF_lower=0.99 ≥ 0.7, exp=+16.9% ≥ 1%, n=10≥5, holdout=[A_new=NA B=X C=NA] |
| 00919 | momentum_hold | +14.1% | 7.04 | 3 | -11.0% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=7.04 ≥ 3.0, exp=+14.1% ≥ 5%, |DD|=11% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 006208 | bollinger_squeeze | +8.0% | 13.79 | 4 | -6.7% | N/A | X | O | X | LOW_N_RESCUE：n=4, raw_PF=13.79 ≥ 3.0, exp=+8.0% ≥ 5%, |DD|=7% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 1560 | mean_reversion | +7.1% | 6.93 | 7 | -11.1% | 0.97 | X | X | X | PF_lower=0.97 ≥ 0.7, exp=+7.1% ≥ 1%, n=7≥5, holdout=[A_new=NA B=NA C=X] |
| 2337 | low_vol_pullback | +5.4% | 4.12 | 5 | -8.6% | 0.74 | X | X | X | PF_lower=0.74 ≥ 0.7, exp=+5.4% ≥ 1%, n=5≥5, holdout=[A_new=NA B=X C=NA] |
| 2353 | donchian_breakout | +5.3% | 3.09 | 8 | -16.2% | 0.73 | X | X | X | PF_lower=0.73 ≥ 0.7, exp=+5.3% ≥ 1%, n=8≥5, holdout=[A_new=NA B=NA C=X] |
| 2369 | low_vol_pullback | +3.6% | 3.90 | 7 | -13.4% | 0.77 | X | X | X | PF_lower=0.77 ≥ 0.7, exp=+3.6% ≥ 1%, n=7≥5, holdout=[A_new=NA B=NA C=X] |
| 2382 | low_vol_pullback | +3.0% | 2.09 | 16 | -18.4% | 0.76 | X | X | X | PF_lower=0.76 ≥ 0.7, exp=+3.0% ≥ 1%, n=16≥5, holdout=[A_new=NA B=X C=X] |
| 1402 | low_vol_pullback | +2.7% | 5.07 | 6 | -5.5% | 0.77 | X | O | X | PF_lower=0.77 ≥ 0.7, exp=+2.7% ≥ 1%, n=6≥5, holdout=[A_new=NA B=O C=X] |
| 2330 | gap_continuation | +1.1% | 1.55 | 42 | -29.2% | 0.72 | X | O | X | PF_lower=0.72 ≥ 0.7, exp=+1.1% ≥ 1%, n=42≥5, holdout=[A_new=NA B=O C=X] |

### Tier F — 部位上限 0% （共 27 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2344 | momentum_hold | +80.1% | 12.64 | 4 | -26.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2881 | momentum_hold | +71.4% | inf | 1 | -12.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2002 | monthly_revenue_event | +26.5% | inf | 1 | -0.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2615 | donchian_breakout | +17.9% | 3.47 | 7 | -26.2% | 0.44 | X | X | X | FAIL：PF_lower=0.44, exp=+17.9%, n=7, holdout=[A_new=NA B=NA C=NA] |
| 2308 | volume_breakout | +15.4% | 3.43 | 6 | -24.9% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+15.4%, n=6, holdout=[A_new=NA B=O C=X] |
| 1605 | bollinger_squeeze | +11.0% | 4.08 | 5 | -21.2% | 0.25 | X | X | X | FAIL：PF_lower=0.25, exp=+11.0%, n=5, holdout=[A_new=NA B=X C=NA] |
| 2603 | monthly_revenue_event | +10.9% | 13.33 | 2 | -5.3% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2426 | mean_reversion | +10.7% | 8.24 | 3 | -17.5% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2027 | gap_continuation | +8.4% | 2.30 | 4 | -31.7% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2345 | gap_continuation | +6.6% | 2.46 | 10 | -31.6% | 0.33 | X | X | O | FAIL：PF_lower=0.33, exp=+6.6%, n=10, holdout=[A_new=NA B=X C=O] |
| 2474 | mean_reversion | +6.0% | inf | 1 | -0.4% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2324 | chip_momentum | +5.5% | 2.97 | 11 | -18.4% | 0.48 | X | X | X | FAIL：PF_lower=0.48, exp=+5.5%, n=11, holdout=[A_new=NA B=X C=X] |
| 1809 | chip_momentum | +3.5% | 1.32 | 11 | -35.8% | 0.06 | X | X | X | FAIL：PF_lower=0.06, exp=+3.5%, n=11, holdout=[A_new=NA B=NA C=NA] |
| 2327 | donchian_breakout | +3.5% | 1.27 | 7 | -37.1% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+3.5%, n=7, holdout=[A_new=NA B=O C=NA] |
| 2360 | gap_continuation | +3.4% | 1.82 | 9 | -30.1% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+3.4%, n=9, holdout=[A_new=NA B=O C=X] |
| 2618 | momentum_hold | +3.1% | 2.70 | 14 | -23.5% | 0.38 | X | X | O | FAIL：PF_lower=0.38, exp=+3.1%, n=14, holdout=[A_new=NA B=NA C=O] |
| 00940 | momentum_hold | +2.7% | inf | 1 | -7.3% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2379 | mean_reversion | +2.5% | 2.49 | 5 | -13.3% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+2.5%, n=5, holdout=[A_new=NA B=NA C=X] |
| 1102 | trend_pullback | +2.0% | inf | 1 | -3.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 0056 | donchian_breakout | +1.8% | 2.09 | 11 | -10.4% | 0.37 | X | X | X | FAIL：PF_lower=0.37, exp=+1.8%, n=11, holdout=[A_new=NA B=X C=X] |
| 2303 | chip_momentum | +1.5% | 1.42 | 20 | -29.8% | 0.25 | X | O | X | FAIL：PF_lower=0.25, exp=+1.5%, n=20, holdout=[A_new=NA B=O C=X] |
| 00878 | bollinger_squeeze | +1.3% | 1.96 | 10 | -11.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.3%, n=10, holdout=[A_new=NA B=NA C=X] |
| 1216 | mean_reversion | +0.9% | 1.36 | 4 | -9.0% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1101 | low_vol_pullback | +0.6% | 1.15 | 3 | -8.7% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2105 | chip_momentum | +0.4% | 1.04 | 17 | -23.7% | 0.20 | X | X | X | FAIL：PF_lower=0.20, exp=+0.4%, n=17, holdout=[A_new=NA B=NA C=X] |
| 2207 | chip_streak | -0.0% | 0.91 | 8 | -23.5% | 0.02 | X | X | X | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 1227 | monthly_revenue_event | -0.7% | 0.00 | 2 | -3.3% | N/A | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
