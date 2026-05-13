# TIERING REPORT — 20260513_225738

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 41 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 43**  （目標 ≥ 20）

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
| 1717 | support_bounce | +4.4% | 2.45 | 15 | -20.0% | 0.93 | X | X | O | PF_lower=0.93 ≥ 0.7, exp=+4.4% ≥ 1%, n=15≥5, holdout=[A_new=NA B=X C=O] |

### Tier F — 部位上限 0% （共 41 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2886 | support_bounce | +2.1% | 1.71 | 4 | -10.3% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3481 | support_bounce | +1.6% | 1.23 | 2 | -12.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9933 | support_bounce | +1.5% | 1.64 | 11 | -18.2% | 0.38 | X | O | X | FAIL：PF_lower=0.38, exp=+1.5%, n=11, holdout=[A_new=NA B=O C=NA] |
| 2609 | support_bounce | +1.4% | 1.10 | 8 | -24.7% | 0.28 | X | X | X | FAIL：PF_lower=0.28, exp=+1.4%, n=8, holdout=[A_new=NA B=NA C=X] |
| 0056 | support_bounce | +1.2% | 1.40 | 7 | -21.1% | 0.20 | X | O | X | FAIL：PF_lower=0.20, exp=+1.2%, n=7, holdout=[A_new=NA B=O C=X] |
| 2009 | support_bounce | +1.1% | 1.23 | 5 | -15.8% | 0.19 | X | O | X | FAIL：PF_lower=0.19, exp=+1.1%, n=5, holdout=[A_new=NA B=O C=X] |
| 2912 | support_bounce | +0.5% | 1.06 | 11 | -30.7% | 0.16 | X | X | O | FAIL：PF_lower=0.16, exp=+0.5%, n=11, holdout=[A_new=NA B=NA C=O] |
| 2049 | support_bounce | +0.2% | 0.99 | 9 | -14.1% | 0.18 | X | X | X | FAIL：PF_lower=0.18, exp=+0.2%, n=9, holdout=[A_new=NA B=X C=NA] |
| 3045 | support_bounce | +0.1% | 1.11 | 12 | -13.7% | 0.27 | X | O | X | FAIL：PF_lower=0.27, exp=+0.1%, n=12, holdout=[A_new=NA B=O C=X] |
| 2105 | support_bounce | -0.3% | 0.86 | 4 | -17.4% | N/A | X | O | O | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 1234 | support_bounce | -0.4% | 0.00 | 1 | -4.9% | N/A | X | O | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 5388 | support_bounce | -0.5% | 0.80 | 11 | -30.3% | 0.20 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 1227 | support_bounce | -0.6% | 0.70 | 17 | -21.6% | 0.16 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2887 | support_bounce | -0.6% | 0.71 | 10 | -23.4% | 0.20 | X | O | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2227 | support_bounce | -0.7% | 0.72 | 15 | -25.9% | 0.24 | X | O | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 5876 | support_bounce | -0.8% | 0.59 | 15 | -22.3% | 0.15 | X | O | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 1521 | support_bounce | -0.8% | 0.68 | 12 | -34.4% | 0.18 | X | O | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 1582 | support_bounce | -0.9% | 0.40 | 10 | -12.5% | 0.06 | X | O | O | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 1907 | support_bounce | -1.2% | 0.68 | 4 | -14.3% | N/A | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 4147 | support_bounce | -1.4% | 0.59 | 10 | -23.9% | 0.00 | X | X | O | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2002 | support_bounce | -1.4% | 0.60 | 8 | -16.7% | 0.00 | X | O | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 1101 | support_bounce | -1.7% | 0.50 | 12 | -33.1% | 0.00 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 5880 | support_bounce | -1.8% | 0.41 | 10 | -18.0% | 0.09 | X | O | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2458 | support_bounce | -2.0% | 0.55 | 5 | -17.0% | 0.00 | X | O | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 9940 | support_bounce | -2.4% | 0.33 | 18 | -42.6% | 0.00 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 9907 | support_bounce | -2.4% | 0.34 | 4 | -16.9% | N/A | X | O | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 2014 | support_bounce | -2.7% | 0.48 | 3 | -18.1% | N/A | X | O | X | FAIL：test expectancy=-2.7% < 0（負期望值） |
| 2867 | support_bounce | -2.7% | 0.35 | 8 | -23.2% | 0.00 | X | X | X | FAIL：test expectancy=-2.7% < 0（負期望值） |
| 5269 | support_bounce | -2.7% | 0.60 | 5 | -29.7% | 0.10 | X | O | O | FAIL：test expectancy=-2.7% < 0（負期望值） |
| 4961 | support_bounce | -3.0% | 0.27 | 6 | -24.4% | 0.00 | X | O | X | FAIL：test expectancy=-3.0% < 0（負期望值） |
| 8069 | support_bounce | -3.1% | 0.41 | 2 | -11.2% | N/A | X | X | X | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 8454 | support_bounce | -3.4% | 0.31 | 12 | -36.2% | 0.06 | X | O | X | FAIL：test expectancy=-3.4% < 0（負期望值） |
| 2723 | support_bounce | -3.5% | 0.30 | 7 | -30.8% | 0.00 | X | X | X | FAIL：test expectancy=-3.5% < 0（負期望值） |
| 6285 | support_bounce | -6.0% | 0.00 | 4 | -26.7% | N/A | X | X | X | FAIL：test expectancy=-6.0% < 0（負期望值） |
| 6121 | support_bounce | -6.2% | 0.00 | 1 | -6.2% | N/A | X | X | X | FAIL：test expectancy=-6.2% < 0（負期望值） |
| 9921 | support_bounce | -6.9% | 0.21 | 7 | -45.5% | 0.00 | X | O | X | FAIL：test expectancy=-6.9% < 0（負期望值） |
| 1503 | support_bounce | -8.4% | 0.00 | 1 | -11.5% | N/A | X | O | X | FAIL：test expectancy=-8.4% < 0（負期望值） |
| 1504 | support_bounce | -11.5% | 0.15 | 10 | -100.0% | 0.00 | X | X | O | FAIL：test expectancy=-11.5% < 0（負期望值） |
| 2371 | support_bounce | -13.7% | 0.00 | 3 | -38.2% | N/A | X | O | X | FAIL：test expectancy=-13.7% < 0（負期望值） |
| 2606 | support_bounce | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2823 | support_bounce | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
