# TIERING REPORT — 20260520_015227

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 8 | 50% | STRONG：可用，建議 50% 部位 |
| B | 16 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 32 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 119 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 57 / 191**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2059 | gap_continuation | +16.7% | 14.43 | 12 | -35.9% | 2.48 | X | X | O | PF_lower=2.48 ≥ 2.0, exp=+16.7% ≥ 5%, n=12≥8, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |

### Tier A — 部位上限 50% （共 8 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3653 | gap_continuation | +20.9% | inf | 7 | -23.5% | 5.00 | X | X | O | PF_lower=5.00 ≥ 1.5, exp=+20.9% ≥ 3%, n=7≥6, holdout=[A_new=NA B=X C=O], gate=any holdout PASS |
| 7769 | donchian_breakout | +17.0% | 19.93 | 6 | -14.1% | 2.62 | X | X | X | PF_lower=2.62 ≥ 1.5, exp=+17.0% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥2.0 自動晉升 |
| 8069 | trend_pullback | +17.0% | 13.38 | 6 | -14.7% | 1.61 | X | O | X | PF_lower=1.61 ≥ 1.5, exp=+17.0% ≥ 3%, n=6≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 3035 | mean_reversion | +14.8% | 5.70 | 9 | -16.7% | 1.94 | X | X | O | PF_lower=1.94 ≥ 1.5, exp=+14.8% ≥ 3%, n=9≥6, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |
| 3533 | gap_continuation | +12.7% | 8.13 | 10 | -23.3% | 1.97 | X | X | O | PF_lower=1.97 ≥ 1.5, exp=+12.7% ≥ 3%, n=10≥6, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |
| 5536 | mean_reversion | +8.4% | 54.26 | 6 | -30.3% | 5.00 | X | O | X | PF_lower=5.00 ≥ 1.5, exp=+8.4% ≥ 3%, n=6≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 5274 | trend_pullback | +7.4% | 6.45 | 13 | -23.5% | 1.87 | X | O | O | PF_lower=1.87 ≥ 1.5, exp=+7.4% ≥ 3%, n=13≥6, holdout=[A_new=NA B=O C=O], gate=any holdout PASS |
| 1560 | mean_reversion | +5.2% | 10.97 | 6 | -10.5% | 2.15 | X | X | O | PF_lower=2.15 ≥ 1.5, exp=+5.2% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |

