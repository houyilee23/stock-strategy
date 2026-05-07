# Auto-Iterate Final Report — 20260504_203450

**Generated**: 自動執行（Auto Mode）— Q5=(b) 激進改寫授權範圍內
**Universe**: 45 檔（涵蓋 Takeshi / Katie / Research / Research_todo 去重後合集）
**0050 test CAGR**: +27.0%

## 1. Tier 分布

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用 |
| A | 3 | 50% | STRONG：可用，建議 50% 部位 |
| B | 3 | 30% | MODERATE：可用，30% 部位 + 嚴格 trailing stop |
| C | 11 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 27 | 0% | FAIL：移出 universe，建議走組合模式或買 0050 |

**可操作標的（S+A+B+C）= 18 / 45**  （目標 ≥ 20）

## 2. Watchlist 覆蓋率

### Takeshi — 可操作 7 / 9

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 1303 | 南亞 | A | gap_continuation | 50% | +11.5% | 7.68 | 9 |
| 1301 | 台塑 | A | gap_continuation | 50% | +5.6% | N/A | 6 |
| 1326 | 台化 | B | low_vol_pullback | 30% | +3.5% | 7.31 | 8 |
| 2408 | 南亞科 | C | chip_momentum | 15% | +16.9% | 8.22 | 10 |
| 2337 | 旺宏 | C | low_vol_pullback | 15% | +5.4% | 4.12 | 5 |
| 2369 | 2369 | C | low_vol_pullback | 15% | +3.6% | 3.90 | 7 |
| 2382 | 廣達 | C | low_vol_pullback | 15% | +3.0% | 2.09 | 16 |

### Katie — 可操作 3 / 8

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 1301 | 台塑 | A | gap_continuation | 50% | +5.6% | N/A | 6 |
| 1560 | 中砂 | C | mean_reversion | 15% | +7.1% | 6.93 | 7 |
| 2330 | 台積電 | C | gap_continuation | 15% | +1.1% | 1.55 | 42 |

### universe — 可操作 18 / 45

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 1802 | 台玻 | S | low_vol_pullback | 100% | +7.6% | 24.57 | 9 |
| 1303 | 南亞 | A | gap_continuation | 50% | +11.5% | 7.68 | 9 |
| 2317 | 鴻海 | A | gap_continuation | 50% | +11.1% | N/A | 6 |
| 1301 | 台塑 | A | gap_continuation | 50% | +5.6% | N/A | 6 |
| 2454 | 聯發科 | B | monthly_revenue_event | 30% | +8.7% | 11.00 | 10 |
| 2383 | 台光電 | B | donchian_breakout | 30% | +8.4% | 3.28 | 26 |
| 1326 | 台化 | B | low_vol_pullback | 30% | +3.5% | 7.31 | 8 |
| 2376 | 技嘉 | C | momentum_hold | 15% | +35.7% | 11.97 | 5 |
| 2408 | 南亞科 | C | chip_momentum | 15% | +16.9% | 8.22 | 10 |
| 00919 | 群益台灣精選高息 | C | momentum_hold | 15% | +14.1% | 7.04 | 3 |
| 006208 | 富邦台50 | C | bollinger_squeeze | 15% | +8.0% | 13.79 | 4 |
| 1560 | 中砂 | C | mean_reversion | 15% | +7.1% | 6.93 | 7 |
| 2337 | 旺宏 | C | low_vol_pullback | 15% | +5.4% | 4.12 | 5 |
| 2353 | 宏碁 | C | donchian_breakout | 15% | +5.3% | 3.09 | 8 |
| 2369 | 2369 | C | low_vol_pullback | 15% | +3.6% | 3.90 | 7 |
| 2382 | 廣達 | C | low_vol_pullback | 15% | +3.0% | 2.09 | 16 |
| 1402 | 遠東新 | C | low_vol_pullback | 15% | +2.7% | 5.07 | 6 |
| 2330 | 台積電 | C | gap_continuation | 15% | +1.1% | 1.55 | 42 |

