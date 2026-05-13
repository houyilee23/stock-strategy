# TIERING REPORT — 20260513_184655

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
| 2886 | low_volume_reversal | +1.3% | 1.76 | 11 | -12.2% | 0.49 | X | X | X | FAIL：PF_lower=0.49, exp=+1.3%, n=11, holdout=[A_new=NA B=X C=X] |
| 0056 | low_volume_reversal | +0.7% | 1.34 | 32 | -32.6% | 0.58 | X | O | X | FAIL：PF_lower=0.58, exp=+0.7%, n=32, holdout=[A_new=NA B=O C=X] |
| 3045 | low_volume_reversal | +0.3% | 1.18 | 25 | -18.3% | 0.41 | X | O | O | FAIL：PF_lower=0.41, exp=+0.3%, n=25, holdout=[A_new=NA B=O C=O] |
| 2412 | low_volume_reversal | +0.3% | 1.18 | 27 | -13.4% | 0.53 | X | X | X | FAIL：PF_lower=0.53, exp=+0.3%, n=27, holdout=[A_new=NA B=X C=X] |
| 2002 | low_volume_reversal | -0.4% | 0.83 | 13 | -19.3% | 0.16 | X | O | O | FAIL：test expectancy=-0.4% < 0（負期望值） |
| 2474 | low_volume_reversal | -0.9% | 0.53 | 31 | -29.8% | 0.22 | X | X | O | FAIL：test expectancy=-0.9% < 0（負期望值） |
| 1101 | low_volume_reversal | -1.3% | 0.60 | 15 | -22.0% | 0.12 | X | O | X | FAIL：test expectancy=-1.3% < 0（負期望值） |
| 9940 | low_volume_reversal | -1.4% | 0.45 | 37 | -50.8% | 0.14 | X | X | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 5880 | low_volume_reversal | -1.4% | 0.49 | 19 | -40.2% | 0.11 | X | O | X | FAIL：test expectancy=-1.4% < 0（負期望值） |
| 1227 | low_volume_reversal | -1.8% | 0.23 | 25 | -42.6% | 0.02 | X | X | X | FAIL：test expectancy=-1.8% < 0（負期望值） |
| 2105 | low_volume_reversal | -2.4% | 0.42 | 17 | -41.0% | 0.03 | X | X | X | FAIL：test expectancy=-2.4% < 0（負期望值） |
| 2912 | low_volume_reversal | -2.5% | 0.27 | 19 | -41.2% | 0.04 | X | X | O | FAIL：test expectancy=-2.5% < 0（負期望值） |
| 9921 | low_volume_reversal | -4.6% | 0.28 | 33 | -80.6% | 0.05 | X | X | X | FAIL：test expectancy=-4.6% < 0（負期望值） |
