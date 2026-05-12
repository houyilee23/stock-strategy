# TIERING REPORT — 20260513_020728

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 1 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 21 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 1 / 22**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 1 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2426 | double_pullback | +3.5% | 2.13 | 31 | -27.0% | 1.13 | X | X | X | PF_lower=1.13 ≥ 1.0, exp=+3.5% ≥ 2%, n=31≥5, holdout=[A_new=NA B=X C=NA] |

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 21 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2356 | double_pullback | +2.3% | 1.32 | 16 | -25.6% | 0.54 | X | O | X | FAIL：PF_lower=0.54, exp=+2.3%, n=16, holdout=[A_new=NA B=O C=X] |
| 9921 | double_pullback | +1.8% | 1.54 | 13 | -22.6% | 0.50 | X | X | X | FAIL：PF_lower=0.50, exp=+1.8%, n=13, holdout=[A_new=NA B=X C=NA] |
| 5880 | double_pullback | +1.6% | 1.55 | 7 | -6.7% | 0.43 | X | X | O | FAIL：PF_lower=0.43, exp=+1.6%, n=7, holdout=[A_new=NA B=NA C=O] |
| 2881 | double_pullback | +0.8% | 1.16 | 26 | -26.4% | 0.55 | X | X | X | FAIL：PF_lower=0.55, exp=+0.8%, n=26, holdout=[A_new=NA B=X C=X] |
| 0056 | double_pullback | +0.7% | 1.26 | 18 | -12.9% | 0.48 | X | X | X | FAIL：PF_lower=0.48, exp=+0.7%, n=18, holdout=[A_new=NA B=X C=X] |
| 2379 | double_pullback | +0.3% | 1.02 | 29 | -22.2% | 0.43 | X | O | X | FAIL：PF_lower=0.43, exp=+0.3%, n=29, holdout=[A_new=NA B=O C=X] |
| 2412 | double_pullback | +0.2% | 1.06 | 16 | -12.0% | 0.24 | X | X | X | FAIL：PF_lower=0.24, exp=+0.2%, n=16, holdout=[A_new=NA B=X C=X] |
| 3045 | double_pullback | +0.2% | 1.01 | 14 | -16.9% | 0.26 | X | X | O | FAIL：PF_lower=0.26, exp=+0.2%, n=14, holdout=[A_new=NA B=X C=O] |
| 1605 | double_pullback | -0.1% | 0.88 | 37 | -46.3% | 0.44 | X | O | O | FAIL：test expectancy=-0.1% < 0（負期望值） |
| 2002 | double_pullback | -0.6% | 0.82 | 12 | -41.6% | 0.19 | X | X | O | FAIL：test expectancy=-0.6% < 0（負期望值） |
| 6669 | double_pullback | -0.8% | 0.72 | 68 | -61.0% | 0.49 | X | X | X | FAIL：test expectancy=-0.8% < 0（負期望值） |
| 2886 | double_pullback | -0.9% | 0.69 | 22 | -31.1% | 0.24 | X | O | X | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 2474 | double_pullback | -1.0% | 0.66 | 25 | -38.7% | 0.25 | X | O | O | FAIL：test expectancy=-1.0% < 0（負期望值） |
| 2324 | double_pullback | -1.1% | 0.69 | 30 | -43.6% | 0.25 | X | X | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 1216 | double_pullback | -1.1% | 0.60 | 29 | -37.4% | 0.21 | X | O | X | FAIL：test expectancy=-1.1% < 0（負期望值） |
| 2105 | double_pullback | -1.3% | 0.66 | 26 | -39.2% | 0.25 | X | X | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 1227 | double_pullback | -2.4% | 0.27 | 17 | -34.2% | 0.02 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 9940 | double_pullback | -2.9% | 0.18 | 11 | -30.1% | 0.00 | X | X | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 1101 | double_pullback | -2.9% | 0.38 | 15 | -44.1% | 0.03 | X | O | X | FAIL：test expectancy=-2.9% < 0（負期望值） |
| 2912 | double_pullback | -3.5% | 0.02 | 11 | -33.2% | 0.00 | X | O | X | FAIL：test expectancy=-3.5% < 0（負期望值） |
| 2207 | double_pullback | -4.0% | 0.20 | 21 | -59.0% | 0.00 | X | X | X | FAIL：test expectancy=-4.0% < 0（負期望值） |