### Tier B — 部位上限 30% （共 16 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2383 | gap_continuation | +48.1% | 8.42 | 7 | -54.0% | 1.09 | X | X | X | PF_lower=1.09 ≥ 1.0, exp=+48.1% ≥ 2%, n=7≥5, holdout=[A_new=NA B=X C=NA] |
| 8046 | trend_pullback | +40.8% | inf | 5 | -23.8% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.0, exp=+40.8% ≥ 2%, n=5≥5, holdout=[A_new=NA B=X C=NA] |
| 3017 | chip_momentum | +35.1% | 48.93 | 5 | -19.6% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.0, exp=+35.1% ≥ 2%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 6510 | gap_continuation | +23.8% | 20.47 | 5 | -23.4% | 1.68 | X | X | X | PF_lower=1.68 ≥ 1.0, exp=+23.8% ≥ 2%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 006208 | gap_continuation | +17.1% | 12.33 | 6 | -14.0% | 1.32 | X | O | X | PF_lower=1.32 ≥ 1.0, exp=+17.1% ≥ 2%, n=6≥5, holdout=[A_new=NA B=O C=X] |
| 3036 | chip_momentum | +10.8% | 6.52 | 12 | -100.0% | 1.74 | X | X | X | PF_lower=1.74 ≥ 1.0, exp=+10.8% ≥ 2%, n=12≥5, holdout=[A_new=NA B=NA C=X] |
| 1605 | mean_reversion | +10.4% | 5.83 | 8 | -31.6% | 1.21 | X | O | O | PF_lower=1.21 ≥ 1.0, exp=+10.4% ≥ 2%, n=8≥5, holdout=[A_new=NA B=O C=O] |
| 2882 | gap_continuation | +9.7% | 8.63 | 8 | -15.4% | 1.54 | X | X | X | PF_lower=1.54 ≥ 1.0, exp=+9.7% ≥ 2%, n=8≥5, holdout=[A_new=NA B=X C=X] |
| 2812 | bollinger_squeeze | +9.4% | 16.31 | 5 | -17.3% | 1.63 | X | X | X | PF_lower=1.63 ≥ 1.0, exp=+9.4% ≥ 2%, n=5≥5, holdout=[A_new=NA B=NA C=NA] |
| 2455 | low_vol_pullback | +6.9% | inf | 5 | -9.9% | 5.00 | X | O | X | PF_lower=5.00 ≥ 1.0, exp=+6.9% ≥ 2%, n=5≥5, holdout=[A_new=NA B=O C=NA] |
| 2308 | mean_reversion | +6.2% | 6.86 | 6 | -13.6% | 1.10 | X | X | X | PF_lower=1.10 ≥ 1.0, exp=+6.2% ≥ 2%, n=6≥5, holdout=[A_new=NA B=X C=X] |
| 2324 | chip_momentum | +6.0% | 7.83 | 8 | -6.5% | 1.85 | X | X | X | PF_lower=1.85 ≥ 1.0, exp=+6.0% ≥ 2%, n=8≥5, holdout=[A_new=NA B=NA C=NA] |
| 3081 | gap_continuation | +4.7% | 2.47 | 23 | -28.2% | 1.03 | X | O | X | PF_lower=1.03 ≥ 1.0, exp=+4.7% ≥ 2%, n=23≥5, holdout=[A_new=NA B=O C=NA] |
| 4938 | chip_momentum | +4.5% | 5.87 | 7 | -14.1% | 1.05 | X | X | X | PF_lower=1.05 ≥ 1.0, exp=+4.5% ≥ 2%, n=7≥5, holdout=[A_new=NA B=NA C=X] |
| 6443 | chip_streak | +2.6% | 31.89 | 7 | -4.6% | 4.26 | X | O | O | PF_lower=4.26 ≥ 1.0, exp=+2.6% ≥ 2%, n=7≥5, holdout=[A_new=NA B=O C=O] |
| 1326 | mean_reversion | +2.5% | 7.07 | 12 | -5.8% | 1.51 | X | X | X | PF_lower=1.51 ≥ 1.0, exp=+2.5% ≥ 2%, n=12≥5, holdout=[A_new=NA B=X C=NA] |

