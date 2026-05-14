# TIERING REPORT — 20260514_053311

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 1 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 28 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 29**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1717 | three_day_reversal | +4.7% | inf | 7 | -7.6% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+4.7% ≥ 3%, n=7≥6, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥2.0 自動晉升 |

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 28 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2723 | three_day_reversal | +10.3% | inf | 1 | -1.9% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2014 | three_day_reversal | +2.3% | 1.39 | 9 | -35.0% | 0.42 | X | X | X | FAIL：PF_lower=0.42, exp=+2.3%, n=9, holdout=[A_new=NA B=NA C=X] |
| 2458 | three_day_reversal | +1.4% | 1.56 | 6 | -11.6% | 0.28 | X | X | X | FAIL：PF_lower=0.28, exp=+1.4%, n=6, holdout=[A_new=NA B=NA C=X] |
| 5876 | three_day_reversal | +0.4% | 1.43 | 2 | -3.6% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3481 | three_day_reversal | -0.5% | 0.82 | 6 | -30.8% | 0.12 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 2912 | three_day_reversal | -1.1% | 0.47 | 2 | -4.5% | N/A | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 1456 | three_day_reversal | -1.1% | 0.64 | 18 | -36.6% | 0.14 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 5880 | three_day_reversal | -1.2% | 0.47 | 14 | -25.5% | 0.07 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2609 | three_day_reversal | -1.3% | 0.63 | 10 | -30.4% | 0.13 | X | X | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2886 | three_day_reversal | -1.5% | 0.44 | 2 | -7.2% | N/A | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 2867 | three_day_reversal | -1.7% | 0.43 | 13 | -32.0% | 0.00 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 9940 | three_day_reversal | -1.8% | 0.14 | 6 | -12.0% | 0.00 | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 1582 | three_day_reversal | -1.9% | 0.49 | 16 | -36.8% | 0.12 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2105 | three_day_reversal | -1.9% | 0.52 | 10 | -29.6% | 0.03 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 4961 | three_day_reversal | -2.1% | 0.55 | 9 | -21.8% | 0.09 | X | O | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2049 | three_day_reversal | -2.9% | 0.18 | 4 | -15.4% | N/A | X | O | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2009 | three_day_reversal | -3.1% | 0.43 | 4 | -19.0% | N/A | X | O | X | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 9933 | three_day_reversal | -3.1% | 0.00 | 1 | -6.5% | N/A | X | X | X | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 8454 | three_day_reversal | -4.5% | 0.24 | 4 | -18.2% | N/A | X | X | X | FAIL：test expectancy=-4.5% < 0（負期望值） |
| 1101 | three_day_reversal | -4.8% | 0.00 | 2 | -10.2% | N/A | X | O | X | FAIL：test expectancy=-4.8% < 0（負期望值） |
| 2371 | three_day_reversal | -5.0% | 0.17 | 5 | -23.1% | 0.00 | X | O | X | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 0056 | three_day_reversal | -5.0% | 0.00 | 1 | -7.7% | N/A | X | X | X | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 1521 | three_day_reversal | -7.1% | 0.00 | 2 | -13.8% | N/A | X | X | X | FAIL：test expectancy=-7.1% < 0（負期望值） |
| 5269 | three_day_reversal | -7.8% | 0.08 | 6 | -44.1% | 0.00 | X | O | X | FAIL：test expectancy=-7.8% < 0（負期望值） |
| 1227 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2227 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2823 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3045 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
