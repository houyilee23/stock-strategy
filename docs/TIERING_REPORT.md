# TIERING REPORT — 20260518_110805

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 5 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 5**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 5 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3323 | ensemble_oversold_vote | +19.8% | inf | 1 | -10.3% | N/A | X | O | O | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2328 | ensemble_oversold_vote | +1.2% | 2.82 | 4 | -15.3% | N/A | X | O | O | FAIL：test n_trades=4 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2352 | ensemble_oversold_vote | -1.6% | 0.35 | 6 | -30.9% | 0.01 | X | O | O | FAIL：test expectancy=-1.6% < 0（負期望值） |
| 5274 | ensemble_oversold_vote | -1.7% | 0.65 | 5 | -34.4% | 0.09 | X | X | O | FAIL：test expectancy=-1.7% < 0（負期望值） |
| 7769 | ensemble_oversold_vote | -2.2% | 0.00 | 2 | -6.3% | N/A | X | X | X | FAIL：test expectancy=-2.2% < 0（負期望值） |
