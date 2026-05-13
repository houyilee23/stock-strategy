# TIERING REPORT — 20260513_163816

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 13 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 13**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 13 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2105 | weekly_low_buy | +1.3% | 2.38 | 5 | -4.7% | 0.29 | X | X | X | FAIL：PF_lower=0.29, exp=+1.3%, n=5, holdout=[A_new=NA B=X C=NA] |
| 5880 | weekly_low_buy | +1.0% | 1.97 | 10 | -7.5% | 0.29 | X | O | O | FAIL：PF_lower=0.29, exp=+1.0%, n=10, holdout=[A_new=NA B=O C=O] |
| 3045 | weekly_low_buy | +0.2% | 1.02 | 5 | -8.8% | 0.04 | X | O | X | FAIL：PF_lower=0.04, exp=+0.2%, n=5, holdout=[A_new=NA B=O C=X] |
| 0056 | weekly_low_buy | +0.1% | 1.02 | 9 | -14.9% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+0.1%, n=9, holdout=[A_new=NA B=O C=X] |
| 9940 | weekly_low_buy | -0.7% | 0.45 | 22 | -17.2% | 0.00 | X | O | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 9921 | weekly_low_buy | -1.5% | 0.15 | 15 | -19.9% | 0.00 | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 2412 | weekly_low_buy | -1.6% | 0.28 | 5 | -14.5% | 0.00 | X | O | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2002 | weekly_low_buy | -1.7% | 0.00 | 18 | -27.9% | 0.00 | X | O | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2886 | weekly_low_buy | -1.9% | 0.23 | 5 | -17.7% | 0.00 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2912 | weekly_low_buy | -2.1% | 0.32 | 15 | -36.9% | 0.00 | X | O | O | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 1101 | weekly_low_buy | -2.1% | 0.10 | 12 | -26.0% | 0.00 | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 1227 | weekly_low_buy | -2.3% | 0.01 | 28 | -49.9% | 0.00 | X | X | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 2474 | weekly_low_buy | -2.6% | 0.01 | 11 | -25.7% | 0.00 | X | X | O | FAIL：test expectancy=-2.6% < 0（負期望值） |
