# TIERING REPORT — 20260515_195302

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 19 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 19**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 19 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2606 | hammer_revert | +8.7% | inf | 1 | -3.9% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2002 | hammer_revert | +3.0% | inf | 2 | -0.9% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2845 | hammer_revert | +1.3% | 1.66 | 4 | -8.0% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1234 | hammer_revert | -0.5% | 0.61 | 2 | -3.5% | N/A | X | X | O | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 5388 | hammer_revert | -0.8% | 0.51 | 3 | -5.3% | N/A | X | X | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 3045 | hammer_revert | -0.9% | 0.29 | 4 | -6.4% | N/A | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 3105 | hammer_revert | -1.8% | 0.00 | 1 | -3.8% | N/A | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2886 | hammer_revert | -2.0% | 0.00 | 3 | -5.9% | N/A | X | X | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 2458 | hammer_revert | -2.4% | 0.39 | 3 | -12.0% | N/A | X | O | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 1504 | hammer_revert | -2.8% | 0.02 | 3 | -13.0% | N/A | X | X | O | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 9921 | hammer_revert | -3.0% | 0.00 | 2 | -6.9% | N/A | X | O | O | FAIL：test expectancy=-3.0% < 0（負期望值） |
| 1722 | hammer_revert | -3.3% | 0.00 | 2 | -6.4% | N/A | X | O | O | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 1535 | hammer_revert | -3.5% | 0.00 | 2 | -8.1% | N/A | X | O | X | FAIL：test expectancy=-3.5% < 0（負期望值） |
| 8454 | hammer_revert | -3.8% | 0.00 | 4 | -14.6% | N/A | X | O | X | FAIL：test expectancy=-3.8% < 0（負期望值） |
| 2727 | hammer_revert | -4.0% | 0.00 | 1 | -4.2% | N/A | X | X | O | FAIL：test expectancy=-4.0% < 0（負期望值） |
| 4147 | hammer_revert | -5.0% | 0.28 | 3 | -20.1% | N/A | X | X | O | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 3533 | hammer_revert | -7.7% | 0.00 | 1 | -7.6% | N/A | X | O | O | FAIL：test expectancy=-7.7% < 0（負期望值） |
| 2867 | hammer_revert | -10.9% | 0.16 | 10 | -100.0% | 0.00 | X | X | X | FAIL：test expectancy=-10.9% < 0（負期望值） |
| 1314 | hammer_revert | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
