# TIERING REPORT — 20260504_213029

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 2 | 50% | STRONG：可用，建議 50% 部位 |
| B | 1 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 1 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 3 / 4**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 2 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1303 | gap_continuation | +11.5% | 7.68 | 9 | -22.7% | 1.63 | X | O | X | PF_lower=1.63 ≥ 1.5, exp=+11.5% ≥ 3%, n=9≥6, holdout=[A_new=NA B=O C=NA], gate=any holdout PASS |
| 1301 | gap_continuation | +5.6% | inf | 6 | -9.3% | 5.00 | X | X | X | PF_lower=5.00 ≥ 1.5, exp=+5.6% ≥ 3%, n=6≥6, holdout=[A_new=NA B=X C=NA], gate=PF_lower≥2.0 自動晉升 |

### Tier B — 部位上限 30% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 1326 | low_vol_pullback | +3.5% | 7.31 | 8 | -8.3% | 1.48 | X | O | X | PF_lower=1.48 ≥ 1.0, exp=+3.5% ≥ 2%, n=8≥5, holdout=[A_new=NA B=O C=X] |

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 6505 | trend_pullback | +39.8% | inf | 1 | -5.7% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
