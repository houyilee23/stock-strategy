# TIERING REPORT — 20260510_015130

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 33 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 34**  （目標 ≥ 20）

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
| 00940 | kd_oversold_cross | +1.8% | 12.52 | 6 | -7.7% | 1.70 | X | X | X | PF_lower=1.70 ≥ 0.7, exp=+1.8% ≥ 1%, n=6≥5, holdout=[A_new=NA B=NA C=NA] |

### Tier F — 部位上限 0% （共 33 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2426 | kd_oversold_cross | +0.9% | 1.39 | 26 | -25.5% | 0.64 | X | O | X | FAIL：PF_lower=0.64, exp=+0.9%, n=26, holdout=[A_new=NA B=O C=X] |
| 1216 | kd_oversold_cross | +0.4% | 1.41 | 18 | -10.7% | 0.39 | X | X | O | FAIL：PF_lower=0.39, exp=+0.4%, n=18, holdout=[A_new=NA B=NA C=O] |
| 2885 | kd_oversold_cross | +0.3% | 1.19 | 15 | -15.9% | 0.32 | X | O | X | FAIL：PF_lower=0.32, exp=+0.3%, n=15, holdout=[A_new=NA B=O C=X] |
| 2379 | kd_oversold_cross | +0.3% | 1.03 | 22 | -19.9% | 0.35 | X | X | X | FAIL：PF_lower=0.35, exp=+0.3%, n=22, holdout=[A_new=NA B=X C=X] |
| 2881 | kd_oversold_cross | +0.2% | 1.09 | 16 | -20.8% | 0.35 | X | O | X | FAIL：PF_lower=0.35, exp=+0.2%, n=16, holdout=[A_new=NA B=O C=X] |
| 00878 | kd_oversold_cross | +0.0% | 0.98 | 19 | -15.3% | 0.27 | X | X | X | FAIL：PF_lower=0.27, exp=+0.0%, n=19, holdout=[A_new=NA B=NA C=X] |
| 3661 | kd_oversold_cross | -0.0% | 0.87 | 14 | -28.4% | 0.27 | X | O | O | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 2603 | kd_oversold_cross | -0.1% | 0.90 | 21 | -37.1% | 0.31 | X | X | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 3045 | kd_oversold_cross | -0.1% | 0.87 | 18 | -14.4% | 0.24 | X | O | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 1605 | kd_oversold_cross | -0.4% | 0.71 | 25 | -30.5% | 0.24 | X | O | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2327 | kd_oversold_cross | -0.6% | 0.66 | 29 | -31.9% | 0.28 | X | O | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2886 | kd_oversold_cross | -0.6% | 0.56 | 21 | -26.2% | 0.19 | X | O | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 6505 | kd_oversold_cross | -0.8% | 0.56 | 34 | -37.7% | 0.21 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2618 | kd_oversold_cross | -0.8% | 0.69 | 22 | -38.9% | 0.22 | X | X | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2356 | kd_oversold_cross | -0.9% | 0.54 | 36 | -33.9% | 0.24 | X | O | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2412 | kd_oversold_cross | -0.9% | 0.34 | 16 | -19.9% | 0.04 | X | O | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 1809 | kd_oversold_cross | -1.0% | 0.50 | 47 | -55.6% | 0.22 | X | X | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 6669 | kd_oversold_cross | -1.0% | 0.76 | 26 | -57.0% | 0.32 | X | X | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2324 | kd_oversold_cross | -1.1% | 0.38 | 24 | -31.9% | 0.14 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 4938 | kd_oversold_cross | -1.1% | 0.36 | 31 | -36.3% | 0.14 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 9940 | kd_oversold_cross | -1.2% | 0.38 | 41 | -46.2% | 0.14 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2912 | kd_oversold_cross | -1.3% | 0.26 | 22 | -25.8% | 0.06 | X | O | O | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 0056 | kd_oversold_cross | -1.3% | 0.22 | 15 | -19.6% | 0.01 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 5880 | kd_oversold_cross | -1.3% | 0.34 | 17 | -26.2% | 0.10 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2207 | kd_oversold_cross | -1.3% | 0.39 | 35 | -38.4% | 0.10 | X | X | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 1227 | kd_oversold_cross | -1.4% | 0.16 | 41 | -44.9% | 0.06 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 1101 | kd_oversold_cross | -1.6% | 0.22 | 42 | -56.8% | 0.08 | X | O | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 9921 | kd_oversold_cross | -1.6% | 0.40 | 32 | -43.7% | 0.15 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2105 | kd_oversold_cross | -1.6% | 0.31 | 25 | -37.9% | 0.10 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2474 | kd_oversold_cross | -1.6% | 0.26 | 42 | -50.9% | 0.07 | X | X | O | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2002 | kd_oversold_cross | -1.9% | 0.23 | 35 | -57.6% | 0.06 | X | O | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2615 | kd_oversold_cross | -2.1% | 0.32 | 26 | -54.0% | 0.07 | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 5347 | kd_oversold_cross | -3.0% | 0.21 | 26 | -68.8% | 0.04 | X | X | X | FAIL：test expectancy=-3.0% < 0（負期望值） |
