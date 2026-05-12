# TIERING REPORT — 20260513_041211

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 1 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 19 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 20**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6669 | coppock_buy | +2.2% | 3.25 | 23 | -17.3% | 1.31 | X | X | O | PF_lower=1.31 ≥ 1.0, exp=+2.2% ≥ 2%, n=23≥5, holdout=[A_new=NA B=NA C=O] |

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 19 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2324 | coppock_buy | +1.7% | 1.40 | 12 | -24.0% | 0.36 | X | X | X | FAIL：PF_lower=0.36, exp=+1.7%, n=12, holdout=[A_new=NA B=X C=X] |
| 2881 | coppock_buy | +0.9% | 1.44 | 15 | -18.5% | 0.30 | X | X | X | FAIL：PF_lower=0.30, exp=+0.9%, n=15, holdout=[A_new=NA B=X C=X] |
| 2356 | coppock_buy | +0.3% | 0.99 | 21 | -43.0% | 0.26 | X | O | X | FAIL：PF_lower=0.26, exp=+0.3%, n=21, holdout=[A_new=NA B=O C=X] |
| 2105 | coppock_buy | +0.1% | 0.96 | 19 | -27.3% | 0.02 | X | X | X | FAIL：PF_lower=0.02, exp=+0.1%, n=19, holdout=[A_new=NA B=X C=X] |
| 2379 | coppock_buy | -0.1% | 0.90 | 21 | -45.7% | 0.37 | X | O | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 2474 | coppock_buy | -0.2% | 0.83 | 26 | -24.7% | 0.20 | X | X | O | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 2886 | coppock_buy | -0.3% | 0.82 | 20 | -29.9% | 0.12 | X | O | O | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 2412 | coppock_buy | -0.3% | 0.71 | 16 | -12.4% | 0.12 | X | O | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 0056 | coppock_buy | -0.5% | 0.67 | 13 | -19.3% | 0.00 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 9940 | coppock_buy | -0.6% | 0.68 | 28 | -36.8% | 0.16 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 1101 | coppock_buy | -0.8% | 0.64 | 18 | -33.5% | 0.09 | X | O | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 3045 | coppock_buy | -1.0% | 0.48 | 23 | -27.3% | 0.10 | X | X | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 5880 | coppock_buy | -1.1% | 0.50 | 21 | -33.8% | 0.06 | X | X | O | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2002 | coppock_buy | -1.1% | 0.62 | 21 | -37.4% | 0.11 | X | X | O | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2912 | coppock_buy | -1.2% | 0.39 | 15 | -23.3% | 0.09 | X | O | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 9921 | coppock_buy | -1.3% | 0.41 | 19 | -30.1% | 0.00 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 1216 | coppock_buy | -1.9% | 0.38 | 19 | -36.0% | 0.04 | X | O | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2207 | coppock_buy | -2.0% | 0.39 | 16 | -29.7% | 0.11 | X | O | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 1227 | coppock_buy | -2.5% | 0.07 | 24 | -47.3% | 0.00 | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
