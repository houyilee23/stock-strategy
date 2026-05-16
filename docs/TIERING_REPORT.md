# TIERING REPORT — 20260516_165821

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 2 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 3 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 59 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 5 / 66**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3661 | ensemble_oversold_vote | +13.1% | inf | 6 | -15.3% | 5.00 | X | O | O | PF_lower=5.00 ≥ 1.5, exp=+13.1% ≥ 3%, n=6≥6, holdout=[A_new=NA B=O C=O], gate=any holdout PASS |
| 3036 | ensemble_oversold_vote | +9.6% | 20.99 | 7 | -18.2% | 3.68 | X | X | O | PF_lower=3.68 ≥ 1.5, exp=+9.6% ≥ 3%, n=7≥6, holdout=[A_new=NA B=X C=O], gate=any holdout PASS |

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2308 | ensemble_oversold_vote | +12.6% | inf | 3 | -8.0% | N/A | X | X | O | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+12.6% ≥ 5%, |DD|=8% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |
| 8081 | ensemble_oversold_vote | +10.2% | inf | 3 | -11.7% | N/A | X | O | O | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+10.2% ≥ 5%, |DD|=12% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |
| 2354 | ensemble_oversold_vote | +6.8% | 31.81 | 3 | -10.9% | N/A | X | O | O | LOW_N_RESCUE：n=3, raw_PF=31.81 ≥ 3.0, exp=+6.8% ≥ 5%, |DD|=11% ≤ 25%, holdout=[A_new=NA B=O C=O]（紙上交易 3 個月） |

