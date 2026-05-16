# TIERING REPORT — 20260517_034627

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 45 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 45**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 45 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 5522 | ensemble_breakout_pullback | +10.8% | inf | 2 | -4.1% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2880 | ensemble_breakout_pullback | +9.4% | inf | 1 | -6.8% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5388 | ensemble_breakout_pullback | +8.3% | 9.32 | 2 | -19.3% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2845 | ensemble_breakout_pullback | +8.2% | inf | 2 | -10.9% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2723 | ensemble_breakout_pullback | +6.9% | inf | 1 | -9.5% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3045 | ensemble_breakout_pullback | +3.8% | inf | 4 | -3.8% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5483 | ensemble_breakout_pullback | +3.2% | 2.32 | 4 | -14.0% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2867 | ensemble_breakout_pullback | +3.1% | 1.68 | 3 | -17.7% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5904 | ensemble_breakout_pullback | +1.9% | inf | 1 | -7.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9904 | ensemble_breakout_pullback | +1.3% | inf | 1 | -6.5% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2886 | ensemble_breakout_pullback | +0.7% | 1.26 | 7 | -13.5% | 0.20 | X | O | X | FAIL：PF_lower=0.20, exp=+0.7%, n=7, holdout=[A_new=NA B=O C=X] |
| 2367 | ensemble_breakout_pullback | -0.1% | 0.90 | 5 | -20.3% | 0.00 | X | O | O | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 2855 | ensemble_breakout_pullback | -1.5% | 0.61 | 2 | -9.2% | N/A | X | O | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 2105 | ensemble_breakout_pullback | -1.9% | 0.64 | 4 | -20.9% | N/A | X | X | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 1227 | ensemble_breakout_pullback | -2.1% | 0.00 | 3 | -8.8% | N/A | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 1909 | ensemble_breakout_pullback | -2.1% | 0.39 | 4 | -13.2% | N/A | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 1535 | ensemble_breakout_pullback | -2.2% | 0.00 | 1 | -6.4% | N/A | X | X | O | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 1234 | ensemble_breakout_pullback | -2.2% | 0.00 | 3 | -7.4% | N/A | X | X | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 1722 | ensemble_breakout_pullback | -2.3% | 0.05 | 2 | -8.7% | N/A | X | X | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 2722 | ensemble_breakout_pullback | -2.3% | 0.44 | 5 | -13.6% | 0.00 | X | X | O | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 3105 | ensemble_breakout_pullback | -3.0% | 0.30 | 4 | -17.9% | N/A | X | X | X | FAIL：test expectancy=-3.0% < 0（負期望值） |
| 1521 | ensemble_breakout_pullback | -3.1% | 0.10 | 3 | -12.2% | N/A | X | X | X | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 2458 | ensemble_breakout_pullback | -5.3% | 0.00 | 6 | -30.3% | 0.00 | X | X | X | FAIL：test expectancy=-5.3% < 0（負期望值） |
| 2015 | ensemble_breakout_pullback | -5.4% | 0.00 | 2 | -12.8% | N/A | X | O | X | FAIL：test expectancy=-5.4% < 0（負期望值） |
| 6446 | ensemble_breakout_pullback | -6.2% | 0.00 | 1 | -6.2% | N/A | X | X | O | FAIL：test expectancy=-6.2% < 0（負期望值） |
| 5876 | ensemble_breakout_pullback | -6.4% | 0.00 | 1 | -7.5% | N/A | X | O | O | FAIL：test expectancy=-6.4% < 0（負期望值） |
| 1101 | ensemble_breakout_pullback | -6.5% | 0.00 | 1 | -6.9% | N/A | X | O | X | FAIL：test expectancy=-6.5% < 0（負期望值） |
| 1504 | ensemble_breakout_pullback | -7.1% | 0.00 | 1 | -7.1% | N/A | X | X | X | FAIL：test expectancy=-7.1% < 0（負期望值） |
| 3533 | ensemble_breakout_pullback | -7.6% | 0.00 | 2 | -17.1% | N/A | X | X | O | FAIL：test expectancy=-7.6% < 0（負期望值） |
| 4961 | ensemble_breakout_pullback | -8.1% | 0.00 | 3 | -25.5% | N/A | X | O | X | FAIL：test expectancy=-8.1% < 0（負期望值） |
| 4174 | ensemble_breakout_pullback | -8.5% | 0.00 | 1 | -8.6% | N/A | X | X | O | FAIL：test expectancy=-8.5% < 0（負期望值） |
| 2371 | ensemble_breakout_pullback | -8.7% | 0.00 | 1 | -9.7% | N/A | X | X | O | FAIL：test expectancy=-8.7% < 0（負期望值） |
| 2606 | ensemble_breakout_pullback | -10.7% | 0.00 | 3 | -37.8% | N/A | X | X | O | FAIL：test expectancy=-10.7% < 0（負期望值） |
| 2392 | ensemble_breakout_pullback | -16.4% | 0.13 | 8 | -100.0% | 0.00 | X | X | X | FAIL：test expectancy=-16.4% < 0（負期望值） |
| 1565 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2227 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2823 | ensemble_breakout_pullback | N/A | inf | 0 | -N/A | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2912 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 4137 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5880 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6804 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 8454 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9921 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9940 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9941 | ensemble_breakout_pullback | N/A | inf | 0 | -0.0% | N/A | X | O | O | FAIL：test expectancy=-inf% < 0（負期望值） |
