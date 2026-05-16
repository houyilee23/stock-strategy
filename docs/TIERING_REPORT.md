# TIERING REPORT — 20260516_090509

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 3 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 3**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 3 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 3526 | psar_flip | +1.5% | 1.42 | 10 | -19.0% | 0.31 | X | X | X | FAIL：PF_lower=0.31, exp=+1.5%, n=10, holdout=[A_new=NA B=X C=X] |
| 1909 | psar_flip | -0.3% | 0.83 | 16 | -20.1% | 0.17 | X | X | X | FAIL：test expectancy=-0.3% < 0（負期望值） |
| 9904 | psar_flip | -0.5% | 0.77 | 10 | -11.7% | 0.13 | X | X | O | FAIL：test expectancy=-0.5% < 0（負期望值） |
