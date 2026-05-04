# Auto-Iterate Final Report — merged_20260505_023327

**Generated**: 自動執行（Auto Mode）— Q5=(b) 激進改寫授權範圍內
**Universe**: 15 檔（涵蓋 Takeshi / Katie / Research / Research_todo 去重後合集）
**0050 test CAGR**: +27.0%

## 1. Tier 分布

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 1 | 100% | ROBUST：訊號模式直接用 |
| A | 2 | 50% | STRONG：可用，建議 50% 部位 |
| B | 3 | 30% | MODERATE：可用，30% 部位 + 嚴格 trailing stop |
| C | 2 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 7 | 0% | FAIL：移出 universe，建議走組合模式或買 0050 |

**可操作標的（S+A+B+C）= 8 / 15**  （目標 ≥ 20）

## 2. Watchlist 覆蓋率

### Takeshi — 可操作 8 / 15

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 8046 | 8046 | S | low_vol_pullback | 100% | +6.0% | 19.30 | 10 |
| 1303 | 南亞 | A | gap_continuation | 50% | +11.5% | 7.68 | 9 |
| 1301 | 台塑 | A | gap_continuation | 50% | +5.6% | N/A | 6 |
| 2369 | 2369 | B | low_vol_pullback | 30% | +5.6% | 4.58 | 13 |
| 6770 | 力積電 | B | low_vol_pullback | 30% | +4.5% | 9.19 | 9 |
| 1326 | 台化 | B | low_vol_pullback | 30% | +3.5% | 7.31 | 8 |
| 2337 | 旺宏 | C | monthly_revenue_event | 15% | +18.0% | N/A | 3 |
| 3189 | 3189 | C | chip_momentum | 15% | +5.4% | 2.71 | 25 |

### Katie — 可操作 1 / 1

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 1301 | 台塑 | A | gap_continuation | 50% | +5.6% | N/A | 6 |

### universe — 可操作 8 / 15

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 8046 | 8046 | S | low_vol_pullback | 100% | +6.0% | 19.30 | 10 |
| 1303 | 南亞 | A | gap_continuation | 50% | +11.5% | 7.68 | 9 |
| 1301 | 台塑 | A | gap_continuation | 50% | +5.6% | N/A | 6 |
| 2369 | 2369 | B | low_vol_pullback | 30% | +5.6% | 4.58 | 13 |
| 6770 | 力積電 | B | low_vol_pullback | 30% | +4.5% | 9.19 | 9 |
| 1326 | 台化 | B | low_vol_pullback | 30% | +3.5% | 7.31 | 8 |
| 2337 | 旺宏 | C | monthly_revenue_event | 15% | +18.0% | N/A | 3 |
| 3189 | 3189 | C | chip_momentum | 15% | +5.4% | 2.71 | 25 |

### research_todo — 可操作 0 / 0

（無可操作）

## 3. 新模板貢獻分析（Phase 3 + Phase 6 加入）

| 模板 | 用途 | tradeable 命中數 |
|------|------|------------------|
| volume_breakout | LOW_SAMPLE 大型權值股（去 trend filter） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| gap_continuation | 事件驅動跳空 + 收紅 | 2 |
| low_vol_pullback | 傳產慢牛低波動回檔 | 4 |
| bollinger_squeeze | BB 壓縮後爆量突破 | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| chip_streak | 三大法人連續 ≥N 天買超（台股法人持續性 alpha） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| monthly_revenue_event | 月營收 YoY > X% + 公布日跳空（台股獨有日曆事件） | 1 |

**新模板貢獻**：7 / 8 tradeable （舊模板：1）

### 新模板拯救的個股（best_template ∈ 新四模板）

| Stock | 名稱 | Tier | 模板 | Exp | PF_lower |
|-------|------|------|------|-----|----------|
| 8046 | 8046 | S | low_vol_pullback | +6.0% | 5.00 |
| 1303 | 南亞 | A | gap_continuation | +11.5% | 1.63 |
| 1301 | 台塑 | A | gap_continuation | +5.6% | 5.00 |
| 2369 | 2369 | B | low_vol_pullback | +5.6% | 1.82 |
| 6770 | 力積電 | B | low_vol_pullback | +4.5% | 1.77 |
| 1326 | 台化 | B | low_vol_pullback | +3.5% | 1.48 |
| 2337 | 旺宏 | C | monthly_revenue_event | +18.0% | N/A |

