# TIERING REPORT — 20260509_072626

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 2 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 7 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 41 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 9 / 50**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2345 | narrow_range_breakout | +7.3% | 4.70 | 19 | -27.8% | 1.39 | X | X | O | PF_lower=1.39 ≥ 1.0, exp=+7.3% ≥ 2%, n=19≥5, holdout=[A_new=NA B=X C=O] |
| 2344 | narrow_range_breakout | +5.4% | 2.39 | 21 | -23.8% | 1.11 | X | X | X | PF_lower=1.11 ≥ 1.0, exp=+5.4% ≥ 2%, n=21≥5, holdout=[A_new=NA B=NA C=X] |

### Tier C — 部位上限 15% （共 7 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3034 | narrow_range_breakout | +4.2% | 2.21 | 13 | -22.4% | 0.78 | X | O | X | PF_lower=0.78 ≥ 0.7, exp=+4.2% ≥ 1%, n=13≥5, holdout=[A_new=NA B=O C=NA] |
| 2303 | narrow_range_breakout | +3.2% | 2.53 | 14 | -22.3% | 0.79 | X | O | X | PF_lower=0.79 ≥ 0.7, exp=+3.2% ≥ 1%, n=14≥5, holdout=[A_new=NA B=O C=NA] |
| 2891 | narrow_range_breakout | +2.8% | 2.10 | 23 | -19.4% | 0.93 | X | X | X | PF_lower=0.93 ≥ 0.7, exp=+2.8% ≥ 1%, n=23≥5, holdout=[A_new=NA B=X C=X] |
| 2027 | narrow_range_breakout | +2.3% | 3.69 | 15 | -13.0% | 0.93 | X | O | O | PF_lower=0.93 ≥ 0.7, exp=+2.3% ≥ 1%, n=15≥5, holdout=[A_new=NA B=O C=O] |
| 6271 | narrow_range_breakout | +2.3% | 2.25 | 20 | -23.6% | 0.76 | X | O | X | PF_lower=0.76 ≥ 0.7, exp=+2.3% ≥ 1%, n=20≥5, holdout=[A_new=NA B=O C=NA] |
| 2360 | narrow_range_breakout | +1.9% | 2.25 | 26 | -18.6% | 0.93 | X | O | O | PF_lower=0.93 ≥ 0.7, exp=+1.9% ≥ 1%, n=26≥5, holdout=[A_new=NA B=O C=O] |
| 3037 | narrow_range_breakout | +1.7% | 2.75 | 32 | -23.7% | 1.08 | X | X | O | PF_lower=1.08 ≥ 0.7, exp=+1.7% ≥ 1%, n=32≥5, holdout=[A_new=NA B=NA C=O] |

