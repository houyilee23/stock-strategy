# TIERING REPORT — 20260517_145429

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 5 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 74 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 5 / 83**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 5 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6443 | ensemble_triple_confirm | +8.7% | inf | 3 | -8.7% | N/A | X | X | O | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+8.7% ≥ 5%, |DD|=9% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |
| 1560 | ensemble_triple_confirm | +7.5% | 4.32 | 9 | -16.6% | 0.88 | X | X | O | PF_lower=0.88 ≥ 0.7, exp=+7.5% ≥ 1%, n=9≥5, holdout=[A_new=NA B=NA C=O] |
| 2408 | ensemble_triple_confirm | +6.6% | 1.81 | 15 | -43.2% | 0.87 | X | O | O | PF_lower=0.87 ≥ 0.7, exp=+6.6% ≥ 1%, n=15≥5, holdout=[A_new=NA B=O C=O] |
| 2360 | ensemble_triple_confirm | +6.5% | 2.84 | 7 | -17.3% | 0.71 | X | O | O | PF_lower=0.71 ≥ 0.7, exp=+6.5% ≥ 1%, n=7≥5, holdout=[A_new=NA B=O C=O] |
| 3526 | ensemble_triple_confirm | +3.0% | 3.01 | 10 | -13.5% | 0.98 | X | O | O | PF_lower=0.98 ≥ 0.7, exp=+3.0% ≥ 1%, n=10≥5, holdout=[A_new=NA B=O C=O] |

