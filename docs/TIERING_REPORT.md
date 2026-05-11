# TIERING REPORT — 20260511_232924

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 2 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 31 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 2 / 33**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2618 | keltner_breakout | +3.3% | 1.94 | 14 | -19.7% | 0.73 | X | O | O | PF_lower=0.73 ≥ 0.7, exp=+3.3% ≥ 1%, n=14≥5, holdout=[A_new=NA B=O C=O] |
| 3661 | keltner_breakout | +2.2% | 1.62 | 21 | -36.2% | 0.75 | X | O | X | PF_lower=0.75 ≥ 0.7, exp=+2.2% ≥ 1%, n=21≥5, holdout=[A_new=NA B=O C=X] |

### Tier F — 部位上限 0% （共 31 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2881 | keltner_breakout | +1.9% | 2.18 | 14 | -13.1% | 0.22 | X | X | X | FAIL：PF_lower=0.22, exp=+1.9%, n=14, holdout=[A_new=NA B=X C=X] |
| 9921 | keltner_breakout | +1.8% | 1.95 | 6 | -11.9% | 0.41 | X | O | X | FAIL：PF_lower=0.41, exp=+1.8%, n=6, holdout=[A_new=NA B=O C=NA] |
| 1605 | keltner_breakout | +1.7% | 1.35 | 15 | -37.9% | 0.53 | X | O | O | FAIL：PF_lower=0.53, exp=+1.7%, n=15, holdout=[A_new=NA B=O C=O] |
| 5347 | keltner_breakout | +1.7% | 1.55 | 12 | -19.6% | 0.53 | X | O | O | FAIL：PF_lower=0.53, exp=+1.7%, n=12, holdout=[A_new=NA B=O C=O] |
| 6669 | keltner_breakout | +1.3% | 1.15 | 23 | -33.8% | 0.54 | X | X | O | FAIL：PF_lower=0.54, exp=+1.3%, n=23, holdout=[A_new=NA B=NA C=O] |
| 2105 | keltner_breakout | +1.1% | 1.22 | 10 | -17.5% | 0.12 | X | X | X | FAIL：PF_lower=0.12, exp=+1.1%, n=10, holdout=[A_new=NA B=X C=X] |
| 0056 | keltner_breakout | +0.7% | 1.36 | 22 | -18.9% | 0.48 | X | X | X | FAIL：PF_lower=0.48, exp=+0.7%, n=22, holdout=[A_new=NA B=X C=X] |
| 00878 | keltner_breakout | +0.1% | 1.06 | 18 | -10.6% | 0.40 | X | X | X | FAIL：PF_lower=0.40, exp=+0.1%, n=18, holdout=[A_new=NA B=NA C=X] |
| 2885 | keltner_breakout | +0.0% | 0.97 | 35 | -24.6% | 0.47 | X | X | O | FAIL：PF_lower=0.47, exp=+0.0%, n=35, holdout=[A_new=NA B=X C=O] |
| 2426 | keltner_breakout | -0.4% | 0.78 | 17 | -41.7% | 0.22 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2886 | keltner_breakout | -0.4% | 0.79 | 22 | -39.7% | 0.08 | X | O | O | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2379 | keltner_breakout | -1.0% | 0.74 | 25 | -53.4% | 0.18 | X | O | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2002 | keltner_breakout | -1.3% | 0.63 | 6 | -21.9% | 0.01 | X | X | O | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 5880 | keltner_breakout | -1.3% | 0.51 | 8 | -13.0% | 0.00 | X | X | O | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 1101 | keltner_breakout | -1.5% | 0.46 | 10 | -17.3% | 0.08 | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 2327 | keltner_breakout | -1.6% | 0.57 | 14 | -35.2% | 0.17 | X | O | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 1216 | keltner_breakout | -1.6% | 0.16 | 8 | -15.1% | 0.00 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2412 | keltner_breakout | -1.7% | 0.32 | 12 | -19.7% | 0.00 | X | X | O | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 9940 | keltner_breakout | -1.7% | 0.33 | 9 | -14.8% | 0.00 | X | O | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2603 | keltner_breakout | -1.7% | 0.71 | 15 | -52.9% | 0.15 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 1809 | keltner_breakout | -2.0% | 0.53 | 27 | -56.0% | 0.25 | X | O | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 3045 | keltner_breakout | -2.1% | 0.11 | 13 | -27.4% | 0.00 | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2356 | keltner_breakout | -2.6% | 0.49 | 17 | -47.5% | 0.03 | X | O | X | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 1227 | keltner_breakout | -2.8% | 0.20 | 7 | -18.1% | 0.00 | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 4938 | keltner_breakout | -3.1% | 0.37 | 8 | -31.9% | 0.00 | X | X | X | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 2474 | keltner_breakout | -3.6% | 0.00 | 10 | -35.6% | 0.00 | X | X | X | FAIL：test expectancy=-3.6% < 0（負期望值） |
| 2912 | keltner_breakout | -3.7% | 0.00 | 7 | -23.3% | 0.00 | X | O | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2324 | keltner_breakout | -3.7% | 0.27 | 11 | -38.9% | 0.00 | X | X | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2207 | keltner_breakout | -3.8% | 0.19 | 15 | -45.0% | 0.00 | X | X | X | FAIL：test expectancy=-3.8% < 0（負期望值） |
| 6505 | keltner_breakout | -3.9% | 0.33 | 4 | -20.1% | N/A | X | O | X | FAIL：test expectancy=-3.9% < 0（負期望值） |
| 2615 | keltner_breakout | -4.0% | 0.37 | 11 | -45.2% | 0.08 | X | X | X | FAIL：test expectancy=-4.0% < 0（負期望值） |
