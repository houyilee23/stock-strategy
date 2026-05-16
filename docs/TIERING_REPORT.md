# TIERING REPORT — 20260516_142823

## 1. 統計摘要

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用，單檔上限 100% |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop |
| C | 0 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 27 | 0% | FAIL：移出 universe |

**可操作標的合計（S+A+B+C）= 0 / 27**  （目標 ≥ 20）

## 2. 各 Tier 個股清單

### Tier S — 部位上限 100% （共 0 檔）

（無）

### Tier A — 部位上限 50% （共 0 檔）

（無）

### Tier B — 部位上限 30% （共 0 檔）

（無）

### Tier C — 部位上限 15% （共 0 檔）

（無）

### Tier F — 部位上限 0% （共 27 檔）

| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |
|-------|----------|-----|----|---|----|----------|-------|---|---|--------|
| 2855 | ensemble_trend_confirm | +14.1% | inf | 1 | -5.9% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2867 | ensemble_trend_confirm | +9.6% | inf | 1 | -1.6% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3526 | ensemble_trend_confirm | +6.9% | inf | 1 | -0.9% | N/A | X | X | X | FAIL：test n_trades=1 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 2880 | ensemble_trend_confirm | +2.5% | 1.70 | 2 | -12.0% | N/A | X | X | O | FAIL：test n_trades=2 < 5（樣本不足，未達 LOW_N_RESCUE） |
| 3045 | ensemble_trend_confirm | -1.5% | 0.52 | 2 | -7.4% | N/A | X | X | O | FAIL：test expectancy=-1.5% < 0（負期望值） |
| 2886 | ensemble_trend_confirm | -4.6% | 0.00 | 1 | -7.4% | N/A | X | O | O | FAIL：test expectancy=-4.6% < 0（負期望值） |
| 1504 | ensemble_trend_confirm | -5.0% | 0.00 | 3 | -18.0% | N/A | X | X | X | FAIL：test expectancy=-5.0% < 0（負期望值） |
| 2367 | ensemble_trend_confirm | -7.4% | 0.00 | 1 | -8.5% | N/A | X | O | X | FAIL：test expectancy=-7.4% < 0（負期望值） |
| 9921 | ensemble_trend_confirm | -10.8% | 0.00 | 1 | -12.7% | N/A | X | X | X | FAIL：test expectancy=-10.8% < 0（負期望值） |
| 1234 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1314 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1535 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 1722 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2002 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2347 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2458 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2606 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2727 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 2845 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3105 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 3533 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 4147 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5388 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | O | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5483 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 5904 | ensemble_trend_confirm | N/A | inf | 0 | -1.6% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 6446 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | O | X | FAIL：test expectancy=-inf% < 0（負期望值） |
| 8454 | ensemble_trend_confirm | N/A | inf | 0 | -0.0% | N/A | X | X | X | FAIL：test expectancy=-inf% < 0（負期望值） |
