# TIERING REPORT — 20260512_020416

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 24 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 25**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 4938 | roc_reversal | +3.0% | 3.84 | 6 | -4.7% | 0.73 | X | O | O | PF_lower=0.73 ≥ 0.7, exp=+3.0% ≥ 1%, n=6≥5, holdout=[A_new=NA B=O C=O] |

### Tier F — 部位上限 0% （共 24 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1216 | roc_reversal | +4.3% | inf | 2 | -4.2% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2881 | roc_reversal | +1.8% | 1.27 | 2 | -16.9% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 0056 | roc_reversal | +1.1% | 1.46 | 6 | -11.6% | 0.01 | X | O | X | FAIL：PF_lower=0.01, exp=+1.1%, n=6, holdout=[A_new=NA B=O C=X] |
| 2603 | roc_reversal | +0.9% | 1.11 | 9 | -27.5% | 0.25 | X | X | X | FAIL：PF_lower=0.25, exp=+0.9%, n=9, holdout=[A_new=NA B=NA C=X] |
| 2412 | roc_reversal | -0.4% | 0.58 | 6 | -7.7% | 0.01 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2324 | roc_reversal | -0.8% | 0.65 | 4 | -11.5% | N/A | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2002 | roc_reversal | -0.8% | 0.71 | 17 | -30.6% | 0.20 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2426 | roc_reversal | -1.1% | 0.59 | 14 | -22.3% | 0.20 | X | O | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 9940 | roc_reversal | -2.0% | 0.00 | 1 | -7.3% | N/A | X | O | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 9921 | roc_reversal | -2.0% | 0.65 | 2 | -14.2% | N/A | X | X | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 2105 | roc_reversal | -2.5% | 0.46 | 11 | -27.1% | 0.09 | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 6669 | roc_reversal | -2.8% | 0.34 | 22 | -54.7% | 0.13 | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 2356 | roc_reversal | -2.9% | 0.53 | 6 | -27.6% | 0.07 | X | O | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2379 | roc_reversal | -3.7% | 0.25 | 2 | -10.8% | N/A | X | O | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 1101 | roc_reversal | -4.4% | 0.00 | 1 | -5.8% | N/A | X | O | X | FAIL：test expectancy=-4.4% < 0（負期望值） |
| 1605 | roc_reversal | -4.7% | 0.27 | 6 | -35.3% | 0.04 | X | O | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 2886 | roc_reversal | -4.9% | 0.00 | 4 | -18.4% | N/A | X | X | X | FAIL：test expectancy=-4.9% < 0（負期望值） |
| 6505 | roc_reversal | -5.3% | 0.00 | 3 | -17.2% | N/A | X | X | X | FAIL：test expectancy=-5.3% < 0（負期望值） |
| 1227 | roc_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2207 | roc_reversal | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2474 | roc_reversal | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2912 | roc_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3045 | roc_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5880 | roc_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
