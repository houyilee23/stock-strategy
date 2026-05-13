# TIERING REPORT — 20260513_104916

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
| 2474 | double_volume | +1.6% | inf | 2 | -3.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 0056 | double_volume | +1.3% | 2.08 | 7 | -10.0% | 0.27 | X | O | X | FAIL：PF_lower=0.27, exp=+1.3%, n=7, holdout=[A_new=NA B=O C=NA] |
| 2324 | double_volume | -0.0% | 0.94 | 5 | -9.2% | 0.02 | X | X | O | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 2412 | double_volume | -0.3% | 0.77 | 4 | -4.2% | N/A | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 2912 | double_volume | -0.4% | 0.69 | 3 | -5.2% | N/A | X | O | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2379 | double_volume | -0.7% | 0.63 | 3 | -6.7% | N/A | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 9921 | double_volume | -1.0% | 0.63 | 6 | -12.1% | 0.14 | X | O | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 3045 | double_volume | -1.6% | 0.35 | 5 | -12.0% | 0.00 | X | O | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 5880 | double_volume | -1.9% | 0.18 | 9 | -18.2% | 0.03 | X | X | O | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2356 | double_volume | -2.0% | 0.51 | 10 | -29.2% | 0.11 | X | O | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 2105 | double_volume | -2.4% | 0.25 | 11 | -25.3% | 0.00 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 1101 | double_volume | -3.4% | 0.00 | 8 | -24.7% | 0.00 | X | O | X | FAIL：test expectancy=-3.4% < 0（負期望值） |
| 2002 | double_volume | -3.5% | 0.16 | 6 | -21.5% | 0.00 | X | O | X | FAIL：test expectancy=-3.5% < 0（負期望值） |
| 2207 | double_volume | -4.4% | 0.07 | 19 | -58.1% | 0.00 | X | X | X | FAIL：test expectancy=-4.4% < 0（負期望值） |
| 1227 | double_volume | -4.5% | 0.00 | 1 | -9.5% | N/A | X | X | X | FAIL：test expectancy=-4.5% < 0（負期望值） |
| 9940 | double_volume | -4.6% | 0.00 | 7 | -28.4% | 0.00 | X | X | X | FAIL：test expectancy=-4.6% < 0（負期望值） |
| 2886 | double_volume | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