### Tier F — 部位上限 0% （共 41 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2356 | narrow_range_breakout | +3.4% | 1.94 | 15 | -16.1% | 0.70 | X | O | X | FAIL：PF_lower=0.70, exp=+3.4%, n=15, holdout=[A_new=NA B=O C=X] |
| 2426 | narrow_range_breakout | +2.5% | 1.65 | 19 | -28.8% | 0.67 | X | O | X | FAIL：PF_lower=0.67, exp=+2.5%, n=19, holdout=[A_new=NA B=O C=X] |
| 1605 | narrow_range_breakout | +2.5% | 1.36 | 20 | -39.7% | 0.61 | X | O | O | FAIL：PF_lower=0.61, exp=+2.5%, n=20, holdout=[A_new=NA B=O C=O] |
| 2603 | narrow_range_breakout | +1.0% | 1.09 | 24 | -36.2% | 0.51 | X | X | X | FAIL：PF_lower=0.51, exp=+1.0%, n=24, holdout=[A_new=NA B=NA C=X] |
| 9940 | narrow_range_breakout | +1.0% | 1.25 | 14 | -26.0% | 0.34 | X | X | X | FAIL：PF_lower=0.34, exp=+1.0%, n=14, holdout=[A_new=NA B=X C=X] |
| 2324 | narrow_range_breakout | +0.5% | 1.03 | 19 | -23.3% | 0.43 | X | X | X | FAIL：PF_lower=0.43, exp=+0.5%, n=19, holdout=[A_new=NA B=X C=X] |
| 4938 | narrow_range_breakout | +0.5% | 1.07 | 18 | -31.3% | 0.38 | X | X | X | FAIL：PF_lower=0.38, exp=+0.5%, n=18, holdout=[A_new=NA B=X C=X] |
| 3231 | narrow_range_breakout | +0.4% | 1.01 | 24 | -36.3% | 0.36 | X | O | X | FAIL：PF_lower=0.36, exp=+0.4%, n=24, holdout=[A_new=NA B=O C=X] |
| 2618 | narrow_range_breakout | +0.3% | 0.99 | 19 | -41.4% | 0.36 | X | O | O | FAIL：PF_lower=0.36, exp=+0.3%, n=19, holdout=[A_new=NA B=O C=O] |
| 2327 | narrow_range_breakout | +0.1% | 0.91 | 14 | -35.1% | 0.35 | X | O | X | FAIL：PF_lower=0.35, exp=+0.1%, n=14, holdout=[A_new=NA B=O C=X] |
| 0056 | narrow_range_breakout | +0.1% | 0.99 | 17 | -11.1% | 0.27 | X | X | X | FAIL：PF_lower=0.27, exp=+0.1%, n=17, holdout=[A_new=NA B=X C=X] |
| 2885 | narrow_range_breakout | -0.1% | 0.91 | 20 | -24.1% | 0.35 | X | O | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 2412 | narrow_range_breakout | -0.1% | 0.87 | 21 | -17.7% | 0.28 | X | X | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 6669 | narrow_range_breakout | -0.2% | 0.81 | 24 | -60.3% | 0.39 | X | X | X | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 2881 | narrow_range_breakout | -0.4% | 0.81 | 20 | -18.7% | 0.24 | X | X | O | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 00878 | narrow_range_breakout | -0.4% | 0.75 | 29 | -29.0% | 0.25 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 6488 | narrow_range_breakout | -0.5% | 0.80 | 14 | -29.8% | 0.32 | X | O | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 3045 | narrow_range_breakout | -0.6% | 0.63 | 18 | -21.2% | 0.16 | X | O | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2308 | narrow_range_breakout | -0.6% | 0.73 | 21 | -45.7% | 0.35 | X | X | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2886 | narrow_range_breakout | -0.6% | 0.76 | 25 | -31.6% | 0.32 | X | O | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 9921 | narrow_range_breakout | -0.7% | 0.69 | 18 | -20.8% | 0.27 | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 9914 | narrow_range_breakout | -0.7% | 0.77 | 12 | -26.8% | 0.27 | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2379 | narrow_range_breakout | -0.9% | 0.75 | 14 | -30.9% | 0.27 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 1102 | narrow_range_breakout | -1.0% | 0.62 | 15 | -28.6% | 0.12 | X | O | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2002 | narrow_range_breakout | -1.0% | 0.67 | 13 | -29.7% | 0.21 | X | O | O | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2892 | narrow_range_breakout | -1.3% | 0.45 | 18 | -27.1% | 0.11 | X | X | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2884 | narrow_range_breakout | -1.4% | 0.56 | 17 | -31.4% | 0.13 | X | X | O | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2105 | narrow_range_breakout | -1.5% | 0.53 | 22 | -42.4% | 0.18 | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 1227 | narrow_range_breakout | -1.6% | 0.49 | 7 | -21.0% | 0.00 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 00940 | narrow_range_breakout | -1.8% | 0.18 | 13 | -24.3% | 0.02 | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2615 | narrow_range_breakout | -1.9% | 0.64 | 16 | -59.7% | 0.24 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 3661 | narrow_range_breakout | -2.1% | 0.52 | 37 | -67.9% | 0.31 | X | O | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 5880 | narrow_range_breakout | -2.1% | 0.38 | 19 | -42.1% | 0.06 | X | O | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2474 | narrow_range_breakout | -2.2% | 0.47 | 20 | -41.0% | 0.12 | X | O | O | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 5347 | narrow_range_breakout | -2.6% | 0.54 | 7 | -32.5% | 0.00 | X | X | X | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 1216 | narrow_range_breakout | -3.2% | 0.22 | 15 | -44.1% | 0.03 | X | O | X | FAIL：test expectancy=-3.2% < 0（負期望值） |
| 1809 | narrow_range_breakout | -3.3% | 0.52 | 17 | -64.6% | 0.11 | X | O | X | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 6505 | narrow_range_breakout | -3.3% | 0.36 | 6 | -29.1% | 0.00 | X | O | X | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 2912 | narrow_range_breakout | -3.8% | 0.05 | 12 | -41.7% | 0.00 | X | O | X | FAIL：test expectancy=-3.8% < 0（負期望值） |
| 2207 | narrow_range_breakout | -3.9% | 0.23 | 11 | -36.7% | 0.00 | X | X | X | FAIL：test expectancy=-3.9% < 0（負期望值） |
| 1101 | narrow_range_breakout | -5.5% | 0.12 | 10 | -49.5% | 0.00 | X | O | X | FAIL：test expectancy=-5.5% < 0（負期望值） |
