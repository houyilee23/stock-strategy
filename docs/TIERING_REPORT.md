# TIERING REPORT — 20260517_094608

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 1 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 4 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 58 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 5 / 64**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6488 | ensemble_triple_confirm | +7.3% | 8.91 | 8 | -15.1% | 1.68 | X | O | X | PF_lower=1.68 ≥ 1.5, exp=+7.3% ≥ 3%, n=8≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 4 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6443 | ensemble_triple_confirm | +8.7% | inf | 3 | -8.7% | N/A | X | X | O | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+8.7% ≥ 5%, |DD|=9% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |
| 2360 | ensemble_triple_confirm | +6.5% | 2.84 | 7 | -17.3% | 0.71 | X | O | O | PF_lower=0.71 ≥ 0.7, exp=+6.5% ≥ 1%, n=7≥5, holdout=[A_new=NA B=O C=O] |
| 3526 | ensemble_triple_confirm | +3.0% | 3.01 | 10 | -13.5% | 0.98 | X | O | O | PF_lower=0.98 ≥ 0.7, exp=+3.0% ≥ 1%, n=10≥5, holdout=[A_new=NA B=O C=O] |
| 2327 | ensemble_triple_confirm | +2.7% | 1.77 | 13 | -15.4% | 0.70 | X | O | X | PF_lower=0.70 ≥ 0.7, exp=+2.7% ≥ 1%, n=13≥5, holdout=[A_new=NA B=O C=X] |

