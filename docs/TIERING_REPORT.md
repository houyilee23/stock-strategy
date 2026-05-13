# TIERING REPORT — 20260509_015024

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 5 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 10 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 32 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 16 / 50**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3443 | mean_reversion | +8.0% | 20.49 | 8 | -18.7% | 3.24 | X | O | X | PF_lower=3.24 ≥ 2.0, exp=+8.0% ≥ 5%, n=8≥8, holdout=[A_new=NA B=O C=X], gate=any holdout PASS |

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 5 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2059 | donchian_breakout | +15.6% | 8.53 | 11 | -23.9% | 1.76 | X | X | X | PF_lower=1.76 ≥ 1.0, exp=+15.6% ≥ 2%, n=11≥5, holdout=[A_new=NA B=X C=X] |
| 3081 | gap_continuation | +13.9% | 6.94 | 12 | -25.8% | 1.04 | X | X | X | PF_lower=1.04 ≥ 1.0, exp=+13.9% ≥ 2%, n=12≥5, holdout=[A_new=NA B=NA C=X] |
| 6182 | mean_reversion | +13.7% | 19.51 | 5 | -17.2% | 3.82 | X | O | X | PF_lower=3.82 ≥ 1.0, exp=+13.7% ≥ 2%, n=5≥5, holdout=[A_new=NA B=O C=X] |
| 1736 | mean_reversion | +8.9% | 14.13 | 5 | -14.3% | 1.48 | X | X | O | PF_lower=1.48 ≥ 1.0, exp=+8.9% ≥ 2%, n=5≥5, holdout=[A_new=NA B=X C=O] |
| 3035 | low_vol_pullback | +5.0% | 7.08 | 5 | -15.6% | 1.05 | X | X | O | PF_lower=1.05 ≥ 1.0, exp=+5.0% ≥ 2%, n=5≥5, holdout=[A_new=NA B=NA C=O] |

### Tier C — 部位上限 15% （共 10 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2409 | mean_reversion | +16.4% | inf | 3 | -16.5% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+16.4% ≥ 5%, |DD|=17% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 6116 | gap_continuation | +12.1% | 4.73 | 3 | -19.1% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=4.73 ≥ 3.0, exp=+12.1% ≥ 5%, |DD|=19% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2812 | momentum_hold | +10.0% | 22.14 | 4 | -16.6% | N/A | X | X | X | LOW_N_RESCUE：n=4, raw_PF=22.14 ≥ 3.0, exp=+10.0% ≥ 5%, |DD|=17% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 5314 | chip_momentum | +9.5% | 1.03 | 31 | -94.6% | 0.83 | X | X | X | PF_lower=0.83 ≥ 0.7, exp=+9.5% ≥ 1%, n=31≥5, holdout=[A_new=NA B=NA C=NA] |
| 3596 | gap_continuation | +9.2% | 19.03 | 4 | -7.6% | N/A | X | O | X | LOW_N_RESCUE：n=4, raw_PF=19.03 ≥ 3.0, exp=+9.2% ≥ 5%, |DD|=8% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 8081 | trend_pullback | +7.5% | 33.71 | 3 | -8.5% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=33.71 ≥ 3.0, exp=+7.5% ≥ 5%, |DD|=8% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2890 | low_vol_pullback | +7.5% | inf | 3 | -4.4% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+7.5% ≥ 5%, |DD|=4% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2888 | mean_reversion | +5.1% | 56.70 | 4 | -5.1% | N/A | X | O | O | LOW_N_RESCUE：n=4, raw_PF=56.70 ≥ 3.0, exp=+5.1% ≥ 5%, |DD|=5% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 6213 | low_vol_pullback | +3.1% | 3.64 | 8 | -14.1% | 0.80 | X | X | X | PF_lower=0.80 ≥ 0.7, exp=+3.1% ≥ 1%, n=8≥5, holdout=[A_new=NA B=X C=NA] |
| 6531 | low_vol_pullback | +1.8% | 2.69 | 17 | -24.0% | 0.94 | X | O | X | PF_lower=0.94 ≥ 0.7, exp=+1.8% ≥ 1%, n=17≥5, holdout=[A_new=NA B=O C=NA] |

