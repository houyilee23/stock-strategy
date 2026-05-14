# TIERING REPORT — 20260514_113442

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 23 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 23**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 23 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2371 | outside_day_engulf | +7.1% | inf | 2 | -7.3% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2014 | outside_day_engulf | +4.9% | inf | 2 | -4.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3481 | outside_day_engulf | +2.8% | 1.82 | 11 | -19.1% | 0.46 | X | X | X | FAIL：PF_lower=0.46, exp=+2.8%, n=11, holdout=[A_new=NA B=NA C=X] |
| 3045 | outside_day_engulf | +2.2% | inf | 1 | -0.4% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2227 | outside_day_engulf | +0.9% | 1.44 | 4 | -6.7% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2723 | outside_day_engulf | -0.1% | 0.89 | 7 | -12.8% | 0.00 | X | X | X | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 9933 | outside_day_engulf | -0.4% | 0.70 | 3 | -6.8% | N/A | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2609 | outside_day_engulf | -1.5% | 0.49 | 6 | -14.6% | 0.10 | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 5269 | outside_day_engulf | -1.7% | 0.58 | 7 | -32.1% | 0.00 | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2886 | outside_day_engulf | -1.7% | 0.12 | 4 | -6.7% | N/A | X | X | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2105 | outside_day_engulf | -2.2% | 0.41 | 7 | -20.0% | 0.00 | X | O | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 4961 | outside_day_engulf | -2.3% | 0.33 | 8 | -25.0% | 0.00 | X | O | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 1101 | outside_day_engulf | -2.6% | 0.00 | 2 | -6.1% | N/A | X | X | X | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 1227 | outside_day_engulf | -3.0% | 0.00 | 3 | -11.0% | N/A | X | X | X | FAIL：test expectancy=-3.0% < 0（負期望值） |
| 1521 | outside_day_engulf | -5.5% | 0.00 | 2 | -14.7% | N/A | X | X | X | FAIL：test expectancy=-5.5% < 0（負期望值） |
| 2458 | outside_day_engulf | -7.2% | 0.00 | 2 | -15.2% | N/A | X | X | X | FAIL：test expectancy=-7.2% < 0（負期望值） |
| 0056 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2823 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2867 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2912 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5876 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5880 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9940 | outside_day_engulf | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
