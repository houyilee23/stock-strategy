# TIERING REPORT — 20260516_213439

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 33 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 35**  （目標 ≥ 20）

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
| 2308 | ensemble_oversold_vote | +12.6% | inf | 3 | -8.0% | N/A | X | X | O | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+12.6% ≥ 5%, |DD|=8% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |

### Tier F — 部位上限 0% （共 33 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 5536 | ensemble_oversold_vote | +21.9% | inf | 1 | -1.5% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3653 | ensemble_oversold_vote | +15.7% | inf | 2 | -0.4% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2383 | ensemble_oversold_vote | +14.8% | inf | 2 | -9.9% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2379 | ensemble_oversold_vote | +14.4% | inf | 2 | -2.9% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2615 | ensemble_oversold_vote | +13.8% | inf | 1 | -3.4% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2454 | ensemble_oversold_vote | +13.8% | inf | 2 | -3.4% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3702 | ensemble_oversold_vote | +13.0% | inf | 1 | -6.4% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2426 | ensemble_oversold_vote | +9.8% | inf | 2 | -8.0% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3081 | ensemble_oversold_vote | +9.7% | inf | 2 | -3.8% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2345 | ensemble_oversold_vote | +8.6% | inf | 1 | -6.5% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2059 | ensemble_oversold_vote | +8.5% | inf | 2 | -3.6% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5269 | ensemble_oversold_vote | +5.7% | inf | 1 | -0.0% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2451 | ensemble_oversold_vote | +4.9% | 3.25 | 3 | -13.1% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2882 | ensemble_oversold_vote | +4.3% | inf | 3 | -8.5% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3189 | ensemble_oversold_vote | +4.0% | 3.97 | 3 | -28.3% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2207 | ensemble_oversold_vote | +3.9% | inf | 2 | -5.3% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3035 | ensemble_oversold_vote | +2.8% | 2.51 | 5 | -14.2% | 0.00 | X | O | X | FAIL：PF_lower=0.00, exp=+2.8%, n=5, holdout=[A_new=NA B=O C=NA] |
| 6182 | ensemble_oversold_vote | +2.7% | 3.49 | 4 | -7.1% | N/A | X | O | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2887 | ensemble_oversold_vote | +2.0% | 5.14 | 3 | -9.8% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9933 | ensemble_oversold_vote | +2.0% | 1.79 | 3 | -100.0% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6515 | ensemble_oversold_vote | +1.4% | 1.31 | 10 | -45.4% | 0.39 | X | X | O | FAIL：PF_lower=0.39, exp=+1.4%, n=10, holdout=[A_new=NA B=NA C=O] |
| 6770 | ensemble_oversold_vote | +0.3% | 0.97 | 8 | -25.4% | 0.13 | X | X | X | FAIL：PF_lower=0.13, exp=+0.3%, n=8, holdout=[A_new=NA B=NA C=X] |
| 2049 | ensemble_oversold_vote | -0.9% | 0.74 | 2 | -26.9% | N/A | X | O | O | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2393 | ensemble_oversold_vote | -1.2% | 0.60 | 3 | -20.8% | N/A | X | X | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 6669 | ensemble_oversold_vote | -1.2% | 0.69 | 6 | -39.4% | 0.11 | X | X | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 8016 | ensemble_oversold_vote | -1.7% | 0.54 | 4 | -27.3% | N/A | X | O | X | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 2412 | ensemble_oversold_vote | -1.9% | 0.00 | 1 | -3.4% | N/A | X | O | X | FAIL：test expectancy=-1.9% < 0（負期望值） |
| 9907 | ensemble_oversold_vote | -2.0% | 0.42 | 2 | -11.6% | N/A | X | X | O | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 4915 | ensemble_oversold_vote | -2.3% | 0.00 | 2 | -17.7% | N/A | X | O | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 1326 | ensemble_oversold_vote | -3.6% | 0.26 | 7 | -31.7% | 0.04 | X | X | X | FAIL：test expectancy=-3.6% < 0（負期望值） |
| 2344 | ensemble_oversold_vote | -4.8% | 0.26 | 4 | -29.3% | N/A | X | O | X | FAIL：test expectancy=-4.8% < 0（負期望值） |
| 1216 | ensemble_oversold_vote | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1736 | ensemble_oversold_vote | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