### Tier F — 部位上限 0% （共 74 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2330 | ensemble_triple_confirm | +11.4% | inf | 2 | -3.1% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 9914 | ensemble_triple_confirm | +4.6% | inf | 2 | -11.5% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 0056 | ensemble_triple_confirm | +4.1% | 4.54 | 3 | -7.8% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3324 | ensemble_triple_confirm | +3.5% | 1.74 | 5 | -29.1% | 0.33 | X | O | O | FAIL：PF_lower=0.33, exp=+3.5%, n=5, holdout=[A_new=NA B=O C=O] |
| 2885 | ensemble_triple_confirm | +3.3% | 1.81 | 9 | -22.5% | 0.43 | X | O | X | FAIL：PF_lower=0.43, exp=+3.3%, n=9, holdout=[A_new=NA B=O C=NA] |
| 2812 | ensemble_triple_confirm | +3.2% | 2.00 | 7 | -11.9% | 0.36 | X | O | O | FAIL：PF_lower=0.36, exp=+3.2%, n=7, holdout=[A_new=NA B=O C=O] |
| 1503 | ensemble_triple_confirm | +3.0% | 1.37 | 10 | -31.9% | 0.44 | X | O | O | FAIL：PF_lower=0.44, exp=+3.0%, n=10, holdout=[A_new=NA B=O C=O] |
| 3044 | ensemble_triple_confirm | +2.9% | 1.88 | 9 | -25.5% | 0.33 | X | X | X | FAIL：PF_lower=0.33, exp=+2.9%, n=9, holdout=[A_new=NA B=X C=X] |
| 2382 | ensemble_triple_confirm | +2.8% | 1.79 | 6 | -19.3% | 0.23 | X | X | X | FAIL：PF_lower=0.23, exp=+2.8%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 6191 | ensemble_triple_confirm | +2.5% | 1.80 | 11 | -17.8% | 0.44 | X | O | O | FAIL：PF_lower=0.44, exp=+2.5%, n=11, holdout=[A_new=NA B=O C=O] |
| 6531 | ensemble_triple_confirm | +2.2% | 1.55 | 10 | -19.3% | 0.46 | X | O | X | FAIL：PF_lower=0.46, exp=+2.2%, n=10, holdout=[A_new=NA B=O C=X] |
| 2881 | ensemble_triple_confirm | +1.9% | 2.32 | 7 | -7.4% | 0.35 | X | X | O | FAIL：PF_lower=0.35, exp=+1.9%, n=7, holdout=[A_new=NA B=X C=O] |
| 2009 | ensemble_triple_confirm | +1.7% | 1.14 | 6 | -24.3% | 0.31 | X | X | X | FAIL：PF_lower=0.31, exp=+1.7%, n=6, holdout=[A_new=NA B=NA C=NA] |
| 00878 | ensemble_triple_confirm | +1.2% | 1.78 | 5 | -11.4% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+1.2%, n=5, holdout=[A_new=NA B=NA C=NA] |
| 1402 | ensemble_triple_confirm | +1.1% | 1.21 | 6 | -27.4% | 0.17 | X | O | O | FAIL：PF_lower=0.17, exp=+1.1%, n=6, holdout=[A_new=NA B=O C=O] |
| 2880 | ensemble_triple_confirm | +1.1% | 1.18 | 7 | -17.8% | 0.33 | X | O | O | FAIL：PF_lower=0.33, exp=+1.1%, n=7, holdout=[A_new=NA B=O C=O] |
| 4938 | ensemble_triple_confirm | +0.5% | 1.12 | 4 | -8.9% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2890 | ensemble_triple_confirm | +0.4% | 1.00 | 10 | -26.0% | 0.26 | X | X | O | FAIL：PF_lower=0.26, exp=+0.4%, n=10, holdout=[A_new=NA B=X C=O] |
| 2027 | ensemble_triple_confirm | +0.3% | 0.99 | 7 | -23.5% | 0.17 | X | O | O | FAIL：PF_lower=0.17, exp=+0.3%, n=7, holdout=[A_new=NA B=O C=O] |
| 6533 | ensemble_triple_confirm | +0.3% | 1.05 | 10 | -12.6% | 0.33 | X | O | O | FAIL：PF_lower=0.33, exp=+0.3%, n=10, holdout=[A_new=NA B=O C=O] |
| 8069 | ensemble_triple_confirm | +0.3% | 0.99 | 6 | -18.5% | 0.20 | X | O | O | FAIL：PF_lower=0.20, exp=+0.3%, n=6, holdout=[A_new=NA B=O C=O] |
| 6505 | ensemble_triple_confirm | +0.2% | 0.96 | 9 | -22.8% | 0.26 | X | O | X | FAIL：PF_lower=0.26, exp=+0.2%, n=9, holdout=[A_new=NA B=O C=X] |
| 5314 | ensemble_triple_confirm | -0.0% | 0.62 | 13 | -100.0% | 0.28 | X | X | X | FAIL：test expectancy=-0.0% < 0（負期望值） |
| 00919 | ensemble_triple_confirm | -0.3% | 0.81 | 10 | -17.0% | 0.20 | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 8081 | ensemble_triple_confirm | -0.3% | 0.83 | 4 | -19.1% | N/A | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 4904 | ensemble_triple_confirm | -0.4% | 0.68 | 5 | -11.3% | 0.00 | X | X | O | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 6213 | ensemble_triple_confirm | -0.6% | 0.81 | 9 | -23.8% | 0.14 | X | O | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2892 | ensemble_triple_confirm | -0.6% | 0.71 | 7 | -12.9% | 0.00 | X | X | X | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 2884 | ensemble_triple_confirm | -0.7% | 0.71 | 5 | -19.9% | 0.00 | X | O | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 3231 | ensemble_triple_confirm | -0.7% | 0.79 | 8 | -23.2% | 0.24 | X | X | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 6526 | ensemble_triple_confirm | -0.8% | 0.75 | 10 | -42.1% | 0.14 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 6271 | ensemble_triple_confirm | -0.9% | 0.64 | 13 | -30.7% | 0.00 | X | O | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2883 | ensemble_triple_confirm | -1.1% | 0.62 | 12 | -25.7% | 0.17 | X | O | O | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2337 | ensemble_triple_confirm | -1.1% | 0.62 | 7 | -26.5% | 0.10 | X | O | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 4763 | ensemble_triple_confirm | -1.2% | 0.72 | 8 | -35.3% | 0.00 | X | O | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 1605 | ensemble_triple_confirm | -1.2% | 0.69 | 8 | -35.5% | 0.13 | X | O | O | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 2855 | ensemble_triple_confirm | -1.3% | 0.64 | 8 | -28.5% | 0.10 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 2542 | ensemble_triple_confirm | -1.3% | 0.67 | 10 | -29.3% | 0.12 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 3034 | ensemble_triple_confirm | -1.3% | 0.57 | 5 | -17.7% | 0.04 | X | O | O | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 3481 | ensemble_triple_confirm | -1.4% | 0.63 | 7 | -26.3% | 0.00 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 3711 | ensemble_triple_confirm | -1.4% | 0.66 | 10 | -30.9% | 0.16 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 3596 | ensemble_triple_confirm | -1.4% | 0.63 | 8 | -27.3% | 0.15 | X | O | O | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 3037 | ensemble_triple_confirm | -1.7% | 0.61 | 11 | -26.5% | 0.14 | X | O | O | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 1102 | ensemble_triple_confirm | -1.8% | 0.60 | 8 | -26.6% | 0.00 | X | O | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2369 | ensemble_triple_confirm | -2.0% | 0.56 | 13 | -36.9% | 0.00 | X | X | X | FAIL：test expectancy=-2.0% < 0（負期望值） |
| 2609 | ensemble_triple_confirm | -2.1% | 0.50 | 15 | -29.4% | 0.10 | X | X | O | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 5871 | ensemble_triple_confirm | -2.1% | 0.00 | 1 | -2.1% | N/A | X | X | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 3406 | ensemble_triple_confirm | -2.1% | 0.56 | 10 | -27.0% | 0.00 | X | O | X | FAIL：test expectancy=-2.1% < 0（負期望值） |
| 2002 | ensemble_triple_confirm | -2.3% | 0.40 | 9 | -27.0% | 0.00 | X | X | O | FAIL：test expectancy=-2.3% < 0（負期望值） |
| 2356 | ensemble_triple_confirm | -2.4% | 0.48 | 11 | -35.7% | 0.09 | X | O | O | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 2354 | ensemble_triple_confirm | -2.4% | 0.58 | 9 | -30.7% | 0.00 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 00940 | ensemble_triple_confirm | -2.5% | 0.16 | 4 | -11.5% | N/A | X | X | X | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 2618 | ensemble_triple_confirm | -2.6% | 0.29 | 8 | -19.5% | 0.00 | X | O | O | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 3014 | ensemble_triple_confirm | -2.6% | 0.45 | 6 | -23.9% | 0.00 | X | X | O | FAIL：test expectancy=-2.6% < 0（負期望值） |
| 2820 | ensemble_triple_confirm | -2.8% | 0.17 | 5 | -19.9% | 0.00 | X | X | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 2353 | ensemble_triple_confirm | -2.8% | 0.54 | 3 | -13.6% | N/A | X | O | X | FAIL：test expectancy=-2.8% < 0（負期望值） |
| 2727 | ensemble_triple_confirm | -2.9% | 0.20 | 7 | -24.0% | 0.00 | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2888 | ensemble_triple_confirm | -2.9% | 0.48 | 8 | -33.8% | 0.00 | X | O | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2376 | ensemble_triple_confirm | -3.0% | 0.52 | 9 | -50.8% | 0.00 | X | X | X | FAIL：test expectancy=-3.0% < 0（負期望值） |
| 2014 | ensemble_triple_confirm | -3.3% | 0.30 | 9 | -31.3% | 0.00 | X | X | O | FAIL：test expectancy=-3.3% < 0（負期望值） |
| 1789 | ensemble_triple_confirm | -3.7% | 0.22 | 6 | -23.7% | 0.00 | X | X | O | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 6491 | ensemble_triple_confirm | -3.7% | 0.21 | 7 | -32.9% | 0.00 | X | O | O | FAIL：test expectancy=-3.7% < 0（負期望值） |
| 1456 | ensemble_triple_confirm | -4.0% | 0.35 | 6 | -34.8% | 0.00 | X | X | X | FAIL：test expectancy=-4.0% < 0（負期望值） |
| 8341 | ensemble_triple_confirm | -4.2% | 0.00 | 7 | -27.3% | 0.00 | X | O | O | FAIL：test expectancy=-4.2% < 0（負期望值） |
| 2474 | ensemble_triple_confirm | -4.3% | 0.24 | 10 | -43.2% | 0.00 | X | X | O | FAIL：test expectancy=-4.3% < 0（負期望值） |
| 5347 | ensemble_triple_confirm | -4.5% | 0.27 | 10 | -52.7% | 0.09 | X | O | X | FAIL：test expectancy=-4.5% < 0（負期望值） |
| 3454 | ensemble_triple_confirm | -4.8% | 0.26 | 5 | -24.1% | 0.00 | X | O | O | FAIL：test expectancy=-4.8% < 0（負期望值） |
| 2324 | ensemble_triple_confirm | -4.9% | 0.29 | 6 | -33.8% | 0.00 | X | X | X | FAIL：test expectancy=-4.9% < 0（負期望值） |
| 6116 | ensemble_triple_confirm | -5.0% | 0.16 | 7 | -34.3% | 0.00 | X | X | X | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 3008 | ensemble_triple_confirm | -5.3% | 0.30 | 5 | -31.9% | 0.00 | X | O | O | FAIL：test expectancy=-5.3% < 0（負期望值） |
| 2603 | ensemble_triple_confirm | -5.6% | 0.21 | 7 | -38.0% | 0.00 | X | X | X | FAIL：test expectancy=-5.6% < 0（負期望值） |
| 1907 | ensemble_triple_confirm | -7.3% | 0.00 | 3 | -24.7% | N/A | X | X | O | FAIL：test expectancy=-7.3% < 0（負期望值） |
| 1314 | ensemble_triple_confirm | -11.3% | 0.22 | 10 | -100.0% | 0.02 | X | X | O | FAIL：test expectancy=-11.3% < 0（負期望值） |
| 4148 | ensemble_triple_confirm | -38.4% | 0.00 | 3 | -100.0% | N/A | X | X | O | FAIL：test expectancy=-38.4% < 0（負期望值） |
