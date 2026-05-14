# TIERING REPORT — 20260515_020559

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 32 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 32**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 32 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1314 | trend_confirm_hold | +9.5% | 3.59 | 2 | -11.4% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4915 | trend_confirm_hold | +8.9% | 5.82 | 2 | -15.1% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2867 | trend_confirm_hold | +4.3% | 2.49 | 3 | -15.4% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2354 | trend_confirm_hold | +4.3% | inf | 2 | -2.9% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 0056 | trend_confirm_hold | +2.5% | 2.02 | 2 | -7.3% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5269 | trend_confirm_hold | +1.7% | 1.27 | 2 | -11.7% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2371 | trend_confirm_hold | +1.0% | 1.04 | 2 | -11.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2014 | trend_confirm_hold | -0.2% | 0.83 | 3 | -26.7% | N/A | X | O | O | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 2015 | trend_confirm_hold | -1.2% | 0.00 | 1 | -7.0% | N/A | X | O | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 6446 | trend_confirm_hold | -1.3% | 0.61 | 3 | -17.3% | N/A | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2723 | trend_confirm_hold | -1.5% | 0.65 | 2 | -11.5% | N/A | X | X | X | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 2105 | trend_confirm_hold | -2.4% | 0.62 | 3 | -23.5% | N/A | X | X | O | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 2886 | trend_confirm_hold | -2.6% | 0.47 | 3 | -17.5% | N/A | X | X | X | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 2912 | trend_confirm_hold | -3.5% | 0.00 | 1 | -5.1% | N/A | X | X | O | FAIL：test expectancy=-3.5% < 0（負期望值） |
| 2227 | trend_confirm_hold | -4.6% | 0.00 | 1 | -5.7% | N/A | X | X | X | FAIL：test expectancy=-4.6% < 0（負期望值） |
| 5880 | trend_confirm_hold | -4.7% | 0.00 | 2 | -10.7% | N/A | X | X | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 4137 | trend_confirm_hold | -4.9% | 0.00 | 2 | -9.7% | N/A | X | X | X | FAIL：test expectancy=-4.9% < 0（負期望值） |
| 1227 | trend_confirm_hold | -4.9% | 0.00 | 1 | -8.3% | N/A | X | X | X | FAIL：test expectancy=-4.9% < 0（負期望值） |
| 2845 | trend_confirm_hold | -5.6% | 0.00 | 3 | -18.6% | N/A | X | X | X | FAIL：test expectancy=-5.6% < 0（負期望值） |
| 1101 | trend_confirm_hold | -5.8% | 0.00 | 2 | -15.8% | N/A | X | X | X | FAIL：test expectancy=-5.8% < 0（負期望值） |
| 1535 | trend_confirm_hold | -6.0% | 0.00 | 2 | -12.5% | N/A | X | X | O | FAIL：test expectancy=-6.0% < 0（負期望值） |
| 6533 | trend_confirm_hold | -7.0% | 0.00 | 2 | -17.1% | N/A | X | O | X | FAIL：test expectancy=-7.0% < 0（負期望值） |
| 5483 | trend_confirm_hold | -8.9% | 0.00 | 2 | -23.4% | N/A | X | X | X | FAIL：test expectancy=-8.9% < 0（負期望值） |
| 2451 | trend_confirm_hold | -9.3% | 0.00 | 1 | -11.5% | N/A | X | X | X | FAIL：test expectancy=-9.3% < 0（負期望值） |
| 1521 | trend_confirm_hold | -10.7% | 0.00 | 1 | -10.7% | N/A | X | X | X | FAIL：test expectancy=-10.7% < 0（負期望值） |
| 4961 | trend_confirm_hold | -10.9% | 0.00 | 2 | -22.8% | N/A | X | X | X | FAIL：test expectancy=-10.9% < 0（負期望值） |
| 2722 | trend_confirm_hold | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2823 | trend_confirm_hold | N/A | inf | 0 | -N/A | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 4174 | trend_confirm_hold | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5876 | trend_confirm_hold | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9933 | trend_confirm_hold | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 9940 | trend_confirm_hold | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
