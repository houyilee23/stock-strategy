# Auto-Iterate Final Report — 20260505_194813

**Generated**: 自動執行（Auto Mode）— Q5=(b) 激進改寫授權範圍內
**Universe**: 7 檔（涵蓋 Takeshi / Katie / Research / Research_todo 去重後合集）
**0050 test CAGR**: +27.0%

## 1. Tier 分布

| Tier | 數量 | 部位上限 | 描述 |
|------|------|----------|------|
| S | 0 | 100% | ROBUST：訊號模式直接用 |
| A | 0 | 50% | STRONG：可用，建議 50% 部位 |
| B | 0 | 30% | MODERATE：可用，30% 部位 + 嚴格 trailing stop |
| C | 2 | 15% | WEAK：紙上交易 3 個月再啟用，最大 15% |
| F | 5 | 0% | FAIL：移出 universe，建議走組合模式或買 0050 |

**可操作標的（S+A+B+C）= 2 / 7**  （目標 ≥ 20）

## 2. Watchlist 覆蓋率

### Takeshi — 可操作 0 / 0

（無可操作）

### Katie — 可操作 2 / 7

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 1560 | 中砂 | C | mean_reversion | 15% | +7.1% | 6.93 | 7 |
| 2330 | 台積電 | C | gap_continuation | 15% | +1.1% | 1.55 | 42 |

### universe — 可操作 2 / 7

| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |
|-------|------|------|------|----------|-----|----|---|
| 1560 | 中砂 | C | mean_reversion | 15% | +7.1% | 6.93 | 7 |
| 2330 | 台積電 | C | gap_continuation | 15% | +1.1% | 1.55 | 42 |

### research_todo — 可操作 0 / 0

（無可操作）

## 3. 新模板貢獻分析（Phase 3 + Phase 6 加入）

| 模板 | 用途 | tradeable 命中數 |
|------|------|------------------|
| volume_breakout | LOW_SAMPLE 大型權值股（去 trend filter） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| gap_continuation | 事件驅動跳空 + 收紅 | 1 |
| low_vol_pullback | 傳產慢牛低波動回檔 | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| bollinger_squeeze | BB 壓縮後爆量突破 | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| chip_streak | 三大法人連續 ≥N 天買超（台股法人持續性 alpha） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |
| monthly_revenue_event | 月營收 YoY > X% + 公布日跳空（台股獨有日曆事件） | 0  ⚠️ 0 命中（其他模板覆蓋更好） |

**新模板貢獻**：1 / 2 tradeable （舊模板：1）

### 新模板拯救的個股（best_template ∈ 新四模板）

| Stock | 名稱 | Tier | 模板 | Exp | PF_lower |
|-------|------|------|------|-----|----------|
| 2330 | 台積電 | C | gap_continuation | +1.1% | 0.72 |

## 4. 各 Tier 完整清單

### Tier C （2 檔）

| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |
|-------|------|------|-----|----|---|----|----------|----------|
| 1560 | 中砂 | mean_reversion | +7.1% | 6.93 | 7 | -11.1% | 0.97 | A_new=NA B=NA C=X |
| 2330 | 台積電 | gap_continuation | +1.1% | 1.55 | 42 | -29.2% | 0.72 | A_new=NA B=O C=X |

## 5. 給 Takeshi/Katie 的行動建議

### 立即可用（S+A）
（無）

### 條件可用（B），加嚴格 trailing stop
（無）

### 觀察（C），先紙上交易 3 個月
- **1560 中砂** (mean_reversion) — Tier C, 最大部位 15%
- **2330 台積電** (gap_continuation) — Tier C, 最大部位 15%

## 6. 已知限制與後續建議

- **未達目標**：tradeable=2 < 15。下一輪建議：
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

### BNH_A （1 檔）

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | Sharpe | 股息率 | 部位上限 |
|-------|------|------|---------|--------|--------|--------|----------|
| 2303 | 聯電 | +23.8% | +6.7% | 46.2% | 0.83 | 4.0% | 30% |

### BNH_B （1 檔）

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | Sharpe | 股息率 | 部位上限 |
|-------|------|------|---------|--------|--------|--------|----------|
| 2324 | 仁寶 | +15.7% | -1.5% | 26.7% | 0.80 | 4.5% | 20% |

### F-tier 中也不適合 BNH （3 檔）

這些股票既無法 timing 也輸 0050，建議改走組合模式或直接買 0050。

| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | 股息率 |
|-------|------|------|---------|--------|--------|
| 2426 | 鼎元 | +11.7% | -5.5% | 64.4% | 2.3% |
| 2344 | 華邦電 | +8.1% | -9.1% | 62.7% | 1.9% |
| 9940 | 信義 | +5.6% | -11.6% | 39.9% | 5.6% |

**BNH 救回統計**：2 / 5 F-tier 個股可改走 BNH。

---
_Run dir: `output/auto_iterate/20260505_194813/`_
_Detail: `TIERING_REPORT.md` / `per_stock_best.yaml` / `comparison.csv`_