### Tier F — 部位上限 0% （共 32 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 8454 | momentum_hold | +51.5% | inf | 2 | -26.7% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2723 | trend_pullback | +28.5% | inf | 1 | -13.0% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1582 | trend_pullback | +27.4% | inf | 1 | -12.9% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2014 | bollinger_squeeze | +21.0% | 2.29 | 4 | -29.5% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1503 | momentum_hold | +13.9% | 3.25 | 7 | -31.1% | 0.00 | X | X | O | FAIL：PF_lower=0.00, exp=+13.9%, n=7, holdout=[A_new=NA B=X C=O] |
| 2458 | mean_reversion | +13.4% | inf | 1 | -3.4% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2609 | gap_continuation | +12.4% | 1.30 | 13 | -65.3% | 0.19 | X | X | X | FAIL：PF_lower=0.19, exp=+12.4%, n=13, holdout=[A_new=NA B=NA C=X] |
| 1504 | donchian_breakout | +8.7% | 3.98 | 11 | -21.6% | 0.30 | X | X | X | FAIL：PF_lower=0.30, exp=+8.7%, n=11, holdout=[A_new=NA B=NA C=X] |
| 2823 | mean_reversion | +8.3% | inf | 1 | -4.9% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4961 | donchian_breakout | +7.1% | 1.50 | 7 | -39.7% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+7.1%, n=7, holdout=[A_new=NA B=O C=NA] |
| 2606 | mean_reversion | +7.0% | 1.55 | 7 | -36.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+7.0%, n=7, holdout=[A_new=NA B=X C=NA] |
| 8069 | bollinger_squeeze | +6.3% | inf | 2 | -6.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1907 | gap_continuation | +5.9% | inf | 2 | -3.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3481 | donchian_breakout | +5.7% | 1.83 | 8 | -23.9% | 0.10 | X | X | X | FAIL：PF_lower=0.10, exp=+5.7%, n=8, holdout=[A_new=NA B=NA C=NA] |
| 2009 | bollinger_squeeze | +4.7% | 1.27 | 4 | -42.8% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1717 | gap_continuation | +4.6% | 2.33 | 12 | -23.7% | 0.37 | X | X | X | FAIL：PF_lower=0.37, exp=+4.6%, n=12, holdout=[A_new=NA B=NA C=X] |
| 5876 | gap_continuation | +4.1% | inf | 1 | -3.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9907 | low_vol_pullback | +3.9% | inf | 2 | -6.1% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5269 | gap_continuation | +3.8% | 2.16 | 11 | -22.2% | 0.33 | X | X | X | FAIL：PF_lower=0.33, exp=+3.8%, n=11, holdout=[A_new=NA B=X C=X] |
| 6285 | mean_reversion | +3.7% | 4.07 | 2 | -9.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6121 | bollinger_squeeze | +2.6% | 2.14 | 4 | -15.0% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9933 | bollinger_squeeze | +2.4% | 5.98 | 3 | -6.2% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5388 | mean_reversion | +2.3% | 2.06 | 8 | -10.4% | 0.32 | X | X | O | FAIL：PF_lower=0.32, exp=+2.3%, n=8, holdout=[A_new=NA B=NA C=O] |
| 2887 | low_vol_pullback | +1.9% | 2.44 | 3 | -6.2% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4147 | trend_pullback | +1.6% | 3.71 | 2 | -6.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1456 | low_vol_pullback | +1.5% | 1.47 | 3 | -9.6% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1234 | mean_reversion | +1.5% | 3.06 | 4 | -5.3% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2049 | volume_breakout | +1.5% | 1.60 | 13 | -16.2% | 0.29 | X | O | X | FAIL：PF_lower=0.29, exp=+1.5%, n=13, holdout=[A_new=NA B=O C=NA] |
| 2867 | mean_reversion | +1.3% | 1.33 | 4 | -8.9% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2371 | momentum_hold | -0.3% | 0.85 | 2 | -28.2% | N/A | X | O | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 1521 | low_vol_pullback | -0.4% | 0.81 | 4 | -9.2% | N/A | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2227 | mean_reversion | -0.9% | 0.00 | 2 | -2.2% | N/A | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