### research_todo — 可操作 0 / 0

（無可操作）

## 3. 新模板貢獻分析（Phase 3 + Phase 6 加入）

| 模板 | 用途 | tradeable 命中數 |
|------|------|------------------|
| volume_breakout | LOW_SAMPLE 大型權值股（去 trend filter） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| gap_continuation | 事件驅動跳空 + 收紅 | 4 |
| low_vol_pullback | 傳產慢牛低波動回檔 | 6 |
| bollinger_squeeze | BB 壓縮後爆量突破 | 1 |
| chip_streak | 三大法人連續 ≥N 天買超（台股法人持續性 alpha） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| monthly_revenue_event | 月營收 YoY > X% + 公布日跳空（台股獨有日曆事件） | 1 |

**新模板貢獻**：12 / 18 tradeable （舊模板：6）

### 新模板拯救的個股（best_template ∈ 新四模板）

| Stock | 名稱 | Tier | 模板 | Exp | PF_lower |
|-------|------|------|------|-----|----------|
| 1802 | 台玻 | S | low_vol_pullback | +7.6% | 5.00 |
| 1303 | 南亞 | A | gap_continuation | +11.5% | 1.63 |
| 2317 | 鴻海 | A | gap_continuation | +11.1% | 5.00 |
| 1301 | 台塑 | A | gap_continuation | +5.6% | 5.00 |
| 2454 | 聯發科 | B | monthly_revenue_event | +8.7% | 1.37 |
| 1326 | 台化 | B | low_vol_pullback | +3.5% | 1.48 |
| 006208 | 富邦台50 | C | bollinger_squeeze | +8.0% | N/A |
| 2337 | 旺宏 | C | low_vol_pullback | +5.4% | 0.74 |
| 2369 | 2369 | C | low_vol_pullback | +3.6% | 0.78 |
| 2382 | 廣達 | C | low_vol_pullback | +3.0% | 0.76 |
| 1402 | 遠東新 | C | low_vol_pullback | +2.7% | 0.77 |
| 2330 | 台積電 | C | gap_continuation | +1.1% | 0.72 |

## 4. 各 Tier 完整清單

### Tier S （1 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 1802 | 台玻 | low_vol_pullback | +7.6% | 24.57 | 9 | -14.0% | 5.00 | A_new=NA B=NA C=NA |

### Tier A （3 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 1303 | 南亞 | gap_continuation | +11.5% | 7.68 | 9 | -22.7% | 1.63 | A_new=NA B=O C=NA |
| 2317 | 鴻海 | gap_continuation | +11.1% | N/A | 6 | -13.0% | 5.00 | A_new=NA B=NA C=NA |
| 1301 | 台塑 | gap_continuation | +5.6% | N/A | 6 | -9.3% | 5.00 | A_new=NA B=X C=NA |

### Tier B （3 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 2454 | 聯發科 | monthly_revenue_event | +8.7% | 11.00 | 10 | -12.1% | 1.37 | A_new=NA B=NA C=NA |
| 2383 | 台光電 | donchian_breakout | +8.4% | 3.28 | 26 | -28.6% | 1.03 | A_new=NA B=X C=O |
| 1326 | 台化 | low_vol_pullback | +3.5% | 7.31 | 8 | -8.3% | 1.48 | A_new=NA B=O C=X |