### Tier F — 部位上限 0% （共 59 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2609 | ensemble_oversold_vote | +20.4% | inf | 1 | -5.9% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6191 | ensemble_oversold_vote | +15.6% | inf | 1 | -2.0% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2327 | ensemble_oversold_vote | +13.6% | inf | 1 | -5.1% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2009 | ensemble_oversold_vote | +12.9% | inf | 2 | -9.1% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3231 | ensemble_oversold_vote | +11.3% | inf | 2 | -13.3% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4148 | ensemble_oversold_vote | +10.7% | inf | 2 | -20.4% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3324 | ensemble_oversold_vote | +10.1% | inf | 2 | -10.4% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2360 | ensemble_oversold_vote | +9.7% | inf | 2 | -5.9% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2881 | ensemble_oversold_vote | +9.2% | inf | 2 | -7.4% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2890 | ensemble_oversold_vote | +7.8% | inf | 1 | -6.3% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2603 | ensemble_oversold_vote | +7.7% | inf | 1 | -4.4% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 8341 | ensemble_oversold_vote | +7.0% | inf | 1 | -6.1% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3014 | ensemble_oversold_vote | +5.9% | inf | 2 | -9.7% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6116 | ensemble_oversold_vote | +5.2% | inf | 1 | -10.0% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3044 | ensemble_oversold_vote | +5.2% | inf | 2 | -10.1% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6271 | ensemble_oversold_vote | +4.8% | 158.37 | 4 | -16.0% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2892 | ensemble_oversold_vote | +4.7% | inf | 2 | -3.4% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2324 | ensemble_oversold_vote | +4.4% | inf | 3 | -8.8% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2812 | ensemble_oversold_vote | +4.4% | 5.52 | 4 | -7.2% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 8069 | ensemble_oversold_vote | +3.8% | 3.45 | 3 | -19.8% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2409 | ensemble_oversold_vote | +3.7% | 4.22 | 3 | -17.9% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3481 | ensemble_oversold_vote | +3.6% | inf | 3 | -11.2% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6491 | ensemble_oversold_vote | +3.5% | 6.90 | 4 | -7.2% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4938 | ensemble_oversold_vote | +3.3% | 7.26 | 3 | -4.2% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6443 | ensemble_oversold_vote | +3.2% | 1.78 | 3 | -26.7% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6533 | ensemble_oversold_vote | +3.1% | 122.37 | 3 | -14.5% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2891 | ensemble_oversold_vote | +3.1% | inf | 2 | -5.2% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2618 | ensemble_oversold_vote | +2.7% | 1.79 | 3 | -9.9% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1503 | ensemble_oversold_vote | +2.5% | 2.09 | 4 | -20.4% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2014 | ensemble_oversold_vote | +2.1% | 2.53 | 3 | -10.4% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2885 | ensemble_oversold_vote | +2.1% | 1.55 | 4 | -23.5% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2027 | ensemble_oversold_vote | +2.1% | 1.63 | 7 | -24.9% | 0.29 | X | X | X | FAIL：PF_lower=0.29, exp=+2.1%, n=7, holdout=[A_new=NA B=NA C=X] |
| 2887 | ensemble_oversold_vote | +2.0% | 5.14 | 3 | -9.8% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1907 | ensemble_oversold_vote | +1.9% | 2.06 | 6 | -20.5% | 0.30 | X | O | O | FAIL：PF_lower=0.30, exp=+1.9%, n=6, holdout=[A_new=NA B=O C=O] |
| 3596 | ensemble_oversold_vote | +1.7% | 1.90 | 4 | -14.4% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2820 | ensemble_oversold_vote | +1.6% | inf | 4 | -7.5% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1605 | ensemble_oversold_vote | +1.3% | 1.11 | 3 | -20.9% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2542 | ensemble_oversold_vote | +1.2% | 1.35 | 5 | -13.7% | 0.00 | X | O | O | FAIL：PF_lower=0.00, exp=+1.2%, n=5, holdout=[A_new=NA B=O C=O] |
| 9914 | ensemble_oversold_vote | -0.1% | 0.89 | 6 | -19.5% | 0.08 | X | O | O | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 3406 | ensemble_oversold_vote | -0.2% | 0.88 | 2 | -30.6% | N/A | X | O | O | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 1456 | ensemble_oversold_vote | -0.2% | 0.86 | 6 | -29.4% | 0.00 | X | X | O | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 1582 | ensemble_oversold_vote | -0.7% | 0.71 | 2 | -10.3% | N/A | X | O | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 6488 | ensemble_oversold_vote | -0.8% | 0.72 | 4 | -17.9% | N/A | X | O | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2049 | ensemble_oversold_vote | -0.8% | 0.75 | 2 | -26.9% | N/A | X | O | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 3034 | ensemble_oversold_vote | -1.1% | 0.56 | 5 | -13.5% | 0.01 | X | O | O | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2888 | ensemble_oversold_vote | -1.2% | 0.00 | 1 | -11.7% | N/A | X | X | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 3454 | ensemble_oversold_vote | -2.5% | 0.38 | 6 | -31.5% | 0.00 | X | O | O | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 1789 | ensemble_oversold_vote | -4.2% | 0.36 | 3 | -21.5% | N/A | X | O | X | FAIL：test expectancy=-4.2% < 0（負期望值） |
| 6505 | ensemble_oversold_vote | -4.2% | 0.26 | 3 | -16.8% | N/A | X | X | X | FAIL：test expectancy=-4.2% < 0（負期望值） |
| 5347 | ensemble_oversold_vote | -4.2% | 0.36 | 2 | -27.7% | N/A | X | O | O | FAIL：test expectancy=-4.2% < 0（負期望值） |
| 2356 | ensemble_oversold_vote | -4.7% | 0.00 | 2 | -29.7% | N/A | X | O | X | FAIL：test expectancy=-4.7% < 0（負期望值） |
| 6526 | ensemble_oversold_vote | -5.0% | 0.34 | 4 | -35.1% | N/A | X | X | O | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 5314 | ensemble_oversold_vote | -6.6% | 0.33 | 5 | -46.8% | 0.00 | X | X | X | FAIL：test expectancy=-6.6% < 0（負期望值） |
| 2303 | ensemble_oversold_vote | -8.4% | 0.00 | 1 | -12.1% | N/A | X | X | O | FAIL：test expectancy=-8.4% < 0（負期望值） |
| 4763 | ensemble_oversold_vote | -12.0% | 0.18 | 3 | -42.4% | N/A | X | X | O | FAIL：test expectancy=-12.0% < 0（負期望值） |
| 6213 | ensemble_oversold_vote | -12.3% | 0.00 | 2 | -37.2% | N/A | X | O | O | FAIL：test expectancy=-12.3% < 0（負期望值） |
| 6531 | ensemble_oversold_vote | -17.2% | 0.00 | 1 | -23.6% | N/A | X | X | X | FAIL：test expectancy=-17.2% < 0（負期望值） |
| 1102 | ensemble_oversold_vote | N/A | inf | 0 | -0.0% | N/A | X | O | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2474 | ensemble_oversold_vote | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
