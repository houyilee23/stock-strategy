# TIERING REPORT — 20260516_081220

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 2 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 8 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 2 / 10**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 5536 | chip_momentum | +17.3% | 6.50 | 9 | -34.9% | 0.98 | X | O | X | PF_lower=0.98 ≥ 0.7, exp=+17.3% ≥ 1%, n=9≥5, holdout=[A_new=NA B=O C=X] |
| 6443 | chip_momentum | +10.6% | 3.20 | 7 | -21.0% | 0.00 | X | X | O | C_HIGH_Q_RESCUE：n=7, raw_PF=3.20 ≥ 3.0, exp=+10.6% ≥ 5%, |DD|=21% ≤ 25%, holdout=[A_new=NA B=NA C=O]（小樣本高品質訊號，紙上交易 3 個月） |

### Tier F — 部位上限 0% （共 8 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2367 | chip_momentum | +1.0% | 1.38 | 17 | -19.1% | 0.45 | X | X | O | FAIL：PF_lower=0.45, exp=+1.0%, n=17, holdout=[A_new=NA B=X C=O] |
| 3526 | chip_momentum | +0.9% | 1.36 | 5 | -13.5% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+0.9%, n=5, holdout=[A_new=NA B=NA C=X] |
| 3324 | chip_momentum | +0.0% | 0.84 | 19 | -59.1% | 0.09 | X | X | X | FAIL：PF_lower=0.09, exp=+0.0%, n=19, holdout=[A_new=NA B=X C=X] |
| 1909 | chip_momentum | -2.1% | 0.00 | 3 | -6.3% | N/A | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 9904 | chip_momentum | -2.1% | 0.18 | 4 | -10.1% | N/A | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 6526 | chip_momentum | -2.9% | 0.40 | 15 | -48.7% | 0.01 | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2455 | chip_momentum | -7.0% | 0.00 | 7 | -42.2% | 0.00 | X | O | X | FAIL：test expectancy=-7.0% < 0（負期望值） |
| 8341 | chip_momentum | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
