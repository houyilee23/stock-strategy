# TIERING REPORT — 20260505_194813

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 2 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 5 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 2 / 7**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1560 | mean_reversion | +7.1% | 6.93 | 7 | -11.1% | 0.97 | X | X | X | PF_lower=0.97 ≥ 0.7, exp=+7.1% ≥ 1%, n=7≥5, holdout=[A_new=NA B=NA C=X] |
| 2330 | gap_continuation | +1.1% | 1.55 | 42 | -29.2% | 0.72 | X | O | X | PF_lower=0.72 ≥ 0.7, exp=+1.1% ≥ 1%, n=42≥5, holdout=[A_new=NA B=O C=X] |

### Tier F — 部位上限 0% （共 5 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2344 | momentum_hold | +80.1% | 12.64 | 4 | -26.4% | N/A | X | X | X | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2426 | mean_reversion | +10.7% | 8.24 | 3 | -17.5% | N/A | X | X | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2324 | chip_momentum | +5.5% | 2.97 | 11 | -18.4% | 0.48 | X | X | X | FAIL：PF_lower=0.48, exp=+5.5%, n=11, holdout=[A_new=NA B=X C=X] |
| 9940 | low_vol_pullback | +2.7% | 2.55 | 3 | -7.3% | N/A | X | O | X | FAIL：test n_trades=3 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2303 | chip_momentum | +1.5% | 1.42 | 20 | -29.8% | 0.25 | X | O | X | FAIL：PF_lower=0.25, exp=+1.5%, n=20, holdout=[A_new=NA B=O C=X] |
