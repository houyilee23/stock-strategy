# TIERING REPORT — 20260509_203247

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 4 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 34 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 4 / 38**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 4 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1102 | support_bounce | +7.3% | 14.71 | 4 | -7.3% | N/A | X | X | X | LOW_N_RESCUE：n=4, raw_PF=14.71 ≥ 3.0, exp=+7.3% ≥ 5%, |DD|=7% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |
| 2892 | support_bounce | +7.2% | inf | 4 | -6.1% | N/A | X | O | O | LOW_N_RESCUE：n=4, raw_PF=inf ≥ 3.0, exp=+7.2% ≥ 5%, |DD|=6% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 6488 | support_bounce | +4.7% | 2.13 | 11 | -20.8% | 0.77 | X | O | X | PF_lower=0.77 ≥ 0.7, exp=+4.7% ≥ 1%, n=11≥5, holdout=[A_new=NA B=O C=X] |
| 2884 | support_bounce | +3.5% | 4.19 | 10 | -19.1% | 0.97 | X | X | X | PF_lower=0.97 ≥ 0.7, exp=+3.5% ≥ 1%, n=10≥5, holdout=[A_new=NA B=X C=X] |

### Tier F — 部位上限 0% （共 34 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3661 | support_bounce | +5.6% | inf | 1 | -16.4% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2615 | support_bounce | +3.8% | 1.63 | 5 | -26.2% | 0.26 | X | X | O | FAIL：PF_lower=0.26, exp=+3.8%, n=5, holdout=[A_new=NA B=NA C=O] |
| 4938 | support_bounce | +3.5% | 1.68 | 2 | -15.2% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2207 | support_bounce | +2.9% | 2.29 | 6 | -19.3% | 0.35 | X | X | X | FAIL：PF_lower=0.35, exp=+2.9%, n=6, holdout=[A_new=NA B=X C=NA] |
| 1605 | support_bounce | +2.8% | 1.51 | 10 | -24.7% | 0.44 | X | O | O | FAIL：PF_lower=0.44, exp=+2.8%, n=10, holdout=[A_new=NA B=O C=O] |
| 6669 | support_bounce | +2.5% | inf | 1 | -10.9% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2886 | support_bounce | +2.1% | 1.71 | 4 | -10.3% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2474 | support_bounce | +2.1% | 2.26 | 5 | -16.1% | 0.19 | X | X | X | FAIL：PF_lower=0.19, exp=+2.1%, n=5, holdout=[A_new=NA B=X C=NA] |
| 2885 | support_bounce | +1.4% | 1.85 | 8 | -25.9% | 0.19 | X | O | O | FAIL：PF_lower=0.19, exp=+1.4%, n=8, holdout=[A_new=NA B=O C=O] |
| 0056 | support_bounce | +1.2% | 1.40 | 7 | -21.1% | 0.20 | X | O | X | FAIL：PF_lower=0.20, exp=+1.2%, n=7, holdout=[A_new=NA B=O C=X] |
| 2324 | support_bounce | +0.8% | 0.95 | 3 | -24.5% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2412 | support_bounce | +0.7% | 1.26 | 7 | -15.4% | 0.23 | X | X | X | FAIL：PF_lower=0.23, exp=+0.7%, n=7, holdout=[A_new=NA B=NA C=X] |
| 2912 | support_bounce | +0.5% | 1.06 | 11 | -30.7% | 0.16 | X | X | O | FAIL：PF_lower=0.16, exp=+0.5%, n=11, holdout=[A_new=NA B=NA C=O] |
| 2379 | support_bounce | +0.3% | 0.97 | 5 | -14.8% | 0.15 | X | O | X | FAIL：PF_lower=0.15, exp=+0.3%, n=5, holdout=[A_new=NA B=O C=X] |
| 3045 | support_bounce | +0.1% | 1.11 | 12 | -13.7% | 0.27 | X | O | X | FAIL：PF_lower=0.27, exp=+0.1%, n=12, holdout=[A_new=NA B=O C=X] |
| 2426 | support_bounce | +0.1% | 1.00 | 8 | -12.1% | 0.19 | X | X | X | FAIL：PF_lower=0.19, exp=+0.1%, n=8, holdout=[A_new=NA B=NA C=X] |
| 2105 | support_bounce | -0.3% | 0.86 | 4 | -17.4% | N/A | X | O | O | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 1809 | support_bounce | -0.8% | 0.78 | 3 | -14.8% | N/A | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 5880 | support_bounce | -1.0% | 0.63 | 7 | -18.4% | 0.13 | X | O | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 1227 | support_bounce | -1.1% | 0.47 | 17 | -23.2% | 0.09 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 1216 | support_bounce | -1.1% | 0.51 | 4 | -15.6% | N/A | X | X | O | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2002 | support_bounce | -1.4% | 0.60 | 8 | -16.7% | 0.00 | X | O | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 9921 | support_bounce | -1.5% | 0.68 | 7 | -28.4% | 0.14 | X | X | O | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 00878 | support_bounce | -1.7% | 0.45 | 7 | -19.8% | 0.07 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 1101 | support_bounce | -1.9% | 0.40 | 11 | -24.8% | 0.00 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2881 | support_bounce | -2.0% | 0.51 | 5 | -32.6% | 0.00 | X | X | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 6505 | support_bounce | -2.2% | 0.38 | 9 | -23.6% | 0.00 | X | X | O | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 9940 | support_bounce | -2.4% | 0.31 | 14 | -32.0% | 0.03 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 00940 | support_bounce | -2.8% | 0.40 | 2 | -16.0% | N/A | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 2356 | support_bounce | -2.9% | 0.49 | 4 | -18.6% | N/A | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 5347 | support_bounce | -3.3% | 0.35 | 5 | -31.1% | 0.00 | X | X | X | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 2327 | support_bounce | -3.7% | 0.08 | 4 | -21.6% | N/A | X | X | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2618 | support_bounce | -6.0% | 0.00 | 1 | -6.6% | N/A | X | O | X | FAIL：test expectancy=-6.0% < 0（負期望值） |
| 2603 | support_bounce | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
