# TIERING REPORT — 20260516_213445

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 1 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 83 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 84**  （目標 ≥ 20）

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
| 8069 | ensemble_trend_confirm | +5.2% | inf | 3 | -4.1% | N/A | X | X | O | LOW_N_RESCUE：n=3, raw_PF=inf ≥ 3.0, exp=+5.2% ≥ 5%, |DD|=4% ≤ 25%, holdout=[A_new=NA B=NA C=O]（紙上交易 3 個月） |

### Tier F — 部位上限 0% （共 83 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1605 | ensemble_trend_confirm | +17.8% | inf | 1 | -4.9% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1456 | ensemble_trend_confirm | +16.1% | inf | 2 | -7.8% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3596 | ensemble_trend_confirm | +14.3% | inf | 1 | -5.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2337 | ensemble_trend_confirm | +13.3% | inf | 1 | -0.0% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3406 | ensemble_trend_confirm | +12.7% | inf | 1 | -7.2% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2408 | ensemble_trend_confirm | +12.7% | inf | 1 | -7.2% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2883 | ensemble_trend_confirm | +12.7% | inf | 1 | -4.4% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2812 | ensemble_trend_confirm | +12.7% | inf | 1 | -3.8% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 1560 | ensemble_trend_confirm | +12.0% | inf | 2 | -4.8% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 006208 | ensemble_trend_confirm | +11.1% | inf | 1 | -2.3% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6271 | ensemble_trend_confirm | +7.5% | inf | 2 | -8.0% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2356 | ensemble_trend_confirm | +6.7% | inf | 1 | -0.2% | N/A | X | X | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2353 | ensemble_trend_confirm | +6.5% | inf | 1 | -4.5% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2376 | ensemble_trend_confirm | +4.8% | inf | 2 | -4.2% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 5347 | ensemble_trend_confirm | +4.3% | 1.65 | 3 | -22.7% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3037 | ensemble_trend_confirm | +3.7% | 3.13 | 2 | -16.2% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2330 | ensemble_trend_confirm | +3.6% | 1.82 | 3 | -15.0% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2888 | ensemble_trend_confirm | +3.4% | 1.36 | 2 | -11.4% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2474 | ensemble_trend_confirm | +3.4% | inf | 3 | -5.1% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2881 | ensemble_trend_confirm | +3.3% | 1.84 | 2 | -6.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 8341 | ensemble_trend_confirm | +2.8% | inf | 1 | -2.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4958 | ensemble_trend_confirm | +2.6% | 1.52 | 2 | -13.1% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2382 | ensemble_trend_confirm | +2.2% | 1.62 | 2 | -14.9% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2820 | ensemble_trend_confirm | +2.2% | 2.92 | 2 | -2.6% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2884 | ensemble_trend_confirm | +2.2% | 2.71 | 2 | -8.4% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 4904 | ensemble_trend_confirm | +0.3% | 1.04 | 5 | -16.0% | 0.10 | X | X | X | FAIL：PF_lower=0.10, exp=+0.3%, n=5, holdout=[A_new=NA B=X C=NA] |
| 6505 | ensemble_trend_confirm | +0.2% | inf | 1 | -11.6% | N/A | X | O | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3008 | ensemble_trend_confirm | -0.4% | 0.76 | 2 | -3.5% | N/A | X | X | X | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 3324 | ensemble_trend_confirm | -1.6% | 0.00 | 1 | -12.7% | N/A | X | X | X | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 2890 | ensemble_trend_confirm | -2.4% | 0.46 | 3 | -16.1% | N/A | X | O | O | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 1907 | ensemble_trend_confirm | -2.9% | 0.00 | 1 | -10.9% | N/A | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 1102 | ensemble_trend_confirm | -3.6% | 0.00 | 1 | -3.6% | N/A | X | O | X | FAIL：test expectancy=-3.6% < 0（負期望值） |
| 2409 | ensemble_trend_confirm | -4.4% | 0.00 | 1 | -4.4% | N/A | X | X | X | FAIL：test expectancy=-4.4% < 0（負期望值） |
| 2324 | ensemble_trend_confirm | -6.2% | 0.00 | 1 | -7.0% | N/A | X | X | X | FAIL：test expectancy=-6.2% < 0（負期望值） |
| 9914 | ensemble_trend_confirm | -6.5% | 0.00 | 1 | -14.0% | N/A | X | X | X | FAIL：test expectancy=-6.5% < 0（負期望值） |
| 4763 | ensemble_trend_confirm | -7.3% | 0.00 | 1 | -7.6% | N/A | X | X | X | FAIL：test expectancy=-7.3% < 0（負期望值） |
| 3481 | ensemble_trend_confirm | -8.3% | 0.00 | 1 | -8.3% | N/A | X | X | X | FAIL：test expectancy=-8.3% < 0（負期望值） |
| 6191 | ensemble_trend_confirm | -8.7% | 0.26 | 4 | -39.8% | N/A | X | O | X | FAIL：test expectancy=-8.7% < 0（負期望值） |
| 3034 | ensemble_trend_confirm | -10.0% | 0.00 | 2 | -24.3% | N/A | X | O | X | FAIL：test expectancy=-10.0% < 0（負期望值） |
| 2885 | ensemble_trend_confirm | -10.9% | 0.00 | 1 | -17.3% | N/A | X | O | X | FAIL：test expectancy=-10.9% < 0（負期望值） |
| 2360 | ensemble_trend_confirm | -14.5% | 0.00 | 1 | -20.5% | N/A | X | X | O | FAIL：test expectancy=-14.5% < 0（負期望值） |
| 2327 | ensemble_trend_confirm | -15.0% | 0.00 | 1 | -15.0% | N/A | X | O | X | FAIL：test expectancy=-15.0% < 0（負期望值） |
| 1503 | ensemble_trend_confirm | -18.2% | 0.00 | 1 | -18.2% | N/A | X | X | X | FAIL：test expectancy=-18.2% < 0（負期望值） |
| 0056 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 00878 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 00919 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 00940 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1314 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1402 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1582 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1789 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2002 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2009 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2014 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2027 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2354 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2369 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2542 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2603 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2609 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2618 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2727 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2892 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3014 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3044 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3231 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3454 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3526 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3711 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 4148 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 4938 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5314 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5871 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6116 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6213 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6443 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6488 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6491 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6526 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6531 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6533 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 8046 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 8081 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
