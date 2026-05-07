# Recommendations Diff — 2026-05-07

OLD: `archive\per_stock_recommendations_2017train.yaml`
NEW: `config\per_stock_recommendations.yaml`

## Summary

- 總股票：OLD 71 / NEW 78 / 共 71 檔出現在兩邊
- 只在 OLD：0
- 只在 NEW：7
- **Tier 改變**：22 檔
- **Template 改變**：35 檔
- **Tradeable 翻轉**：13 檔
- **BNH Tier 改變**：13 檔

## Tier 分佈

| Tier | OLD | NEW | Δ |
|---|---|---|---|
| S | 1 | 2 | +1 |
| A | 6 | 4 | -2 |
| B | 6 | 6 | — |
| C | 14 | 19 | +5 |
| F | 44 | 47 | +3 |

## Tier 變動清單

| 股票 | 名稱 | OLD Tier | NEW Tier | 方向 |
|---|---|---|---|---|
| 1301 | 台塑 | F | A | F↑A |
| 00919 | 群益台灣精選高息 | F | C | F↑C |
| 1402 | 遠東新 | F | C | F↑C |
| 1802 | 台玻 | B | S | B↑S |
| 2337 | 旺宏 | F | C | F↑C |
| 2353 | 宏碁 | F | C | F↑C |
| 2382 | 廣達 | F | C | F↑C |
| 2408 | 南亞科 | F | C | F↑C |
| 1303 | 南亞 | B | A | B↑A |
| 1326 | 台化 | C | B | C↑B |
| 2383 | 台光電 | C | B | C↑B |
| 006208 | 富邦台50 | B | C | B↓C |
| 2317 | 鴻海 | S | A | S↓A |
| 6770 | 力積電 | A | B | A↓B |
| 1560 | 中砂 | A | C | A↓C |
| 1809 | 中釉 | C | F | C↓F |
| 2330 | 台積電 | A | C | A↓C |
| 2345 | 智邦 | C | F | C↓F |
| 2615 | 萬海 | C | F | C↓F |
| 2881 | 富邦金 | C | F | C↓F |
| 2308 | 台達電 | A | F | A↓F |
| 2360 | 致茂 | A | F | A↓F |

## Template 變動清單

| 股票 | 名稱 | OLD Template | NEW Template |
|---|---|---|---|
| 006208 | 富邦台50 | donchian_breakout | bollinger_squeeze |
| 00878 | 國泰永續高股息 | mean_reversion | bollinger_squeeze |
| 00919 | 群益台灣精選高息 | trend_pullback | momentum_hold |
| 00940 | 元大台灣價值高息 | mean_reversion | momentum_hold |
| 1227 | 佳格 | donchian_breakout | monthly_revenue_event |
| 1301 | 台塑 | trend_pullback | gap_continuation |
| 1326 | 台化 | trend_pullback | low_vol_pullback |
| 1605 | 華新 | momentum_hold | bollinger_squeeze |
| 1809 | 中釉 | donchian_breakout | chip_momentum |
| 2002 | 中鋼 | mean_reversion | monthly_revenue_event |
| 2027 | 大成鋼 | donchian_breakout | gap_continuation |
| 2105 | 正新 | trend_pullback | chip_momentum |
| 2303 | 聯電 | mean_reversion | chip_momentum |
| 2308 | 台達電 | low_vol_pullback | volume_breakout |
| 2327 | 國巨 | bollinger_squeeze | donchian_breakout |
| 2330 | 台積電 | donchian_breakout | gap_continuation |
| 2337 | 旺宏 | monthly_revenue_event | low_vol_pullback |
| 2344 | 華邦電 | donchian_breakout | momentum_hold |
| 2345 | 智邦 | low_vol_pullback | gap_continuation |
| 2353 | 宏碁 | mean_reversion | donchian_breakout |
| 2360 | 致茂 | low_vol_pullback | gap_continuation |
| 2376 | 技嘉 | monthly_revenue_event | momentum_hold |
| 2379 | 瑞昱 | monthly_revenue_event | mean_reversion |
| 2382 | 廣達 | monthly_revenue_event | low_vol_pullback |
| 2383 | 台光電 | chip_momentum | donchian_breakout |
| 2408 | 南亞科 | bollinger_squeeze | chip_momentum |
| 2426 | 鼎元 | gap_continuation | mean_reversion |
| 2454 | 聯發科 | mean_reversion | monthly_revenue_event |
| 2474 | 可成 | trend_pullback | mean_reversion |
| 2603 | 長榮 | low_vol_pullback | monthly_revenue_event |
| 2615 | 萬海 | volume_breakout | donchian_breakout |
| 2618 | 長榮航 | chip_momentum | momentum_hold |
| 2881 | 富邦金 | mean_reversion | momentum_hold |
| 4958 | 臻鼎-KY | bollinger_squeeze | gap_continuation |
| 6271 | 同欣電 | mean_reversion | chip_momentum |

## Tradeable 翻轉

| 股票 | 名稱 | OLD | NEW |
|---|---|---|---|
| 00919 | 群益台灣精選高息 | False | True |
| 1301 | 台塑 | False | True |
| 1402 | 遠東新 | False | True |
| 1809 | 中釉 | True | False |
| 2308 | 台達電 | True | False |
| 2337 | 旺宏 | False | True |
| 2345 | 智邦 | True | False |
| 2353 | 宏碁 | False | True |
| 2360 | 致茂 | True | False |
| 2382 | 廣達 | False | True |
| 2408 | 南亞科 | False | True |
| 2615 | 萬海 | True | False |
| 2881 | 富邦金 | True | False |

## 只在 NEW（新增）

0056, 1101, 1102, 1216, 2369, 3189, 8046
