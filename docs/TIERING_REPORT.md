# TIERING REPORT — 20260513_195021

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 12 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 12**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 12 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2886 | yearly_high_break | +2.3% | 1.51 | 8 | -22.5% | 0.26 | X | O | X | FAIL：PF_lower=0.26, exp=+2.3%, n=8, holdout=[A_new=NA B=O C=X] |
| 2105 | yearly_high_break | +2.0% | 2.13 | 8 | -10.6% | 0.49 | X | X | O | FAIL：PF_lower=0.49, exp=+2.0%, n=8, holdout=[A_new=NA B=NA C=O] |
| 2002 | yearly_high_break | +0.6% | 1.04 | 4 | -17.2% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5880 | yearly_high_break | +0.1% | 0.98 | 5 | -7.6% | 0.00 | X | X | O | FAIL：PF_lower=0.00, exp=+0.1%, n=5, holdout=[A_new=NA B=X C=O] |
| 0056 | yearly_high_break | -0.5% | 0.77 | 11 | -25.8% | 0.00 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 2474 | yearly_high_break | -3.3% | 0.18 | 3 | -14.7% | N/A | X | X | X | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 1101 | yearly_high_break | -3.6% | 0.42 | 3 | -18.3% | N/A | X | O | X | FAIL：test expectancy=-3.6% < 0（負期望值） |
| 3045 | yearly_high_break | -4.1% | 0.00 | 1 | -4.1% | N/A | X | X | X | FAIL：test expectancy=-4.1% < 0（負期望值） |
| 1227 | yearly_high_break | -4.7% | 0.00 | 1 | -10.1% | N/A | X | X | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 9940 | yearly_high_break | -5.0% | 0.18 | 6 | -27.5% | 0.00 | X | O | X | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 2912 | yearly_high_break | -6.6% | 0.00 | 1 | -6.6% | N/A | X | O | X | FAIL：test expectancy=-6.6% < 0（負期望值） |
| 9921 | yearly_high_break | -11.9% | 0.00 | 2 | -27.8% | N/A | X | X | X | FAIL：test expectancy=-11.9% < 0（負期望值） |
