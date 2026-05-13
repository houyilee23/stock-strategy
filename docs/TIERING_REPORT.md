# TIERING REPORT — 20260513_091426

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 18 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 18**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 18 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2002 | volume_spike_reverse | +2.9% | 2.37 | 3 | -5.3% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2886 | volume_spike_reverse | +2.3% | inf | 4 | -2.6% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1227 | volume_spike_reverse | +0.7% | 1.47 | 3 | -5.1% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3045 | volume_spike_reverse | +0.2% | 1.14 | 8 | -11.2% | 0.18 | X | X | X | FAIL：PF_lower=0.18, exp=+0.2%, n=8, holdout=[A_new=NA B=NA C=X] |
| 2474 | volume_spike_reverse | +0.0% | 0.96 | 5 | -8.9% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+0.0%, n=5, holdout=[A_new=NA B=NA C=X] |
| 2207 | volume_spike_reverse | -0.6% | 0.59 | 27 | -18.0% | 0.21 | X | X | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 9940 | volume_spike_reverse | -0.7% | 0.55 | 3 | -4.8% | N/A | X | O | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2412 | volume_spike_reverse | -0.9% | 0.02 | 6 | -6.9% | 0.00 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2912 | volume_spike_reverse | -1.0% | 0.17 | 5 | -7.4% | 0.00 | X | O | X | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 1216 | volume_spike_reverse | -1.6% | 0.34 | 5 | -12.9% | 0.03 | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2324 | volume_spike_reverse | -3.0% | 0.10 | 5 | -20.1% | 0.00 | X | X | X | FAIL：test expectancy=-3.0% < 0（負期望值） |
| 1101 | volume_spike_reverse | -3.8% | 0.00 | 2 | -7.8% | N/A | X | X | X | FAIL：test expectancy=-3.8% < 0（負期望值） |
| 0056 | volume_spike_reverse | -4.7% | 0.00 | 3 | -13.8% | N/A | X | O | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 9921 | volume_spike_reverse | -5.3% | 0.00 | 1 | -6.5% | N/A | X | O | X | FAIL：test expectancy=-5.3% < 0（負期望值） |
| 2356 | volume_spike_reverse | -6.4% | 0.00 | 2 | -12.5% | N/A | X | X | X | FAIL：test expectancy=-6.4% < 0（負期望值） |
| 2105 | volume_spike_reverse | -10.4% | 0.00 | 1 | -10.4% | N/A | X | X | X | FAIL：test expectancy=-10.4% < 0（負期望值） |
| 2379 | volume_spike_reverse | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5880 | volume_spike_reverse | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