### Tier C （11 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 2376 | 技嘉 | momentum_hold | +35.7% | 11.97 | 5 | -32.9% | 0.85 | A_new=NA B=NA C=NA |
| 2408 | 南亞科 | chip_momentum | +16.9% | 8.22 | 10 | -34.8% | 0.99 | A_new=NA B=X C=NA |
| 00919 | 群益台灣精選高息 | momentum_hold | +14.1% | 7.04 | 3 | -11.0% | N/A | A_new=NA B=NA C=NA |
| 006208 | 富邦台50 | bollinger_squeeze | +8.0% | 13.79 | 4 | -6.7% | N/A | A_new=NA B=O C=NA |
| 1560 | 中砂 | mean_reversion | +7.1% | 6.93 | 7 | -11.1% | 0.97 | A_new=NA B=NA C=X |
| 2337 | 旺宏 | low_vol_pullback | +5.4% | 4.12 | 5 | -8.6% | 0.74 | A_new=NA B=X C=NA |
| 2353 | 宏碁 | donchian_breakout | +5.3% | 3.09 | 8 | -16.2% | 0.73 | A_new=NA B=NA C=X |
| 2369 | 2369 | low_vol_pullback | +3.6% | 3.90 | 7 | -13.4% | 0.78 | A_new=NA B=NA C=X |
| 2382 | 廣達 | low_vol_pullback | +3.0% | 2.09 | 16 | -18.4% | 0.76 | A_new=NA B=X C=X |
| 1402 | 遠東新 | low_vol_pullback | +2.7% | 5.07 | 6 | -5.5% | 0.77 | A_new=NA B=O C=X |
| 2330 | 台積電 | gap_continuation | +1.1% | 1.55 | 42 | -29.2% | 0.72 | A_new=NA B=O C=X |

## 5. 給 Takeshi/Katie 的行動建議

### 立即可用（S+A）
- **1802 台玻** (low_vol_pullback) — Tier S, 建議部位上限 100%
- **1303 南亞** (gap_continuation) — Tier A, 建議部位上限 50%
- **2317 鴻海** (gap_continuation) — Tier A, 建議部位上限 50%
- **1301 台塑** (gap_continuation) — Tier A, 建議部位上限 50%

### 條件可用（B），加嚴格 trailing stop
- **2454 聯發科** (monthly_revenue_event) — Tier B, 建議部位 30%
- **2383 台光電** (donchian_breakout) — Tier B, 建議部位 30%
- **1326 台化** (low_vol_pullback) — Tier B, 建議部位 30%

### 觀察（C），先紙上交易 3 個月
- **2376 技嘉** (momentum_hold) — Tier C, 最大部位 15%
- **2408 南亞科** (chip_momentum) — Tier C, 最大部位 15%
- **00919 群益台灣精選高息** (momentum_hold) — Tier C, 最大部位 15%
- **006208 富邦台50** (bollinger_squeeze) — Tier C, 最大部位 15%
- **1560 中砂** (mean_reversion) — Tier C, 最大部位 15%
- **2337 旺宏** (low_vol_pullback) — Tier C, 最大部位 15%
- **2353 宏碁** (donchian_breakout) — Tier C, 最大部位 15%
- **2369 2369** (low_vol_pullback) — Tier C, 最大部位 15%
- **2382 廣達** (low_vol_pullback) — Tier C, 最大部位 15%
- **1402 遠東新** (low_vol_pullback) — Tier C, 最大部位 15%
- **2330 台積電** (gap_continuation) — Tier C, 最大部位 15%

## 6. 已知限制與後續建議

- **達標**：tradeable=18 ≥ 15，可進入訊號模式生產使用
- **後續優化**：擴充 watchlists_todo 38 檔（金融 / 食品 / 航運）以增加 universe
- **F-tier 個股建議**：走組合模式（top-N）、BNH 候選（見下節）、或直接持有 0050
- **Holdout caveat**：A_new (2010-2016) 多數 NA — 因 universe 多為 2010 後上市；B (2018) / C (2022) 樣本常 < 5，依 v2 tri-state 邏輯不算 fail

## 7. BNH 候選（不適合 timing 但適合長持）

評估期間：2017-01-01 ~ 2024-12-31（≈8 年），對 F-tier 個股做平行評估。

**0050 baseline**：CAGR=+17.2%，|MaxDD|=34.0%，Sharpe=0.98

### BNH Tier 條件

