# TIERING REPORT — 20260512_040934

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 23 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 24**  （目標 ≥ 20）

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
| 6505 | ema_cross | +10.1% | 7.60 | 3 | -13.4% | N/A | X | O | X | LOW_N_RESCUE：n=3, raw_PF=7.60 ≥ 3.0, exp=+10.1% ≥ 5%, |DD|=13% ≤ 25%, holdout=[A_new=NA B=O C=NA]（紙上交易 3 個月） |

### Tier F — 部位上限 0% （共 23 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2881 | ema_cross | +5.5% | 3.60 | 2 | -7.4% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2426 | ema_cross | +2.5% | 1.44 | 8 | -21.2% | 0.23 | X | O | X | FAIL：PF_lower=0.23, exp=+2.5%, n=8, holdout=[A_new=NA B=O C=NA] |
| 6669 | ema_cross | +1.8% | 1.25 | 9 | -27.6% | 0.22 | X | X | X | FAIL：PF_lower=0.22, exp=+1.8%, n=9, holdout=[A_new=NA B=NA C=NA] |
| 3045 | ema_cross | +1.2% | 1.76 | 6 | -10.0% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+1.2%, n=6, holdout=[A_new=NA B=O C=NA] |
| 1605 | ema_cross | +1.1% | 1.17 | 10 | -23.8% | 0.00 | X | O | O | FAIL：PF_lower=0.00, exp=+1.1%, n=10, holdout=[A_new=NA B=O C=O] |
| 2603 | ema_cross | +0.8% | 1.06 | 8 | -26.9% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+0.8%, n=8, holdout=[A_new=NA B=NA C=X] |
| 2412 | ema_cross | +0.7% | 1.43 | 10 | -14.2% | 0.22 | X | X | X | FAIL：PF_lower=0.22, exp=+0.7%, n=10, holdout=[A_new=NA B=X C=X] |
| 9940 | ema_cross | -0.6% | 0.69 | 18 | -30.6% | 0.13 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 1216 | ema_cross | -0.6% | 0.73 | 10 | -15.1% | 0.00 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2474 | ema_cross | -0.9% | 0.57 | 8 | -14.3% | 0.01 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2324 | ema_cross | -0.9% | 0.61 | 12 | -17.6% | 0.20 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2356 | ema_cross | -1.3% | 0.51 | 13 | -38.6% | 0.00 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 9921 | ema_cross | -1.6% | 0.50 | 8 | -26.6% | 0.00 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 0056 | ema_cross | -1.7% | 0.29 | 3 | -8.2% | N/A | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2886 | ema_cross | -2.0% | 0.44 | 7 | -22.4% | 0.00 | X | X | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 2105 | ema_cross | -2.3% | 0.34 | 11 | -23.7% | 0.00 | X | X | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 2912 | ema_cross | -2.4% | 0.19 | 9 | -21.6% | 0.00 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 1227 | ema_cross | -2.5% | 0.00 | 18 | -36.7% | 0.00 | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 5880 | ema_cross | -2.8% | 0.00 | 8 | -23.7% | 0.00 | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 1101 | ema_cross | -3.8% | 0.00 | 6 | -21.1% | 0.00 | X | X | X | FAIL：test expectancy=-3.8% < 0（負期望值） |
| 2379 | ema_cross | -4.1% | 0.12 | 7 | -30.1% | 0.00 | X | O | X | FAIL：test expectancy=-4.1% < 0（負期望值） |
| 2207 | ema_cross | -4.4% | 0.27 | 8 | -33.2% | 0.00 | X | X | X | FAIL：test expectancy=-4.4% < 0（負期望值） |
| 2002 | ema_cross | -7.9% | 0.00 | 4 | -28.0% | N/A | X | X | X | FAIL：test expectancy=-7.9% < 0（負期望值） |
