# TIERING REPORT — 20260513_074009

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 18 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 19**  （目標 ≥ 20）

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
| 2881 | three_white_soldiers | +7.4% | inf | 3 | -8.9% | N/A | X | X | X | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+7.4% ≥ 5%, |DD|=9% ≤ 25%, holdout=[A_new=NA B=NA C=NA]（紙上交易 3 個月） |

### Tier F — 部位上限 0% （共 18 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2886 | three_white_soldiers | +3.0% | 21.48 | 3 | -4.4% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1216 | three_white_soldiers | +0.1% | 1.47 | 3 | -2.8% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2207 | three_white_soldiers | +0.1% | 0.97 | 8 | -12.2% | 0.05 | X | X | O | FAIL：PF_lower=0.05, exp=+0.1%, n=8, holdout=[A_new=NA B=NA C=O] |
| 2105 | three_white_soldiers | -0.4% | 0.84 | 2 | -12.1% | N/A | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 0056 | three_white_soldiers | -1.7% | 0.22 | 6 | -12.7% | 0.00 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2324 | three_white_soldiers | -2.8% | 0.34 | 3 | -9.0% | N/A | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 1101 | three_white_soldiers | -2.9% | 0.00 | 1 | -3.5% | N/A | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2379 | three_white_soldiers | -3.3% | 0.38 | 4 | -22.1% | N/A | X | O | X | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 2912 | three_white_soldiers | -3.4% | 0.00 | 1 | -3.4% | N/A | X | O | X | FAIL：test expectancy=-3.4% < 0（負期望值） |
| 2474 | three_white_soldiers | -4.5% | 0.00 | 4 | -17.1% | N/A | X | X | X | FAIL：test expectancy=-4.5% < 0（負期望值） |
| 9921 | three_white_soldiers | -5.5% | 0.00 | 4 | -20.2% | N/A | X | O | X | FAIL：test expectancy=-5.5% < 0（負期望值） |
| 1227 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2002 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2356 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2412 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3045 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5880 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9940 | three_white_soldiers | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