### Tier C — 部位上限 15% （共 32 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2337 | mean_reversion | +45.4% | 49.59 | 3 | -22.5% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=49.59 ≥ 3.0, exp=+45.4% ≥ 5%, |DD|=23% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 1303 | gap_continuation | +28.4% | 24.48 | 5 | -21.9% | 0.41 | X | O | X | C_HIGH_Q_RESCUE：n=5, raw_PF=24.48 ≥ 3.0, exp=+28.4% ≥ 5%, |DD|=22% ≤ 25%, holdout=[A_new=NA B=O C=NA]（小樣本高品質訊號，紙上交易 3 個月） |
| 2426 | gap_continuation | +27.3% | 11.59 | 3 | -23.7% | N/A | X | O | X | LOW_N_RESCUE：n=3, raw_PF=11.59 ≥ 3.0, exp=+27.3% ≥ 5%, |DD|=24% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 2382 | gap_continuation | +18.9% | 3.01 | 8 | -24.6% | 0.73 | X | X | X | PF_lower=0.73 ≥ 0.7, exp=+18.9% ≥ 1%, n=8≥5, holdout=[A_new=NA B=NA C=NA] |
| 2376 | bollinger_squeeze | +18.7% | inf | 4 | -19.3% | N/A | X | X | X | LOW_N_RESCUE：n=4, raw_PF=inf ≥ 3.0, exp=+18.7% ≥ 5%, |DD|=19% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2881 | chip_momentum | +18.2% | inf | 4 | -14.4% | N/A | X | X | X | LOW_N_RESCUE：n=4, raw_PF=inf ≥ 3.0, exp=+18.2% ≥ 5%, |DD|=14% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2603 | gap_continuation | +15.9% | 2.32 | 15 | -60.8% | 0.92 | X | X | X | PF_lower=0.92 ≥ 0.7, exp=+15.9% ≥ 1%, n=15≥5, holdout=[A_new=NA B=X C=X] |
| 2002 | trend_pullback | +15.6% | 6.81 | 3 | -5.8% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=6.81 ≥ 3.0, exp=+15.6% ≥ 5%, |DD|=6% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 6446 | donchian_breakout | +13.5% | 5.22 | 8 | -20.7% | 0.47 | X | O | O | C_HIGH_Q_RESCUE：n=8, raw_PF=5.22 ≥ 3.0, exp=+13.5% ≥ 5%, |DD|=21% ≤ 25%, holdout=[A_new=NA B=O C=O]（小樣本高品質訊號，紙上交易 3 個月） |
| 6116 | mean_reversion | +13.3% | 7.28 | 3 | -12.1% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=7.28 ≥ 3.0, exp=+13.3% ≥ 5%, |DD|=12% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2330 | gap_continuation | +13.0% | 5.53 | 8 | -27.4% | 0.72 | X | X | X | PF_lower=0.72 ≥ 0.7, exp=+13.0% ≥ 1%, n=8≥5, holdout=[A_new=NA B=X C=X] |
| 2722 | donchian_breakout | +13.0% | 5.16 | 3 | -14.8% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=5.16 ≥ 3.0, exp=+13.0% ≥ 5%, |DD|=15% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 5871 | low_vol_pullback | +11.8% | 3.01 | 3 | -12.0% | N/A | X | O | X | LOW_N_RESCUE：n=3, raw_PF=3.01 ≥ 3.0, exp=+11.8% ≥ 5%, |DD|=12% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 2886 | donchian_breakout | +11.8% | inf | 4 | -20.3% | N/A | X | O | X | LOW_N_RESCUE：n=4, raw_PF=inf ≥ 3.0, exp=+11.8% ≥ 5%, |DD|=20% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 3227 | mean_reversion | +11.7% | 6.29 | 5 | -15.4% | 0.91 | X | X | X | PF_lower=0.91 ≥ 0.7, exp=+11.7% ≥ 1%, n=5≥5, holdout=[A_new=NA B=X C=NA] |
| 2371 | bollinger_squeeze | +10.7% | inf | 3 | -24.9% | N/A | X | O | X | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+10.7% ≥ 5%, |DD|=25% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |
| 4904 | donchian_breakout | +8.5% | 3.61 | 5 | -21.9% | 0.30 | X | X | X | C_HIGH_Q_RESCUE：n=5, raw_PF=3.61 ≥ 3.0, exp=+8.5% ≥ 5%, |DD|=22% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（小樣本高品質訊號，紙上交易 3 個月） |
| 8081 | chip_momentum | +7.9% | 5.01 | 8 | -22.9% | 0.59 | X | X | X | C_HIGH_Q_RESCUE：n=8, raw_PF=5.01 ≥ 3.0, exp=+7.9% ≥ 5%, |DD|=23% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（小樣本高品質訊號，紙上交易 3 個月） |
| 2352 | donchian_breakout | +7.7% | 4.45 | 3 | -16.5% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=4.45 ≥ 3.0, exp=+7.7% ≥ 5%, |DD|=17% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 3443 | gap_continuation | +6.4% | 3.91 | 14 | -22.1% | 0.83 | X | O | O | PF_lower=0.83 ≥ 0.7, exp=+6.4% ≥ 1%, n=14≥5, holdout=[A_new=NA B=O C=O] |
| 3037 | mean_reversion | +5.9% | 3.20 | 4 | -24.8% | N/A | X | X | O | LOW_N_RESCUE：n=4, raw_PF=3.20 ≥ 3.0, exp=+5.9% ≥ 5%, |DD|=25% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |
| 2369 | trend_pullback | +5.6% | 3.57 | 3 | -23.0% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=3.57 ≥ 3.0, exp=+5.6% ≥ 5%, |DD|=23% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2890 | bollinger_squeeze | +5.4% | 12.81 | 3 | -7.7% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=12.81 ≥ 3.0, exp=+5.4% ≥ 5%, |DD|=8% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 1535 | donchian_breakout | +5.3% | 12.64 | 4 | -24.2% | N/A | X | O | O | LOW_N_RESCUE：n=4, raw_PF=12.64 ≥ 3.0, exp=+5.3% ≥ 5%, |DD|=24% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 0056 | momentum_hold | +5.3% | 4.23 | 5 | -21.1% | 0.00 | X | X | X | C_HIGH_Q_RESCUE：n=5, raw_PF=4.23 ≥ 3.0, exp=+5.3% ≥ 5%, |DD|=21% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（小樣本高品質訊號，紙上交易 3 個月） |
| 2360 | trend_pullback | +5.2% | inf | 4 | -4.2% | N/A | X | X | O | LOW_N_RESCUE：n=4, raw_PF=inf ≥ 3.0, exp=+5.2% ≥ 5%, |DD|=4% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |
| 3702 | low_vol_pullback | +5.2% | 8.51 | 3 | -2.8% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=8.51 ≥ 3.0, exp=+5.2% ≥ 5%, |DD|=3% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 6515 | donchian_breakout | +3.3% | 2.29 | 30 | -36.0% | 0.77 | X | X | O | PF_lower=0.77 ≥ 0.7, exp=+3.3% ≥ 1%, n=30≥5, holdout=[A_new=NA B=NA C=O] |
| 3711 | mean_reversion | +3.1% | 2.03 | 20 | -27.3% | 0.92 | X | X | X | PF_lower=0.92 ≥ 0.7, exp=+3.1% ≥ 1%, n=20≥5, holdout=[A_new=NA B=NA C=NA] |
| 1802 | low_vol_pullback | +2.3% | 2.19 | 23 | -25.5% | 0.77 | X | X | X | PF_lower=0.77 ≥ 0.7, exp=+2.3% ≥ 1%, n=23≥5, holdout=[A_new=NA B=X C=X] |
| 1301 | mean_reversion | +1.5% | 4.64 | 13 | -9.9% | 1.27 | X | X | X | PF_lower=1.27 ≥ 0.7, exp=+1.5% ≥ 1%, n=13≥5, holdout=[A_new=NA B=X C=NA] |
| 2353 | low_vol_pullback | +1.4% | 29.91 | 5 | -7.6% | 2.81 | X | O | X | PF_lower=2.81 ≥ 0.7, exp=+1.4% ≥ 1%, n=5≥5, holdout=[A_new=NA B=O C=NA] |