## 4. 各 Tier 完整清單

### Tier S （1 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 8046 | 8046 | low_vol_pullback | +6.0% | 19.30 | 10 | -17.2% | 5.00 | A_new=NA B=X C=O |

### Tier A （2 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 1303 | 南亞 | gap_continuation | +11.5% | 7.68 | 9 | -22.7% | 1.63 | A_new=NA B=O C=NA |
| 1301 | 台塑 | gap_continuation | +5.6% | N/A | 6 | -9.3% | 5.00 | A_new=NA B=X C=NA |

### Tier B （3 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 2369 | 2369 | low_vol_pullback | +5.6% | 4.58 | 13 | -21.4% | 1.82 | A_new=NA B=NA C=NA |
| 6770 | 力積電 | low_vol_pullback | +4.5% | 9.19 | 9 | -20.9% | 1.77 | A_new=NA B=NA C=NA |
| 1326 | 台化 | low_vol_pullback | +3.5% | 7.31 | 8 | -8.3% | 1.48 | A_new=NA B=O C=X |

### Tier C （2 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 2337 | 旺宏 | monthly_revenue_event | +18.0% | N/A | 3 | -10.0% | N/A | A_new=NA B=O C=NA |
| 3189 | 3189 | chip_momentum | +5.4% | 2.71 | 25 | -39.6% | 0.92 | A_new=NA B=NA C=NA |

## 5. 給 Takeshi/Katie 的行動建議

### 立即可用（S+A）
- **8046 8046** (low_vol_pullback) — Tier S, 建議部位上限 100%
- **1303 南亞** (gap_continuation) — Tier A, 建議部位上限 50%
- **1301 台塑** (gap_continuation) — Tier A, 建議部位上限 50%

### 條件可用（B），加嚴格 trailing stop
- **2369 2369** (low_vol_pullback) — Tier B, 建議部位 30%
- **6770 力積電** (low_vol_pullback) — Tier B, 建議部位 30%
- **1326 台化** (low_vol_pullback) — Tier B, 建議部位 30%

### 觀察（C），先紙上交易 3 個月
- **2337 旺宏** (monthly_revenue_event) — Tier C, 最大部位 15%
- **3189 3189** (chip_momentum) — Tier C, 最大部位 15%

## 6. 已知限制與後續建議

- **未達目標**：tradeable=8 < 15。下一輪建議：
  1. **Q5(b) 激進改寫**：考慮 multi-template ensemble（≥2 模板同意才進場）
  2. **擴充 universe**：watchlists_todo 共 38 檔尚未測試（金融 / 食品 / 航運）
  3. **Indicator-driven scaling**：重新 enable scaling，但用 ATR-based 智能規則
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

### BNH_S （1 檔）

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | Sharpe | 股息率 | 部位上限 |
|-------|------|------|---------|--------|--------|--------|----------|
| 2382 | 廣達 | +28.7% | +11.5% | 33.6% | 1.00 | 4.6% | 50% |

### F-tier 中也不適合 BNH （6 檔）

這些股票既無法 timing 也輸 0050，建議改走組合模式或直接買 0050。

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | 股息率 |
|-------|------|------|---------|--------|--------|
| 4958 | 臻鼎-KY | +12.7% | -4.5% | 52.3% | 4.2% |
| 1809 | 中釉 | +7.9% | -9.3% | 61.5% | 1.5% |
| 6271 | 同欣電 | +5.7% | -11.5% | 51.6% | 3.0% |
| 2002 | 中鋼 | +0.9% | -16.2% | 48.6% | 3.8% |
| 2408 | 南亞科 | -2.0% | -19.2% | 68.5% | 2.6% |
| 6505 | 台塑化 | -10.5% | -27.7% | 72.6% | 2.5% |

**BNH 救回統計**：1 / 7 F-tier 個股可改走 BNH。

---
_Run dir: `output/auto_iterate/merged_20260505_023327/`_
_Detail: `TIERING_REPORT.md` / `per_stock_best.yaml` / `comparison.csv`_