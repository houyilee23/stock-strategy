# TIERING REPORT — 20260515_134309

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 23 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 24**  （目標 ≥ 20）

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
| 2354 | three_day_reversal | +4.9% | 4.18 | 5 | -10.0% | 0.84 | X | X | X | PF_lower=0.84 ≥ 0.7, exp=+4.9% ≥ 1%, n=5≥5, holdout=[A_new=NA B=X C=NA] |

### Tier F — 部位上限 0% （共 23 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6446 | three_day_reversal | +10.0% | inf | 2 | -5.8% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2722 | three_day_reversal | +9.2% | inf | 1 | -0.0% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5483 | three_day_reversal | +7.0% | inf | 2 | -9.7% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2723 | three_day_reversal | +5.4% | inf | 1 | -0.1% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9940 | three_day_reversal | +2.3% | inf | 1 | -0.8% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2105 | three_day_reversal | -0.1% | 0.91 | 10 | -24.2% | 0.17 | X | X | O | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 2845 | three_day_reversal | -1.3% | 0.66 | 7 | -26.4% | 0.00 | X | X | O | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 5880 | three_day_reversal | -1.6% | 0.00 | 3 | -5.2% | N/A | X | O | O | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 5876 | three_day_reversal | -1.9% | 0.00 | 1 | -3.6% | N/A | X | O | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 2867 | three_day_reversal | -2.1% | 0.25 | 6 | -14.3% | 0.00 | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2015 | three_day_reversal | -5.0% | 0.11 | 6 | -32.6% | 0.00 | X | O | X | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 1101 | three_day_reversal | -5.1% | 0.00 | 2 | -10.7% | N/A | X | O | X | FAIL：test expectancy=-5.1% < 0（負期望值） |
| 1227 | three_day_reversal | -5.1% | 0.00 | 4 | -21.4% | N/A | X | X | X | FAIL：test expectancy=-5.1% < 0（負期望值） |
| 2227 | three_day_reversal | -5.9% | 0.13 | 5 | -28.4% | 0.00 | X | O | X | FAIL：test expectancy=-5.9% < 0（負期望值） |
| 4961 | three_day_reversal | -7.2% | 0.00 | 1 | -9.7% | N/A | X | O | X | FAIL：test expectancy=-7.2% < 0（負期望值） |
| 2371 | three_day_reversal | -9.3% | 0.00 | 1 | -9.3% | N/A | X | X | X | FAIL：test expectancy=-9.3% < 0（負期望值） |
| 5269 | three_day_reversal | -10.8% | 0.00 | 1 | -11.0% | N/A | X | O | X | FAIL：test expectancy=-10.8% < 0（負期望值） |
| 4174 | three_day_reversal | -13.5% | 0.00 | 3 | -36.2% | N/A | X | X | O | FAIL：test expectancy=-13.5% < 0（負期望值） |
| 1521 | three_day_reversal | -25.1% | 0.06 | 4 | -100.0% | N/A | X | X | O | FAIL：test expectancy=-25.1% < 0（負期望值） |
| 1535 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2823 | three_day_reversal | N/A | inf | 0 | -N/A | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2912 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 4137 | three_day_reversal | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
