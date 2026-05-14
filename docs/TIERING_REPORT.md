# TIERING REPORT — 20260514_083612

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 25 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 26**  （目標 ≥ 20）

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
| 1582 | keltner_breakout | +3.2% | 1.99 | 16 | -23.9% | 0.75 | X | X | O | PF_lower=0.75 ≥ 0.7, exp=+3.2% ≥ 1%, n=16≥5, holdout=[A_new=NA B=NA C=O] |

### Tier F — 部位上限 0% （共 25 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 4961 | keltner_breakout | +3.8% | 1.38 | 11 | -37.4% | 0.12 | X | O | X | FAIL：PF_lower=0.12, exp=+3.8%, n=11, holdout=[A_new=NA B=O C=X] |
| 2105 | keltner_breakout | +1.1% | 1.22 | 10 | -17.5% | 0.12 | X | X | X | FAIL：PF_lower=0.12, exp=+1.1%, n=10, holdout=[A_new=NA B=X C=X] |
| 2049 | keltner_breakout | +1.0% | 1.17 | 10 | -24.1% | 0.28 | X | O | X | FAIL：PF_lower=0.28, exp=+1.0%, n=10, holdout=[A_new=NA B=O C=NA] |
| 3481 | keltner_breakout | +0.7% | 1.05 | 17 | -34.3% | 0.34 | X | X | X | FAIL：PF_lower=0.34, exp=+0.7%, n=17, holdout=[A_new=NA B=NA C=NA] |
| 0056 | keltner_breakout | +0.7% | 1.36 | 22 | -18.9% | 0.48 | X | X | X | FAIL：PF_lower=0.48, exp=+0.7%, n=22, holdout=[A_new=NA B=X C=X] |
| 2823 | keltner_breakout | +0.6% | 1.32 | 3 | -6.7% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9933 | keltner_breakout | +0.3% | 1.03 | 13 | -21.2% | 0.32 | X | X | X | FAIL：PF_lower=0.32, exp=+0.3%, n=13, holdout=[A_new=NA B=X C=X] |
| 2458 | keltner_breakout | -0.1% | 0.93 | 12 | -37.4% | 0.24 | X | O | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 2886 | keltner_breakout | -0.4% | 0.79 | 22 | -39.7% | 0.08 | X | O | O | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2723 | keltner_breakout | -0.7% | 0.79 | 11 | -31.3% | 0.16 | X | X | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 5880 | keltner_breakout | -1.0% | 0.56 | 18 | -28.4% | 0.10 | X | X | O | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 5876 | keltner_breakout | -1.4% | 0.35 | 12 | -16.5% | 0.00 | X | O | O | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 1101 | keltner_breakout | -1.5% | 0.46 | 10 | -17.3% | 0.08 | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 5269 | keltner_breakout | -1.7% | 0.59 | 21 | -36.0% | 0.20 | X | O | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 9940 | keltner_breakout | -1.9% | 0.36 | 17 | -33.8% | 0.00 | X | O | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 3045 | keltner_breakout | -2.1% | 0.11 | 13 | -27.4% | 0.00 | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 1456 | keltner_breakout | -2.5% | 0.57 | 8 | -32.6% | 0.00 | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 2371 | keltner_breakout | -2.6% | 0.54 | 13 | -43.0% | 0.11 | X | O | X | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 2867 | keltner_breakout | -2.7% | 0.42 | 8 | -22.3% | 0.00 | X | O | X | FAIL：test expectancy=-2.7% < 0（負期望值） |
| 1227 | keltner_breakout | -2.8% | 0.20 | 7 | -18.1% | 0.00 | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 2609 | keltner_breakout | -3.1% | 0.39 | 22 | -59.6% | 0.10 | X | X | X | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 1521 | keltner_breakout | -3.4% | 0.27 | 12 | -38.2% | 0.01 | X | X | X | FAIL：test expectancy=-3.4% < 0（負期望值） |
| 2912 | keltner_breakout | -3.7% | 0.00 | 7 | -23.3% | 0.00 | X | O | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2227 | keltner_breakout | -3.7% | 0.00 | 2 | -13.0% | N/A | X | X | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2014 | keltner_breakout | -5.3% | 0.21 | 15 | -60.0% | 0.00 | X | O | X | FAIL：test expectancy=-5.3% < 0（負期望值） |