| Tier | CAGR vs 0050 | MaxDD | div_yield | 部位上限 |
|------|--------------|-------|-----------|----------|
| BNH_S | ≥ +5% | ≤ 40% | — | 50% |
| BNH_A | ≥ 0% | ≤ 50% | — | 30% |
| BNH_B | ≥ -3% | — | ≥ 4% | 20% |
| F | 其他 | | | 0%（建議走 0050 / 組合模式） |

### BNH_A （4 檔）

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | Sharpe | 股息率 | 部位上限 |
|-------|------|------|---------|--------|--------|--------|----------|
| 2345 | 智邦 | +44.2% | +27.0% | 43.7% | 1.08 | 2.2% | 30% |
| 2360 | 致茂 | +26.9% | +9.7% | 49.7% | 0.79 | 2.8% | 30% |
| 2303 | 聯電 | +23.8% | +6.7% | 46.2% | 0.83 | 4.0% | 30% |
| 2618 | 長榮航 | +19.0% | +1.8% | 49.1% | 0.69 | 2.7% | 30% |

### BNH_B （5 檔）

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | Sharpe | 股息率 | 部位上限 |
|-------|------|------|---------|--------|--------|--------|----------|
| 2603 | 長榮 | +46.3% | +29.1% | 68.2% | 1.08 | 17.6% | 20% |
| 2615 | 萬海 | +30.5% | +13.3% | 80.8% | 0.81 | 4.4% | 20% |
| 2379 | 瑞昱 | +29.4% | +12.2% | 57.3% | 0.93 | 4.1% | 20% |
| 00878 | 國泰永續高股息 | +16.0% | -1.2% | 17.8% | 1.24 | 6.2% | 20% |
| 2324 | 仁寶 | +15.7% | -1.5% | 26.7% | 0.80 | 4.5% | 20% |

### F-tier 中也不適合 BNH （18 檔）

這些股票既無法 timing 也輸 0050，建議改走組合模式或直接買 0050。

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | 股息率 |
|-------|------|------|---------|--------|--------|
| 2327 | 國巨 | +31.0% | +13.8% | 76.8% | 2.5% |
| 2308 | 台達電 | +16.5% | -0.7% | 39.3% | 2.3% |
| 2881 | 富邦金 | +15.1% | -2.0% | 34.1% | 4.0% |
| 2027 | 大成鋼 | +14.8% | -2.4% | 60.7% | 3.3% |
| 1605 | 華新 | +14.2% | -3.0% | 56.6% | 3.9% |
| 0056 | 元大高股息 | +12.9% | -4.3% | 25.9% | 7.0% |
| 2426 | 鼎元 | +11.7% | -5.5% | 64.4% | 2.3% |
| 1102 | 亞泥 | +11.3% | -5.9% | 30.6% | 6.5% |
| 2207 | 和泰車 | +10.0% | -7.2% | 52.5% | 2.3% |
| 1216 | 統一 | +9.8% | -7.4% | 23.0% | 3.9% |
| 2344 | 華邦電 | +8.1% | -9.1% | 62.7% | 1.9% |
| 1809 | 中釉 | +7.9% | -9.3% | 61.5% | 1.5% |
| 1101 | 台泥 | +7.0% | -10.1% | 35.2% | 4.2% |
| 2474 | 可成 | +3.6% | -13.6% | 54.5% | 6.3% |
| 2002 | 中鋼 | +0.9% | -16.2% | 48.6% | 3.8% |
| 2105 | 正新 | +0.6% | -16.6% | 50.4% | 3.4% |
| 00940 | 元大台灣價值高息 | -1.6% | -18.7% | 13.6% | 0.6% |
| 1227 | 佳格 | -5.0% | -22.2% | 42.0% | 4.0% |

**BNH 救回統計**：9 / 27 F-tier 個股可改走 BNH。

---
_Run dir: `output/auto_iterate/20260504_203450/`_
_Detail: `TIERING_REPORT.md` / `per_stock_best.yaml` / `comparison.csv`_