### Tier F — 部位上限 0% （共 58 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3044 | ensemble_bullish_divergence | +9.4% | inf | 2 | -4.3% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4763 | ensemble_bullish_divergence | +6.7% | inf | 1 | -3.5% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6271 | ensemble_bullish_divergence | +5.2% | 4.09 | 2 | -10.0% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 8069 | ensemble_bullish_divergence | +5.2% | inf | 2 | -4.6% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3481 | ensemble_bullish_divergence | +4.8% | inf | 1 | -0.9% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1503 | ensemble_bullish_divergence | +4.8% | inf | 3 | -8.0% | N/A | X | X | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2880 | ensemble_bullish_divergence | +4.7% | inf | 4 | -4.6% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9914 | ensemble_triple_confirm | +4.6% | inf | 2 | -11.5% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2890 | ensemble_bullish_divergence | +4.3% | inf | 2 | -3.0% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2884 | ensemble_bullish_divergence | +4.2% | 22.32 | 2 | -3.0% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3324 | ensemble_triple_confirm | +3.5% | 1.74 | 5 | -29.1% | 0.33 | X | O | O | FAIL：PF_lower=0.33, exp=+3.5%, n=5, holdout=[A_new=NA B=O C=O] |
| 2885 | ensemble_triple_confirm | +3.3% | 1.81 | 9 | -22.5% | 0.43 | X | O | X | FAIL：PF_lower=0.43, exp=+3.3%, n=9, holdout=[A_new=NA B=O C=NA] |
| 2812 | ensemble_triple_confirm | +3.2% | 2.00 | 7 | -11.9% | 0.36 | X | O | O | FAIL：PF_lower=0.36, exp=+3.2%, n=7, holdout=[A_new=NA B=O C=O] |
| 3406 | ensemble_bullish_divergence | +3.2% | 1.74 | 3 | -10.2% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2609 | ensemble_bullish_divergence | +3.1% | 2.15 | 4 | -10.3% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1907 | ensemble_bullish_divergence | +2.9% | 18.31 | 3 | -6.3% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2727 | ensemble_bullish_divergence | +2.8% | inf | 2 | -1.8% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2888 | ensemble_bullish_divergence | +2.7% | 1.92 | 2 | -9.5% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6191 | ensemble_triple_confirm | +2.5% | 1.80 | 11 | -17.8% | 0.44 | X | O | O | FAIL：PF_lower=0.44, exp=+2.5%, n=11, holdout=[A_new=NA B=O C=O] |
| 6531 | ensemble_triple_confirm | +2.2% | 1.55 | 10 | -19.3% | 0.46 | X | O | X | FAIL：PF_lower=0.46, exp=+2.2%, n=10, holdout=[A_new=NA B=O C=X] |
| 6533 | ensemble_bullish_divergence | +2.1% | 1.94 | 4 | -9.4% | N/A | X | X | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2881 | ensemble_triple_confirm | +1.9% | 2.32 | 7 | -7.4% | 0.35 | X | X | O | FAIL：PF_lower=0.35, exp=+1.9%, n=7, holdout=[A_new=NA B=X C=O] |
| 2009 | ensemble_triple_confirm | +1.7% | 1.14 | 6 | -24.3% | 0.31 | X | X | X | FAIL：PF_lower=0.31, exp=+1.7%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 2892 | ensemble_bullish_divergence | +1.5% | inf | 2 | -3.6% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 00878 | ensemble_triple_confirm | +1.2% | 1.78 | 5 | -11.4% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.2%, n=5, holdout=[A_new=NA B=NA C=NA] |
| 2027 | ensemble_bullish_divergence | +1.2% | 2.75 | 2 | -7.1% | N/A | X | O | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2409 | ensemble_triple_confirm | +1.1% | 1.13 | 7 | -24.3% | 0.18 | X | X | X | FAIL：PF_lower=0.18, exp=+1.1%, n=7, holdout=[A_new=NA B=X C=X] |
| 4938 | ensemble_triple_confirm | +0.5% | 1.12 | 4 | -8.9% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6505 | ensemble_triple_confirm | +0.2% | 0.96 | 9 | -22.8% | 0.26 | X | O | X | FAIL：PF_lower=0.26, exp=+0.2%, n=9, holdout=[A_new=NA B=O C=X] |
| 8081 | ensemble_bullish_divergence | +0.2% | 0.98 | 3 | -12.1% | N/A | X | O | O | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3034 | ensemble_bullish_divergence | +0.1% | 0.98 | 5 | -11.1% | 0.00 | X | O | O | FAIL：PF_lower=0.00, exp=+0.1%, n=5, holdout=[A_new=NA B=O C=O] |
| 5314 | ensemble_triple_confirm | -0.0% | 0.62 | 13 | -100.0% | 0.28 | X | X | X | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 2603 | ensemble_bullish_divergence | -0.2% | 0.87 | 4 | -12.5% | N/A | X | O | X | FAIL：test expectancy=-0.2% < 0（負期望值） |
| 2354 | ensemble_bullish_divergence | -0.5% | 0.74 | 3 | -11.8% | N/A | X | O | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 6213 | ensemble_triple_confirm | -0.6% | 0.81 | 9 | -23.8% | 0.14 | X | O | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2820 | ensemble_bullish_divergence | -0.6% | 0.54 | 2 | -5.4% | N/A | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 3231 | ensemble_triple_confirm | -0.7% | 0.79 | 8 | -23.2% | 0.24 | X | X | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 6491 | ensemble_bullish_divergence | -0.8% | 0.71 | 5 | -18.9% | 0.00 | X | X | O | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 6526 | ensemble_triple_confirm | -0.8% | 0.75 | 10 | -42.1% | 0.14 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 3596 | ensemble_bullish_divergence | -0.9% | 0.73 | 4 | -16.9% | N/A | X | X | O | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 1605 | ensemble_triple_confirm | -1.2% | 0.69 | 8 | -35.5% | 0.13 | X | O | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2855 | ensemble_triple_confirm | -1.3% | 0.64 | 8 | -28.5% | 0.10 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2542 | ensemble_triple_confirm | -1.3% | 0.67 | 10 | -29.3% | 0.12 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 5347 | ensemble_bullish_divergence | -1.7% | 0.56 | 2 | -14.4% | N/A | X | O | O | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 1102 | ensemble_triple_confirm | -1.8% | 0.60 | 8 | -26.6% | 0.00 | X | O | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2356 | ensemble_triple_confirm | -2.4% | 0.48 | 11 | -35.7% | 0.09 | X | O | O | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 2618 | ensemble_triple_confirm | -2.6% | 0.29 | 8 | -19.5% | 0.00 | X | O | O | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 3014 | ensemble_triple_confirm | -2.6% | 0.45 | 6 | -23.9% | 0.00 | X | X | O | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 1789 | ensemble_bullish_divergence | -2.8% | 0.00 | 3 | -13.6% | N/A | X | O | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 1314 | ensemble_bullish_divergence | -3.1% | 0.30 | 2 | -11.0% | N/A | X | O | O | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 8341 | ensemble_bullish_divergence | -3.1% | 0.00 | 2 | -7.1% | N/A | X | X | O | FAIL：test expectancy=-3.1% < 0（負期望值） |
| 2014 | ensemble_triple_confirm | -3.3% | 0.30 | 9 | -31.3% | 0.00 | X | X | O | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 6116 | ensemble_bullish_divergence | -3.7% | 0.33 | 3 | -22.5% | N/A | X | O | O | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 1456 | ensemble_triple_confirm | -4.0% | 0.35 | 6 | -34.8% | 0.00 | X | X | X | FAIL：test expectancy=-4.0% < 0（負期望值） |
| 2474 | ensemble_triple_confirm | -4.3% | 0.24 | 10 | -43.2% | 0.00 | X | X | O | FAIL：test expectancy=-4.3% < 0（負期望值） |
| 4148 | ensemble_bullish_divergence | -4.4% | 0.41 | 2 | -15.5% | N/A | X | X | O | FAIL：test expectancy=-4.4% < 0（負期望值） |
| 3454 | ensemble_triple_confirm | -4.8% | 0.26 | 5 | -24.1% | 0.00 | X | O | O | FAIL：test expectancy=-4.8% < 0（負期望值） |
| 2324 | ensemble_triple_confirm | -4.9% | 0.29 | 6 | -33.8% | 0.00 | X | X | X | FAIL：test expectancy=-4.9% < 0（負期望值） |
