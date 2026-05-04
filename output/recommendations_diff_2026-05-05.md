# Recommendations Diff — 2026-05-05

OLD: `archive\per_stock_recommendations_2017train.yaml`
NEW: `config\per_stock_recommendations.yaml`

## Summary

- 總股票：OLD 71 / NEW 74 / 共 71 檔出現在兩邊
- 只在 OLD：0
- 只在 NEW：3
- **Tier 改變**：6 檔
- **Template 改變**：8 檔
- **Tradeable 翻轉**：3 檔
- **BNH Tier 改變**：3 檔

## Tier 分佈

| Tier | OLD | NEW | Δ |
|---|---|---|---|
| S | 1 | 2 | +1 |
| A | 6 | 7 | +1 |
| B | 6 | 8 | +2 |
| C | 14 | 14 | — |
| F | 44 | 43 | -1 |

## Tier 變動清單

| 股票 | 名稱 | OLD Tier | NEW Tier | 方向 |
|---|---|---|---|---|
| 1301 | 台塑 | F | A | F↑A |
| 2337 | 旺宏 | F | C | F↑C |
| 1303 | 南亞 | B | A | B↑A |
| 1326 | 台化 | C | B | C↑B |
| 6770 | 力積電 | A | B | A↓B |
| 1809 | 中釉 | C | F | C↓F |

## Template 變動清單

| 股票 | 名稱 | OLD Template | NEW Template |
|---|---|---|---|
| 1301 | 台塑 | trend_pullback | gap_continuation |
| 1326 | 台化 | trend_pullback | low_vol_pullback |
| 1809 | 中釉 | donchian_breakout | bollinger_squeeze |
| 2002 | 中鋼 | mean_reversion | monthly_revenue_event |
| 2382 | 廣達 | monthly_revenue_event | chip_momentum |
| 2408 | 南亞科 | bollinger_squeeze | chip_momentum |
| 4958 | 臻鼎-KY | bollinger_squeeze | gap_continuation |
| 6271 | 同欣電 | mean_reversion | chip_momentum |

## Tradeable 翻轉

| 股票 | 名稱 | OLD | NEW |
|---|---|---|---|
| 1301 | 台塑 | False | True |
| 1809 | 中釉 | True | False |
| 2337 | 旺宏 | False | True |

## 只在 NEW（新增）

2369, 3189, 8046
