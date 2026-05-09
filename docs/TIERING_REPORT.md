# TIERING REPORT — 20260509_170602

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 41 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 41**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 41 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2892 | rsi_oversold_volume | +2.2% | 5.34 | 4 | -6.3% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1216 | rsi_oversold_volume | +1.3% | inf | 1 | -3.4% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2379 | rsi_oversold_volume | +1.2% | 1.65 | 8 | -8.8% | 0.00 | X | X | O | FAIL：PF_lower=0.00, exp=+1.2%, n=8, holdout=[A_new=NA B=X C=O] |
| 5880 | rsi_oversold_volume | +1.1% | 3.27 | 5 | -5.8% | 0.29 | X | O | X | FAIL：PF_lower=0.29, exp=+1.1%, n=5, holdout=[A_new=NA B=O C=NA] |
| 00878 | rsi_oversold_volume | +0.9% | 2.10 | 9 | -6.9% | 0.14 | X | X | X | FAIL：PF_lower=0.14, exp=+0.9%, n=9, holdout=[A_new=NA B=NA C=X] |
| 2886 | rsi_oversold_volume | +0.5% | 1.35 | 6 | -8.3% | 0.15 | X | X | X | FAIL：PF_lower=0.15, exp=+0.5%, n=6, holdout=[A_new=NA B=NA C=X] |
| 3231 | rsi_oversold_volume | +0.5% | 4.04 | 2 | -2.4% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2885 | rsi_oversold_volume | +0.5% | inf | 1 | -7.9% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2308 | rsi_oversold_volume | +0.4% | 1.22 | 6 | -16.3% | 0.02 | X | X | X | FAIL：PF_lower=0.02, exp=+0.4%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 2884 | rsi_oversold_volume | +0.3% | 1.10 | 22 | -21.9% | 0.27 | X | O | O | FAIL：PF_lower=0.27, exp=+0.3%, n=22, holdout=[A_new=NA B=O C=O] |
| 2412 | rsi_oversold_volume | +0.2% | 1.22 | 6 | -6.6% | 0.04 | X | O | X | FAIL：PF_lower=0.04, exp=+0.2%, n=6, holdout=[A_new=NA B=O C=X] |
| 2881 | rsi_oversold_volume | +0.2% | 1.56 | 3 | -8.9% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3661 | rsi_oversold_volume | +0.1% | 0.94 | 12 | -33.3% | 0.31 | X | X | O | FAIL：PF_lower=0.31, exp=+0.1%, n=12, holdout=[A_new=NA B=X C=O] |
| 3045 | rsi_oversold_volume | +0.1% | 1.12 | 4 | -8.8% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2912 | rsi_oversold_volume | -0.4% | 0.07 | 2 | -5.2% | N/A | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2356 | rsi_oversold_volume | -0.5% | 0.58 | 2 | -3.9% | N/A | X | O | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 9940 | rsi_oversold_volume | -0.5% | 0.50 | 4 | -3.5% | N/A | X | O | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 6669 | rsi_oversold_volume | -0.5% | 0.78 | 15 | -32.6% | 0.19 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 2327 | rsi_oversold_volume | -0.5% | 0.69 | 10 | -15.6% | 0.07 | X | O | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 4938 | rsi_oversold_volume | -0.6% | 0.41 | 4 | -3.8% | N/A | X | O | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 6488 | rsi_oversold_volume | -0.7% | 0.75 | 11 | -30.5% | 0.08 | X | O | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2207 | rsi_oversold_volume | -1.1% | 0.46 | 8 | -12.7% | 0.02 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 1605 | rsi_oversold_volume | -1.2% | 0.00 | 2 | -2.3% | N/A | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 1101 | rsi_oversold_volume | -1.2% | 0.37 | 23 | -32.6% | 0.00 | X | O | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 9921 | rsi_oversold_volume | -1.2% | 0.20 | 7 | -8.3% | 0.00 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2618 | rsi_oversold_volume | -1.4% | 0.00 | 1 | -4.0% | N/A | X | O | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2603 | rsi_oversold_volume | -1.5% | 0.28 | 2 | -12.4% | N/A | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 1227 | rsi_oversold_volume | -1.6% | 0.01 | 5 | -7.6% | 0.00 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 1809 | rsi_oversold_volume | -1.8% | 0.07 | 3 | -5.6% | N/A | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 9914 | rsi_oversold_volume | -1.8% | 0.00 | 4 | -7.8% | N/A | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 1102 | rsi_oversold_volume | -1.9% | 0.00 | 3 | -5.8% | N/A | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 6505 | rsi_oversold_volume | -2.1% | 0.00 | 2 | -4.2% | N/A | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2474 | rsi_oversold_volume | -2.2% | 0.01 | 2 | -4.5% | N/A | X | X | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 2002 | rsi_oversold_volume | -2.2% | 0.09 | 7 | -14.9% | 0.00 | X | X | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 5347 | rsi_oversold_volume | -2.9% | 0.00 | 4 | -11.5% | N/A | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2426 | rsi_oversold_volume | -2.9% | 0.00 | 4 | -11.3% | N/A | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 0056 | rsi_oversold_volume | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 00940 | rsi_oversold_volume | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2105 | rsi_oversold_volume | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2324 | rsi_oversold_volume | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2615 | rsi_oversold_volume | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
