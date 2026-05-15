# TIERING REPORT — 20260516_033741

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 1 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 13 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 15**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6188 | narrow_range_breakout | +3.9% | inf | 7 | -4.0% | 5.00 | X | X | O | PF_lower=5.00 ≥ 1.5, exp=+3.9% ≥ 3%, n=7≥6, holdout=[A_new=NA B=NA C=O], gate=any holdout PASS |

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 13 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2392 | narrow_range_breakout | +0.0% | 0.92 | 9 | -27.4% | 0.16 | X | X | X | FAIL：PF_lower=0.16, exp=+0.0%, n=9, holdout=[A_new=NA B=X C=NA] |
| 2855 | narrow_range_breakout | -0.4% | 0.82 | 6 | -23.0% | 0.00 | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 6510 | narrow_range_breakout | -1.7% | 0.57 | 22 | -46.2% | 0.23 | X | O | O | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2393 | narrow_range_breakout | -2.1% | 0.62 | 5 | -26.3% | 0.00 | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 9941 | narrow_range_breakout | -2.2% | 0.48 | 4 | -21.2% | N/A | X | X | O | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 1565 | narrow_range_breakout | -3.2% | 0.00 | 3 | -9.3% | N/A | X | X | X | FAIL：test expectancy=-3.2% < 0（負期望值） |
| 5522 | narrow_range_breakout | -3.5% | 0.54 | 5 | -29.9% | 0.00 | X | O | X | FAIL：test expectancy=-3.5% < 0（負期望值） |
| 2492 | narrow_range_breakout | -3.7% | 0.41 | 3 | -28.6% | N/A | X | O | X | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 2347 | narrow_range_breakout | -4.7% | 0.21 | 4 | -30.2% | N/A | X | O | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 5904 | narrow_range_breakout | -4.9% | 0.00 | 4 | -18.1% | N/A | X | X | O | FAIL：test expectancy=-4.9% < 0（負期望值） |
| 8016 | narrow_range_breakout | -5.3% | 0.25 | 3 | -27.9% | N/A | X | O | X | FAIL：test expectancy=-5.3% < 0（負期望值） |
| 4148 | narrow_range_breakout | -6.1% | 0.00 | 6 | -33.0% | 0.00 | X | O | O | FAIL：test expectancy=-6.1% < 0（負期望值） |
| 6804 | narrow_range_breakout | -39.6% | 0.00 | 3 | -100.0% | N/A | X | X | O | FAIL：test expectancy=-39.6% < 0（負期望值） |
