# TIERING REPORT — 20260516_064021

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 7 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 7**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 7 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2347 | linreg_slope_revert | +0.8% | 1.46 | 9 | -14.4% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+0.8%, n=9, holdout=[A_new=NA B=O C=X] |
| 2392 | linreg_slope_revert | +0.1% | 0.99 | 2 | -4.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1565 | linreg_slope_revert | -0.2% | 0.00 | 1 | -4.5% | N/A | X | X | O | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 5522 | linreg_slope_revert | -0.4% | 0.80 | 10 | -26.8% | 0.00 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 9941 | linreg_slope_revert | -1.0% | 0.13 | 41 | -34.6% | 0.04 | X | X | O | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 6804 | linreg_slope_revert | -25.2% | 0.01 | 4 | -100.0% | N/A | X | X | O | FAIL：test expectancy=-25.2% < 0（負期望值） |
| 5904 | linreg_slope_revert | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
