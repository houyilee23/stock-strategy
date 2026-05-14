# TIERING REPORT — 20260514_133550

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 21 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 21**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 21 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 4961 | macd_cross | +2.2% | 1.67 | 13 | -19.6% | 0.49 | X | O | X | FAIL：PF_lower=0.49, exp=+2.2%, n=13, holdout=[A_new=NA B=O C=NA] |
| 1101 | macd_cross | +0.4% | 1.26 | 14 | -10.3% | 0.44 | X | O | X | FAIL：PF_lower=0.44, exp=+0.4%, n=14, holdout=[A_new=NA B=O C=NA] |
| 2609 | macd_cross | -0.4% | 0.80 | 13 | -36.8% | 0.11 | X | X | O | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2371 | macd_cross | -0.5% | 0.71 | 29 | -47.1% | 0.20 | X | O | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 5880 | macd_cross | -0.6% | 0.66 | 22 | -22.9% | 0.21 | X | O | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2105 | macd_cross | -0.7% | 0.67 | 21 | -23.1% | 0.16 | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2886 | macd_cross | -0.7% | 0.51 | 33 | -27.9% | 0.20 | X | O | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2823 | macd_cross | -0.8% | 0.51 | 12 | -16.7% | 0.00 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 9933 | macd_cross | -1.1% | 0.57 | 13 | -23.0% | 0.14 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 1227 | macd_cross | -1.2% | 0.31 | 12 | -14.2% | 0.00 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 0056 | macd_cross | -1.2% | 0.32 | 25 | -30.9% | 0.00 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2723 | macd_cross | -1.4% | 0.49 | 15 | -37.4% | 0.00 | X | X | O | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 3481 | macd_cross | -1.4% | 0.62 | 21 | -57.5% | 0.10 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 9940 | macd_cross | -1.4% | 0.29 | 19 | -33.6% | 0.04 | X | X | O | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2912 | macd_cross | -1.7% | 0.08 | 38 | -48.0% | 0.00 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 5269 | macd_cross | -1.9% | 0.61 | 29 | -63.2% | 0.20 | X | O | O | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 5876 | macd_cross | -2.1% | 0.22 | 21 | -37.1% | 0.02 | X | O | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2014 | macd_cross | -2.3% | 0.52 | 13 | -43.6% | 0.00 | X | X | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 2227 | macd_cross | -2.4% | 0.06 | 17 | -34.2% | 0.00 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 2867 | macd_cross | -3.2% | 0.07 | 13 | -35.9% | 0.00 | X | O | X | FAIL：test expectancy=-3.2% < 0（負期望值） |
| 1521 | macd_cross | -10.6% | 0.15 | 11 | -100.0% | 0.00 | X | X | X | FAIL：test expectancy=-10.6% < 0（負期望值） |