### Tier F — 部位上限 0% （共 119 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3324 | donchian_breakout | +129.7% | 46.13 | 2 | -38.5% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2408 | chip_momentum | +93.5% | inf | 1 | -39.2% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 8454 | chip_momentum | +78.0% | 2.87 | 2 | -44.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2367 | momentum_hold | +51.1% | inf | 2 | -14.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9941 | trend_pullback | +41.8% | inf | 1 | -8.2% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2344 | chip_momentum | +37.7% | 3.52 | 6 | -51.3% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+37.7%, n=6, holdout=[A_new=NA B=NA C=X] |
| 1789 | gap_continuation | +37.3% | inf | 1 | -0.4% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3661 | bollinger_squeeze | +33.7% | 5.39 | 7 | -52.4% | 0.03 | X | O | X | FAIL：PF_lower=0.03, exp=+33.7%, n=7, holdout=[A_new=NA B=O C=X] |
| 3454 | momentum_hold | +33.6% | 6.05 | 4 | -28.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6271 | trend_pullback | +31.7% | inf | 1 | -23.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4961 | trend_pullback | +30.3% | 3.60 | 2 | -17.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2609 | momentum_hold | +30.0% | 2.69 | 6 | -43.9% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+30.0%, n=6, holdout=[A_new=NA B=NA C=X] |
| 8016 | trend_pullback | +29.5% | 5.34 | 2 | -34.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6531 | momentum_hold | +28.8% | inf | 3 | -42.7% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2887 | gap_continuation | +28.3% | inf | 2 | -8.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3014 | trend_pullback | +23.4% | 10.00 | 4 | -26.1% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2891 | trend_pullback | +21.6% | inf | 2 | -9.7% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6533 | momentum_hold | +20.4% | inf | 2 | -12.7% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6182 | mean_reversion | +15.4% | 4.49 | 3 | -29.9% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2379 | chip_momentum | +13.4% | 37.95 | 3 | -36.3% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2727 | chip_momentum | +13.2% | 2.78 | 8 | -25.7% | 0.15 | X | X | X | FAIL：PF_lower=0.15, exp=+13.2%, n=8, holdout=[A_new=NA B=NA C=NA] |
| 2458 | gap_continuation | +12.3% | inf | 1 | -17.3% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6213 | trend_pullback | +12.0% | 4.46 | 2 | -21.5% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2615 | chip_momentum | +10.7% | 1.03 | 17 | -77.8% | 0.03 | X | X | X | FAIL：PF_lower=0.03, exp=+10.7%, n=17, holdout=[A_new=NA B=NA C=X] |
| 2883 | donchian_breakout | +10.7% | 2.43 | 6 | -29.8% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+10.7%, n=6, holdout=[A_new=NA B=NA C=X] |
| 2855 | trend_pullback | +9.8% | 4.65 | 4 | -11.1% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1216 | donchian_breakout | +9.5% | inf | 2 | -11.0% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3044 | bollinger_squeeze | +9.4% | 1.61 | 6 | -41.2% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+9.4%, n=6, holdout=[A_new=NA B=NA C=X] |
| 2014 | gap_continuation | +9.4% | 1.75 | 7 | -27.9% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+9.4%, n=7, holdout=[A_new=NA B=NA C=X] |
| 6191 | gap_continuation | +9.1% | 1.38 | 9 | -42.6% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+9.1%, n=9, holdout=[A_new=NA B=O C=X] |
| 3034 | donchian_breakout | +9.1% | 2.07 | 4 | -25.8% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5269 | gap_continuation | +9.1% | 5.53 | 2 | -23.0% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2027 | momentum_hold | +8.8% | 1.67 | 4 | -43.2% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3526 | bollinger_squeeze | +8.6% | 2.29 | 6 | -33.0% | 0.16 | X | X | X | FAIL：PF_lower=0.16, exp=+8.6%, n=6, holdout=[A_new=NA B=NA C=X] |
| 2823 | low_vol_pullback | +8.5% | inf | 1 | -4.9% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2451 | momentum_hold | +8.1% | 2.53 | 12 | -36.9% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+8.1%, n=12, holdout=[A_new=NA B=NA C=NA] |
| 6188 | donchian_breakout | +8.1% | 1.32 | 6 | -49.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+8.1%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 2327 | chip_momentum | +7.8% | inf | 1 | -16.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1582 | momentum_hold | +7.7% | 4.08 | 4 | -26.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2723 | low_vol_pullback | +7.6% | 1.87 | 2 | -11.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1503 | momentum_hold | +7.1% | 2.48 | 22 | -31.5% | 0.34 | X | X | X | FAIL：PF_lower=0.34, exp=+7.1%, n=22, holdout=[A_new=NA B=NA C=X] |
| 3481 | donchian_breakout | +6.8% | 2.81 | 5 | -15.2% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+6.8%, n=5, holdout=[A_new=NA B=O C=NA] |
| 2393 | donchian_breakout | +6.5% | 2.02 | 6 | -31.1% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+6.5%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 3105 | gap_continuation | +6.1% | 4.72 | 11 | -22.6% | 0.21 | X | O | X | FAIL：PF_lower=0.21, exp=+6.1%, n=11, holdout=[A_new=NA B=O C=NA] |
| 2392 | momentum_hold | +5.9% | 1.70 | 2 | -20.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2884 | donchian_breakout | +5.9% | 3.33 | 5 | -30.8% | 0.34 | X | X | X | FAIL：PF_lower=0.34, exp=+5.9%, n=5, holdout=[A_new=NA B=NA C=X] |
| 4137 | chip_streak | +5.8% | inf | 2 | -7.6% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2606 | mean_reversion | +5.7% | 1.43 | 8 | -37.0% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+5.7%, n=8, holdout=[A_new=NA B=NA C=X] |
| 2492 | mean_reversion | +5.3% | inf | 1 | -6.9% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4147 | donchian_breakout | +5.2% | 1.83 | 2 | -18.8% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6770 | bollinger_squeeze | +4.8% | 2.19 | 18 | -50.7% | 0.02 | X | X | X | FAIL：PF_lower=0.02, exp=+4.8%, n=18, holdout=[A_new=NA B=NA C=X] |
| 3406 | trend_pullback | +4.7% | 2.76 | 7 | -18.4% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+4.7%, n=7, holdout=[A_new=NA B=X C=NA] |
| 2542 | gap_continuation | +4.4% | 2.31 | 4 | -25.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1234 | chip_momentum | +4.3% | 6.85 | 3 | -9.9% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2454 | monthly_revenue_event | +4.2% | 4.68 | 9 | -12.1% | 0.36 | X | X | X | FAIL：PF_lower=0.36, exp=+4.2%, n=9, holdout=[A_new=NA B=NA C=NA] |
| 2867 | mean_reversion | +3.9% | 3.07 | 5 | -10.8% | 0.11 | X | X | X | FAIL：PF_lower=0.11, exp=+3.9%, n=5, holdout=[A_new=NA B=X C=NA] |
| 2303 | low_vol_pullback | +3.4% | 2.07 | 5 | -13.7% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+3.4%, n=5, holdout=[A_new=NA B=NA C=NA] |
| 6781 | chip_momentum | +3.3% | 1.30 | 19 | -44.7% | 0.31 | X | X | X | FAIL：PF_lower=0.31, exp=+3.3%, n=19, holdout=[A_new=NA B=NA C=X] |
| 9914 | low_vol_pullback | +3.2% | 5.22 | 2 | -1.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2409 | chip_momentum | +3.2% | 1.78 | 11 | -27.7% | 0.31 | X | X | X | FAIL：PF_lower=0.31, exp=+3.2%, n=11, holdout=[A_new=NA B=NA C=X] |
| 6285 | gap_continuation | +3.1% | 2.69 | 3 | -26.7% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9933 | mean_reversion | +3.0% | 10.10 | 4 | -5.8% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6491 | gap_continuation | +2.9% | 0.96 | 20 | -68.7% | 0.05 | X | X | X | FAIL：PF_lower=0.05, exp=+2.9%, n=20, holdout=[A_new=NA B=X C=X] |
| 6505 | low_vol_pullback | +2.9% | 1.78 | 4 | -12.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1402 | gap_continuation | +2.8% | 2.44 | 7 | -11.3% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+2.8%, n=7, holdout=[A_new=NA B=O C=X] |
| 2888 | low_vol_pullback | +2.7% | 2.46 | 4 | -11.2% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4148 | momentum_hold | +2.5% | 1.60 | 4 | -12.4% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1717 | gap_continuation | +2.5% | 1.62 | 13 | -23.9% | 0.23 | X | X | X | FAIL：PF_lower=0.23, exp=+2.5%, n=13, holdout=[A_new=NA B=NA C=X] |
| 4915 | mean_reversion | +2.5% | 14.70 | 4 | -4.9% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2356 | mean_reversion | +2.5% | 3.23 | 5 | -17.4% | 0.43 | X | O | X | FAIL：PF_lower=0.43, exp=+2.5%, n=5, holdout=[A_new=NA B=O C=NA] |
| 9940 | low_vol_pullback | +2.5% | inf | 2 | -1.2% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2845 | momentum_hold | +2.4% | inf | 1 | -3.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2820 | bollinger_squeeze | +2.3% | 1.77 | 6 | -14.3% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+2.3%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 9907 | bollinger_squeeze | +2.3% | 1.54 | 7 | -21.0% | 0.18 | X | X | O | FAIL：PF_lower=0.18, exp=+2.3%, n=7, holdout=[A_new=NA B=NA C=O] |
| 2015 | donchian_breakout | +2.3% | 1.54 | 3 | -14.2% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1909 | low_vol_pullback | +2.3% | 1.66 | 5 | -11.5% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+2.3%, n=5, holdout=[A_new=NA B=NA C=NA] |
| 2049 | trend_pullback | +2.3% | 1.86 | 3 | -14.4% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 00965 | bollinger_squeeze | +2.1% | 2.68 | 6 | -12.5% | 0.22 | X | X | X | FAIL：PF_lower=0.22, exp=+2.1%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 3045 | momentum_hold | +2.1% | inf | 1 | -10.3% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3008 | gap_continuation | +2.1% | 1.28 | 2 | -23.8% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2328 | trend_pullback | +2.0% | 1.56 | 4 | -18.6% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2618 | gap_continuation | +2.0% | 1.60 | 5 | -18.8% | 0.00 | X | X | O | FAIL：PF_lower=0.00, exp=+2.0%, n=5, holdout=[A_new=NA B=NA C=O] |
| 2354 | bollinger_squeeze | +1.9% | 2.03 | 2 | -4.8% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1809 | momentum_hold | +1.7% | 1.03 | 4 | -30.6% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1314 | bollinger_squeeze | +1.6% | 1.36 | 3 | -30.6% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1907 | bollinger_squeeze | +1.6% | 3.22 | 3 | -6.2% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5347 | mean_reversion | +1.5% | 1.41 | 4 | -16.5% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5880 | chip_momentum | +1.4% | 1.33 | 6 | -21.4% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.4%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 1722 | low_vol_pullback | +1.3% | 1.41 | 10 | -21.7% | 0.26 | X | O | O | FAIL：PF_lower=0.26, exp=+1.3%, n=10, holdout=[A_new=NA B=O C=O] |
| 1456 | low_vol_pullback | +1.2% | 1.38 | 3 | -8.6% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9904 | mean_reversion | +1.2% | 1.38 | 5 | -11.5% | 0.08 | X | X | X | FAIL：PF_lower=0.08, exp=+1.2%, n=5, holdout=[A_new=NA B=NA C=NA] |
| 5904 | donchian_breakout | +1.0% | 1.01 | 2 | -21.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6488 | volume_breakout | +0.9% | 1.23 | 33 | -28.6% | 0.44 | X | O | O | FAIL：PF_lower=0.44, exp=+0.9%, n=33, holdout=[A_new=NA B=O C=O] |
| 2892 | bollinger_squeeze | +0.9% | 1.26 | 5 | -21.5% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+0.9%, n=5, holdout=[A_new=NA B=X C=NA] |
| 2347 | trend_pullback | +0.7% | 1.27 | 3 | -10.2% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5483 | low_vol_pullback | +0.7% | 14.98 | 3 | -3.0% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6121 | low_vol_pullback | +0.7% | 1.46 | 4 | -8.2% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9921 | mean_reversion | +0.6% | 1.37 | 6 | -11.1% | 0.12 | X | X | X | FAIL：PF_lower=0.12, exp=+0.6%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 1101 | gap_continuation | +0.5% | 1.10 | 10 | -24.2% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+0.5%, n=10, holdout=[A_new=NA B=O C=X] |
| 5388 | low_vol_pullback | +0.5% | 1.14 | 3 | -7.5% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5522 | donchian_breakout | +0.3% | 0.94 | 9 | -31.8% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+0.3%, n=9, holdout=[A_new=NA B=NA C=X] |
| 2474 | gap_continuation | +0.3% | 4.93 | 2 | -5.6% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3323 | bollinger_squeeze | +0.2% | 1.05 | 2 | -23.1% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 00878 | bollinger_squeeze | +0.2% | 1.14 | 27 | -15.4% | 0.39 | X | X | O | FAIL：PF_lower=0.39, exp=+0.2%, n=27, holdout=[A_new=NA B=NA C=O] |
| 6804 | momentum_hold | +0.1% | 0.94 | 33 | -100.0% | 0.15 | X | X | O | FAIL：PF_lower=0.15, exp=+0.1%, n=33, holdout=[A_new=NA B=NA C=O] |
| 4174 | bollinger_squeeze | +0.1% | 0.99 | 2 | -11.4% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2912 | volume_breakout | +0.1% | 1.11 | 3 | -4.4% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2207 | chip_streak | +0.1% | 0.96 | 15 | -29.5% | 0.11 | X | X | O | FAIL：PF_lower=0.11, exp=+0.1%, n=15, holdout=[A_new=NA B=NA C=O] |
| 1102 | chip_streak | +0.0% | 1.00 | 6 | -6.0% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+0.0%, n=6, holdout=[A_new=NA B=O C=X] |
| 1565 | donchian_breakout | -0.3% | 0.82 | 5 | -25.6% | 0.00 | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 1227 | monthly_revenue_event | -0.7% | 0.00 | 2 | -3.3% | N/A | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2227 | volume_breakout | -0.8% | 0.63 | 3 | -8.6% | N/A | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2412 | chip_streak | -0.9% | 0.18 | 22 | -22.2% | 0.04 | X | O | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 6526 | gap_continuation | -1.0% | 0.72 | 29 | -52.6% | 0.17 | X | X | O | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2105 | donchian_breakout | -1.1% | 0.62 | 15 | -34.4% | 0.09 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 5876 | mean_reversion | -1.1% | 0.46 | 8 | -17.2% | 0.07 | X | O | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 00940 | volume_breakout | -1.4% | 0.20 | 12 | -20.7% | 0.00 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 1521 | momentum_hold | -1.8% | 0.00 | 1 | -1.8% | N/A | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 8341 | low_vol_pullback | -2.4% | 0.00 | 2 | -7.5% | N/A | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
