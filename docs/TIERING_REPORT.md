# TIERING REPORT — 20260519_210501

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 3 | 50% | STRONG：可用，建議 50% 部位 |
| B | 3 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 3 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 13 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 9 / 25**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1303 | gap_continuation | +18.7% | 49.65 | 7 | -18.9% | 5.00 | X | O | X | PF_lower=5.00 ≥ 1.5, exp=+18.7% ≥ 3%, n=7≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 2317 | gap_continuation | +10.5% | inf | 6 | -13.0% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+10.5% ≥ 3%, n=6≥6, holdout=[A_new=NA B=NA C=NA], gate=PF_lower≥2.0 自動晉升 |
| 1301 | gap_continuation | +5.6% | inf | 6 | -9.3% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+5.6% ≥ 3%, n=6≥6, holdout=[A_new=NA B=X C=NA], gate=PF_lower≥2.0 自動晉升 |

### Tier B — 部位上限 30% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3189 | chip_momentum | +5.9% | 3.04 | 24 | -34.8% | 1.10 | X | X | X | PF_lower=1.10 ≥ 1.0, exp=+5.9% ≥ 2%, n=24≥5, holdout=[A_new=NA B=NA C=NA] |
| 6770 | low_vol_pullback | +4.6% | 9.19 | 9 | -20.9% | 1.77 | X | X | X | PF_lower=1.77 ≥ 1.0, exp=+4.6% ≥ 2%, n=9≥5, holdout=[A_new=NA B=NA C=NA] |
| 1326 | low_vol_pullback | +3.5% | 7.31 | 8 | -8.3% | 1.48 | X | O | X | PF_lower=1.48 ≥ 1.0, exp=+3.5% ≥ 2%, n=8≥5, holdout=[A_new=NA B=O C=X] |

### Tier C — 部位上限 15% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2337 | low_vol_pullback | +6.2% | 4.54 | 5 | -8.6% | 0.78 | X | X | X | PF_lower=0.78 ≥ 0.7, exp=+6.2% ≥ 1%, n=5≥5, holdout=[A_new=NA B=X C=NA] |
| 2382 | gap_continuation | +3.8% | 2.05 | 19 | -21.2% | 0.76 | X | X | X | PF_lower=0.76 ≥ 0.7, exp=+3.8% ≥ 1%, n=19≥5, holdout=[A_new=NA B=NA C=NA] |
| 6213 | low_vol_pullback | +3.1% | 3.64 | 8 | -14.1% | 0.80 | X | X | X | PF_lower=0.80 ≥ 0.7, exp=+3.1% ≥ 1%, n=8≥5, holdout=[A_new=NA B=X C=NA] |

### Tier F — 部位上限 0% （共 13 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3034 | momentum_hold | +43.9% | 12.47 | 2 | -14.8% | N/A | X | O | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2344 | momentum_hold | +40.0% | 8.62 | 10 | -38.7% | 0.00 | X | X | X | FAIL：PF_lower=0.00, exp=+40.0%, n=10, holdout=[A_new=NA B=NA C=X] |
| 6505 | trend_pullback | +39.8% | inf | 1 | -5.7% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2376 | bollinger_squeeze | +28.3% | 4.39 | 6 | -25.4% | 0.34 | X | O | X | FAIL：PF_lower=0.34, exp=+28.3%, n=6, holdout=[A_new=NA B=O C=NA] |
| 2002 | monthly_revenue_event | +26.5% | inf | 1 | -0.8% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2408 | chip_momentum | +24.8% | 2.99 | 10 | -36.8% | 0.11 | X | O | X | FAIL：PF_lower=0.11, exp=+24.8%, n=10, holdout=[A_new=NA B=O C=X] |
| 4958 | gap_continuation | +6.5% | 2.03 | 7 | -27.5% | 0.37 | X | X | O | FAIL：PF_lower=0.37, exp=+6.5%, n=7, holdout=[A_new=NA B=X C=O] |
| 9907 | low_vol_pullback | +3.9% | inf | 2 | -6.1% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2303 | mean_reversion | +3.5% | 2.33 | 3 | -9.3% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3227 | mean_reversion | +3.1% | 3.02 | 5 | -6.5% | 0.46 | X | O | X | FAIL：PF_lower=0.46, exp=+3.1%, n=5, holdout=[A_new=NA B=O C=NA] |
| 1809 | gap_continuation | +2.1% | 1.00 | 15 | -41.5% | 0.06 | X | X | X | FAIL：PF_lower=0.06, exp=+2.1%, n=15, holdout=[A_new=NA B=X C=NA] |
| 2474 | low_vol_pullback | +0.5% | 1.51 | 2 | -8.7% | N/A | X | X | X | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 6271 | chip_momentum | -1.2% | 0.59 | 8 | -36.7% | 0.00 | X | O | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
