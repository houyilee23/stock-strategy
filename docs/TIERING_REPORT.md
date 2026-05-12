# TIERING REPORT — 20260512_233141

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 22 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 22**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 22 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2356 | stoch_rsi | +0.4% | 1.15 | 37 | -19.9% | 0.49 | X | X | X | FAIL：PF_lower=0.49, exp=+0.4%, n=37, holdout=[A_new=NA B=X C=X] |
| 2324 | stoch_rsi | -0.0% | 0.92 | 29 | -27.2% | 0.36 | X | X | X | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 2886 | stoch_rsi | -0.3% | 0.76 | 35 | -32.2% | 0.30 | X | O | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 3045 | stoch_rsi | -0.3% | 0.64 | 33 | -14.9% | 0.26 | X | O | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 0056 | stoch_rsi | -0.4% | 0.66 | 28 | -30.1% | 0.27 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2426 | stoch_rsi | -0.4% | 0.79 | 37 | -55.5% | 0.36 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2881 | stoch_rsi | -0.5% | 0.64 | 47 | -39.6% | 0.26 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 6669 | stoch_rsi | -0.6% | 0.75 | 80 | -64.6% | 0.48 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 1605 | stoch_rsi | -0.7% | 0.67 | 41 | -44.2% | 0.28 | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2379 | stoch_rsi | -0.7% | 0.68 | 51 | -43.9% | 0.35 | X | O | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2412 | stoch_rsi | -0.8% | 0.27 | 36 | -29.5% | 0.10 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2207 | stoch_rsi | -0.9% | 0.53 | 50 | -39.1% | 0.22 | X | X | O | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 1216 | stoch_rsi | -0.9% | 0.33 | 27 | -23.2% | 0.08 | X | O | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2912 | stoch_rsi | -1.1% | 0.37 | 38 | -40.7% | 0.09 | X | O | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2105 | stoch_rsi | -1.1% | 0.42 | 37 | -36.2% | 0.18 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2474 | stoch_rsi | -1.5% | 0.36 | 41 | -49.1% | 0.18 | X | X | O | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 9940 | stoch_rsi | -1.6% | 0.16 | 46 | -55.9% | 0.04 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 5880 | stoch_rsi | -1.7% | 0.33 | 26 | -42.8% | 0.09 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 1227 | stoch_rsi | -1.9% | 0.08 | 52 | -66.3% | 0.02 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 1101 | stoch_rsi | -2.2% | 0.10 | 49 | -68.7% | 0.03 | X | X | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 2002 | stoch_rsi | -2.2% | 0.18 | 53 | -72.1% | 0.07 | X | X | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 9921 | stoch_rsi | -2.8% | 0.19 | 45 | -75.6% | 0.07 | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
