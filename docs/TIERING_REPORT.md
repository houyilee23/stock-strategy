# TIERING REPORT — 20260514_023341

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 32 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 33**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 32 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2823 | coppock_buy | +3.8% | inf | 1 | -2.2% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2014 | coppock_buy | +3.6% | 2.04 | 7 | -9.3% | 0.19 | X | X | X | FAIL：PF_lower=0.19, exp=+3.6%, n=7, holdout=[A_new=NA B=NA C=NA] |
| 1582 | coppock_buy | +2.2% | 2.16 | 12 | -22.0% | 0.10 | X | X | X | FAIL：PF_lower=0.10, exp=+2.2%, n=12, holdout=[A_new=NA B=X C=X] |
| 8069 | coppock_buy | +1.8% | 1.27 | 16 | -27.3% | 0.43 | X | X | O | FAIL：PF_lower=0.43, exp=+1.8%, n=16, holdout=[A_new=NA B=X C=O] |
| 2009 | coppock_buy | +1.5% | 1.32 | 13 | -22.7% | 0.00 | X | X | O | FAIL：PF_lower=0.00, exp=+1.5%, n=13, holdout=[A_new=NA B=X C=O] |
| 8454 | coppock_buy | +1.2% | 1.18 | 7 | -20.3% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.2%, n=7, holdout=[A_new=NA B=NA C=X] |
| 2049 | coppock_buy | +0.8% | 1.12 | 20 | -36.1% | 0.27 | X | O | O | FAIL：PF_lower=0.27, exp=+0.8%, n=20, holdout=[A_new=NA B=O C=O] |
| 2723 | coppock_buy | +0.3% | 0.95 | 12 | -22.8% | 0.02 | X | X | O | FAIL：PF_lower=0.02, exp=+0.3%, n=12, holdout=[A_new=NA B=X C=O] |
| 2105 | coppock_buy | +0.1% | 0.96 | 19 | -27.3% | 0.02 | X | X | X | FAIL：PF_lower=0.02, exp=+0.1%, n=19, holdout=[A_new=NA B=X C=X] |
| 2886 | coppock_buy | -0.3% | 0.82 | 20 | -29.9% | 0.12 | X | O | O | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 2609 | coppock_buy | -0.3% | 0.81 | 17 | -35.3% | 0.23 | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 0056 | coppock_buy | -0.5% | 0.67 | 13 | -19.3% | 0.00 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 9940 | coppock_buy | -0.6% | 0.68 | 28 | -36.8% | 0.16 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 5269 | coppock_buy | -0.7% | 0.76 | 16 | -28.9% | 0.16 | X | O | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 9933 | coppock_buy | -0.7% | 0.69 | 17 | -27.3% | 0.23 | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 1101 | coppock_buy | -0.8% | 0.64 | 18 | -33.5% | 0.09 | X | O | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 1456 | coppock_buy | -0.9% | 0.66 | 28 | -50.8% | 0.20 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 4961 | coppock_buy | -0.9% | 0.61 | 16 | -47.7% | 0.00 | X | O | O | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 3045 | coppock_buy | -1.0% | 0.48 | 23 | -27.3% | 0.10 | X | X | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 5880 | coppock_buy | -1.1% | 0.50 | 21 | -33.8% | 0.06 | X | X | O | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 1907 | coppock_buy | -1.2% | 0.68 | 16 | -39.6% | 0.02 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2867 | coppock_buy | -1.2% | 0.58 | 18 | -43.2% | 0.02 | X | X | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2912 | coppock_buy | -1.2% | 0.39 | 15 | -23.3% | 0.09 | X | O | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 9921 | coppock_buy | -1.3% | 0.41 | 19 | -30.1% | 0.00 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 3481 | coppock_buy | -1.3% | 0.61 | 15 | -54.6% | 0.14 | X | X | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2371 | coppock_buy | -1.6% | 0.44 | 27 | -42.5% | 0.16 | X | O | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 1717 | coppock_buy | -1.8% | 0.37 | 21 | -53.7% | 0.02 | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2458 | coppock_buy | -2.2% | 0.39 | 21 | -52.5% | 0.02 | X | O | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 5876 | coppock_buy | -2.3% | 0.20 | 30 | -52.4% | 0.02 | X | O | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 2227 | coppock_buy | -2.5% | 0.15 | 26 | -53.7% | 0.00 | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 1227 | coppock_buy | -2.5% | 0.07 | 24 | -47.3% | 0.00 | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 1521 | coppock_buy | -7.6% | 0.12 | 19 | -100.0% | 0.00 | X | X | X | FAIL：test expectancy=-7.6% < 0（負期望值） |
