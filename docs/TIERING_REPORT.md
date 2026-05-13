# TIERING REPORT — 20260513_122307

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 17 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 17**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 17 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 9921 | failed_breakdown | +2.2% | 1.67 | 14 | -12.6% | 0.55 | X | O | O | FAIL：PF_lower=0.55, exp=+2.2%, n=14, holdout=[A_new=NA B=O C=O] |
| 2105 | failed_breakdown | +2.2% | 2.00 | 9 | -17.0% | 0.36 | X | O | O | FAIL：PF_lower=0.36, exp=+2.2%, n=9, holdout=[A_new=NA B=O C=O] |
| 3045 | failed_breakdown | +1.0% | 2.27 | 3 | -6.0% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2324 | failed_breakdown | +1.0% | 1.38 | 5 | -11.1% | 0.08 | X | X | O | FAIL：PF_lower=0.08, exp=+1.0%, n=5, holdout=[A_new=NA B=X C=O] |
| 2207 | failed_breakdown | +1.0% | 1.32 | 10 | -19.2% | 0.29 | X | X | O | FAIL：PF_lower=0.29, exp=+1.0%, n=10, holdout=[A_new=NA B=X C=O] |
| 1227 | failed_breakdown | +0.0% | 0.95 | 18 | -15.8% | 0.22 | X | O | X | FAIL：PF_lower=0.22, exp=+0.0%, n=18, holdout=[A_new=NA B=O C=X] |
| 5880 | failed_breakdown | -0.3% | 0.80 | 8 | -10.0% | 0.08 | X | X | O | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 0056 | failed_breakdown | -1.1% | 0.56 | 4 | -11.5% | N/A | X | O | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2356 | failed_breakdown | -1.3% | 0.65 | 10 | -28.0% | 0.08 | X | X | O | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2886 | failed_breakdown | -1.4% | 0.47 | 17 | -26.1% | 0.10 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2912 | failed_breakdown | -1.8% | 0.36 | 18 | -37.2% | 0.01 | X | O | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 1101 | failed_breakdown | -1.8% | 0.40 | 10 | -23.4% | 0.00 | X | O | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 9940 | failed_breakdown | -1.9% | 0.44 | 10 | -25.7% | 0.00 | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2412 | failed_breakdown | -3.7% | 0.00 | 3 | -10.8% | N/A | X | X | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2002 | failed_breakdown | -3.8% | 0.08 | 7 | -26.9% | 0.00 | X | X | X | FAIL：test expectancy=-3.8% < 0（負期望值） |
| 2474 | failed_breakdown | -4.7% | 0.00 | 3 | -13.5% | N/A | X | X | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 2379 | failed_breakdown | -5.7% | 0.00 | 5 | -29.9% | 0.00 | X | O | X | FAIL：test expectancy=-5.7% < 0（負期望值） |
