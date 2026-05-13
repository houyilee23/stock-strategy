# TIERING REPORT — 20260513_150036

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 13 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 13**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 13 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2412 | monthly_anchor | +0.4% | 1.35 | 31 | -9.7% | 0.60 | X | O | O | FAIL：PF_lower=0.60, exp=+0.4%, n=31, holdout=[A_new=NA B=O C=O] |
| 3045 | monthly_anchor | +0.3% | 1.24 | 32 | -17.5% | 0.54 | X | O | O | FAIL：PF_lower=0.54, exp=+0.3%, n=32, holdout=[A_new=NA B=O C=O] |
| 1101 | monthly_anchor | -0.5% | 0.72 | 36 | -37.3% | 0.26 | X | X | X | FAIL：test expectancy=-0.5% < 0（負期望值） |
| 2474 | monthly_anchor | -0.6% | 0.58 | 52 | -37.0% | 0.27 | X | X | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 0056 | monthly_anchor | -0.7% | 0.63 | 29 | -34.5% | 0.29 | X | X | X | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2912 | monthly_anchor | -0.7% | 0.60 | 37 | -37.5% | 0.21 | X | O | O | FAIL：test expectancy=-0.7% < 0（負期望值） |
| 2886 | monthly_anchor | -0.9% | 0.60 | 33 | -39.4% | 0.25 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 9940 | monthly_anchor | -0.9% | 0.57 | 42 | -46.6% | 0.21 | X | X | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 5880 | monthly_anchor | -1.2% | 0.45 | 36 | -41.0% | 0.17 | X | O | X | FAIL：test expectancy=-1.2% < 0（負期望值） |
| 9921 | monthly_anchor | -1.4% | 0.55 | 29 | -48.2% | 0.18 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2105 | monthly_anchor | -1.4% | 0.53 | 36 | -53.8% | 0.19 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 2002 | monthly_anchor | -2.2% | 0.31 | 39 | -66.1% | 0.06 | X | X | O | FAIL：test expectancy=-2.2% < 0（負期望值） |
| 1227 | monthly_anchor | -2.3% | 0.08 | 47 | -68.1% | 0.01 | X | X | X | FAIL：test expectancy=-2.3% < 0（負期望值） |
