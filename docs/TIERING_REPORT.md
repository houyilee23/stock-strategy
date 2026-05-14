# TIERING REPORT — 20260513_215726

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 2 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 8 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 18 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 10 / 29**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3653 | gap_continuation | +17.5% | 8.12 | 6 | -24.6% | 1.13 | X | X | O | PF_lower=1.13 ≥ 1.0, exp=+17.5% ≥ 2%, n=6≥5, holdout=[A_new=NA B=NA C=O] |
| 3702 | low_vol_pullback | +3.2% | 4.67 | 7 | -8.9% | 1.09 | X | X | X | PF_lower=1.09 ≥ 1.0, exp=+3.2% ≥ 2%, n=7≥5, holdout=[A_new=NA B=X C=NA] |

### Tier C — 部位上限 15% （共 8 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3044 | trend_pullback | +17.5% | inf | 3 | -12.1% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+17.5% ≥ 5%, |DD|=12% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 6491 | mean_reversion | +10.8% | inf | 3 | -9.9% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+10.8% ≥ 5%, |DD|=10% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 1789 | gap_continuation | +9.7% | 3.23 | 3 | -10.4% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=3.23 ≥ 3.0, exp=+9.7% ≥ 5%, |DD|=10% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 3454 | mean_reversion | +9.2% | 3.67 | 4 | -10.5% | N/A | X | O | O | LOW_N_RESCUE：n=4, raw_PF=3.67 ≥ 3.0, exp=+9.2% ≥ 5%, |DD|=10% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 6191 | chip_momentum | +7.6% | 3.45 | 19 | -33.4% | 0.97 | X | O | X | PF_lower=0.97 ≥ 0.7, exp=+7.6% ≥ 1%, n=19≥5, holdout=[A_new=NA B=O C=NA] |
| 3014 | chip_momentum | +6.7% | 2.51 | 9 | -25.1% | 0.77 | X | X | X | PF_lower=0.77 ≥ 0.7, exp=+6.7% ≥ 1%, n=9≥5, holdout=[A_new=NA B=NA C=NA] |
| 3036 | chip_momentum | +5.5% | 1.82 | 22 | -100.0% | 0.81 | X | X | X | PF_lower=0.81 ≥ 0.7, exp=+5.5% ≥ 1%, n=22≥5, holdout=[A_new=NA B=NA C=X] |
| 4763 | donchian_breakout | +4.4% | 3.59 | 13 | -16.7% | 0.81 | X | X | O | PF_lower=0.81 ≥ 0.7, exp=+4.4% ≥ 1%, n=13≥5, holdout=[A_new=NA B=X C=O] |

### Tier F — 部位上限 0% （共 18 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6446 | donchian_breakout | +20.1% | 2.14 | 10 | -44.7% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+20.1%, n=10, holdout=[A_new=NA B=X C=X] |
| 3105 | gap_continuation | +13.9% | 9.22 | 7 | -24.2% | 0.14 | X | O | X | FAIL：PF_lower=0.14, exp=+13.9%, n=7, holdout=[A_new=NA B=O C=NA] |
| 2820 | momentum_hold | +13.5% | inf | 1 | -6.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1314 | mean_reversion | +13.3% | inf | 2 | -5.5% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2451 | momentum_hold | +10.5% | 3.05 | 7 | -34.5% | 0.13 | X | X | X | FAIL：PF_lower=0.13, exp=+10.5%, n=7, holdout=[A_new=NA B=NA C=NA] |
| 2722 | gap_continuation | +9.5% | 1.70 | 5 | -18.0% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+9.5%, n=5, holdout=[A_new=NA B=NA C=NA] |
| 1535 | momentum_hold | +7.6% | 4.53 | 6 | -36.2% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+7.6%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 2015 | mean_reversion | +5.1% | 2.01 | 2 | -8.6% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4915 | momentum_hold | +4.4% | 3.02 | 3 | -21.8% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2845 | gap_continuation | +2.8% | inf | 1 | -3.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6781 | volume_breakout | +2.4% | 1.32 | 22 | -38.8% | 0.42 | X | X | X | FAIL：PF_lower=0.42, exp=+2.4%, n=22, holdout=[A_new=NA B=NA C=X] |
| 4137 | chip_streak | +2.0% | 2.92 | 4 | -8.2% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4174 | mean_reversion | +1.9% | inf | 1 | -7.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5483 | trend_pullback | +1.7% | 1.24 | 3 | -20.5% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2542 | trend_pullback | +1.3% | 2.66 | 6 | -9.5% | 0.33 | X | X | O | FAIL：PF_lower=0.33, exp=+1.3%, n=6, holdout=[A_new=NA B=NA C=O] |
| 2354 | trend_pullback | +0.9% | inf | 1 | -5.7% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3406 | mean_reversion | +0.7% | 1.00 | 2 | -11.2% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6533 | volume_breakout | +0.7% | 1.44 | 6 | -15.0% | 0.14 | X | O | O | FAIL：PF_lower=0.14, exp=+0.7%, n=6, holdout=[A_new=NA B=O C=O] |
