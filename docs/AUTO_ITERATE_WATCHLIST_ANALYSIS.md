# Watchlist Failure Mode Analysis

來源 run：`output/auto_iterate/20260424_133629/TIERING_REPORT.md`
分析範圍：Takeshi (12) + Katie (9) + research (18)，去重後 38 檔（1301 重複，0050/2379/3034/3008/4938/3231 不在 TIERING_REPORT）。

## 分類規則

| 代碼 | 條件 |
|------|------|
| PASS_C | Tier C（已通過，但部位上限 15%） |
| LOW_SAMPLE | n_trades < 5（樣本不足，主要 fail mode） |
| LOW_PF | PF_lower < 0.8 且 n ≥ 5（無統計顯著邊緣） |
| LOW_EXP | expectancy < 1%（理論上若 n 夠也不值得做） |
| HIGH_DD | max DD > 30% |
| NO_DATA | 沒出現在 TIERING_REPORT |

> 註：TIERING_REPORT 已合併失敗原因，這裡按「最致命的單一原因」歸類；HIGH_DD 與 LOW_PF 可能並存。

---

## Summary by Watchlist

| List | Total | PASS_C | LOW_SAMPLE | LOW_PF | LOW_EXP | HIGH_DD | NO_DATA |
|------|-------|--------|------------|--------|---------|---------|---------|
| Takeshi | 12 | 2 | 6 | 3 | 0 | 1* | 0 |
| Katie | 9 | 2 | 6 | 0 | 0 | 0 | 0 |
| research | 18 | 7 | 3 | 2 | 0 | 0 | 6 |

\* 6770 同時 LOW_PF + HIGH_DD，這裡計入 HIGH_DD（更致命）。
PASS_C 重疊：1301 在兩張清單都算 LOW_SAMPLE；4958 (Takeshi)、1560/2330 (Katie)、2317/2308/2360/3017/2383/4958/6515 (research) 為 PASS_C。

---

## By Failure Mode

### PASS_C — 已通過但部位上限 15%（共 10 檔）

可立即用，但 margin 不夠厚，需 paper trade 3 個月再放大。

- **2330** 台積電 / 半導體權值 — momentum_hold, exp=+4.4%, PF=6.70, n=7, DD=-9.6%
- **2317** 鴻海 / 半導體權值 — chip_momentum, exp=+9.8%, PF=11.45, n=7, DD=-11.7%
- **2308** 台達電 / 半導體權值 — donchian_breakout, exp=+4.6%, PF=3.34, n=12, DD=-18.0%
- **2337** 旺宏 / 記憶體 — chip_momentum, exp=+10.8%, PF=7.55, n=9, DD=-24.0%
- **2383** 台光電 / CCL — donchian_breakout, exp=+13.8%, PF=inf, n=6, DD=-11.1%
- **2360** 致茂 / 半導體設備 — donchian_breakout, exp=+5.0%, PF=6.41, n=11, DD=-13.6%
- **3017** 奇鋐 / 散熱（AI 概念）— donchian_breakout, exp=+14.4%, PF=inf, n=5, DD=-18.2%
- **6515** 穎崴 / 半導體測試 — donchian_breakout, exp=+8.0%, PF=4.73, n=11, DD=-21.7%
- **4958** 臻鼎-KY / 軟板 — donchian_breakout, exp=+11.2%, PF=5.37, n=5, DD=-18.5%
- **1560** 中砂 / 半導體耗材 — mean_reversion, exp=+10.4%, PF=7.36, n=5, DD=-12.9%

觀察：donchian_breakout 是最常見的 PASS_C 模板（6/10），全部命中半導體鏈。

---

### LOW_SAMPLE — 樣本太少無法評估（共 14 檔）

test 期間 n_trades < 5，多為大型權值股或低波動傳產，現有模板進場條件太嚴。

- **1301** 台塑 / 傳產塑化 — trend_pullback, n=1, exp=+19.5%（單筆獲利）
- **1326** 台化 / 傳產塑化 — trend_pullback, n=2, exp=+17.7%
- **1303** 南亞 / 傳產塑化 — momentum_hold, n=1, exp=+4.5%
- **6505** 台塑化 / 傳產塑化 — momentum_hold, n=1, exp=+3.0%
- **1809** 中釉 / 傳產陶瓷 — momentum_hold, n=3, exp=+7.5%
- **2002** 中鋼 / 傳產鋼鐵 — donchian_breakout, n=2, exp=-4.8%（負期望）
- **1227** 佳格 / 食品 — chip_momentum, n=1, exp=-2.9%
- **2454** 聯發科 / 半導體權值 — trend_pullback, n=1, exp=+18.8%
- **2303** 聯電 / 半導體權值 — mean_reversion, n=1, exp=+14.5%
- **2426** 鼎元 / LED — momentum_hold, n=2, exp=+15.6%
- **9940** 信義 / 仲介 — chip_momentum, n=2, exp=+0.2%
- **2412** 中華電 / 電信 — mean_reversion, n=2, exp=+3.6%
- **2324** 仁寶 / NB ODM — mean_reversion, n=1, exp=+0.2%
- **2344** 華邦電 / 記憶體 — mean_reversion, n=1, exp=+3.7%
- **2408** 南亞科 / 記憶體 — donchian_breakout, n=4, exp=+8.1%（差 1 筆達標）
- **6271** 同欣電 / 半導體封測 — trend_pullback, n=3, exp=+6.2%
- **2382** 廣達 / NB ODM — momentum_hold, n=3, exp=+3.3%
- **3037** 欣興 / PCB — trend_pullback, n=1, exp=+11.9%
- **1802** 台玻 / 傳產玻璃 — trend_pullback, n=2, exp=+15.7%
- **2327** 國巨 / 被動元件 — trend_pullback, n=0（完全沒進場）

觀察：**14 檔都集中在大型權值股（2330 等級）+ 慢牛傳產**。trend_pullback / momentum_hold / mean_reversion 對這類低波動標的觸發太少。

---

### LOW_PF — 有交易但無統計邊緣（共 3 檔）

n ≥ 5 但 PF_lower < 0.8，模板選錯方向。

- **2345** 智邦 / 網通 — donchian_breakout, exp=+4.1%, PF=2.03, n=9, **PF_lower=0.36**
- **3711** 日月光投控 / 半導體封測 — donchian_breakout, exp=+2.7%, PF=2.08, n=14, **PF_lower=0.48**
- **6669** 緯穎 / 伺服器 — donchian_breakout, exp=+4.8%, PF=4.60, n=7, **PF_lower=0.66**

觀察：都是 donchian_breakout 失敗。3711/2345 在波段大但 noise 也大，breakout 假訊號多。

---

### HIGH_DD — 回撤過大（共 1 檔）

- **6770** 力積電 / 記憶體代工 — chip_momentum, exp=+0.9%, PF=1.08, n=17, **DD=-31.4%**, PF_lower=0.16
  → 同時 LOW_EXP + LOW_PF + HIGH_DD，是最徹底的 fail。

---

### LOW_EXP — 期望值過低（共 0 檔獨立發生）

均已被 LOW_PF 或 HIGH_DD 涵蓋。

---

### NO_DATA — 不在 TIERING_REPORT（共 6 檔）

可能是資料缺失或 universe 篩除。

- **2379** 瑞昱 / 半導體 IC 設計
- **3034** 聯詠 / 半導體 IC 設計
- **3008** 大立光 / 光學
- **4938** 和碩 / NB ODM
- **3231** 緯創 / NB ODM（AI 伺服器）
- **0050** 元大台灣50 / ETF（可能 ETF 被排除）

→ 需先確認為何沒被處理（資料可下載性 / universe filter）。

---

## Recommended Template Targets

基於失敗模式分布（**LOW_SAMPLE 佔 14/38 = 37%** 是首要痛點），建議優先補以下 3-5 個模板：

### 1. `volume_breakout`（首要）— 解 LOW_SAMPLE 大型權值股
**目標**：1301, 1326, 1303, 6505, 2454, 2303, 2002, 2412, 1227, 2324, 2344
**邏輯**：5 日均量 > 20 日均量 ×2 + 收漲突破前 N 日高 → 進場，hold 5-10 天。
這類大型股缺的是「事件型」催化劑，不是趨勢延續，short-period 才能擠出 n_trades。

### 2. `gap_continuation`（首要）— 解 LOW_SAMPLE 半導體權值
**目標**：2454, 2303, 2408, 2344, 6271, 2382, 3037
**邏輯**：跳空 ≥ 2% + 量能放大 → T+1 進場吃缺口延續，3-5 日 trailing stop。
半導體權值股法說/月營收公佈日常常 gap，現有模板幾乎吃不到。

### 3. `low_vol_pullback`（次要）— 解 LOW_SAMPLE 傳產
**目標**：1301, 1326, 1303, 6505, 1809, 2002, 1802, 9940, 2412
**邏輯**：ATR% 低於分位數 30% 的標的，當日 RSI < 35 + 站上 60 日均線 → 進場，目標前高。
傳產股波動小，trend_pullback 用 ATR 倍數的停利停損會被噪聲打掉，要用相對低分位的「靜止彈跳」。

### 4. `noise_filtered_breakout`（次要）— 解 LOW_PF
**目標**：2345, 3711, 6669
**邏輯**：在 donchian 突破基礎上加 ADX > 25 + 60 日波動率 < 中位數，過濾假突破。
這三檔現有 donchian 進場太頻繁，需要更嚴的 regime filter。

### 5. `event_driven`（探索性）— 解 LOW_SAMPLE 慢牛
**目標**：1227, 9940, 2412, 2324, 1809
**邏輯**：除權息前 N 日 / 月營收公佈前 N 日 buy → hold 到事件後 K 日 sell。
這類股票技術面幾乎沒訊號，只能靠 fundamental calendar。需先補資料源。

---

## 建議下一步

1. **先做 volume_breakout + gap_continuation**：覆蓋 LOW_SAMPLE 14 檔的 ~80%，是 ROI 最高的補洞。
2. **NO_DATA 6 檔**：跑一次 fetch + 確認 universe filter，可能多出幾檔合規候選。
3. **6770 力積電**：建議從 universe 移出（記憶體景氣循環+負期望，不是模板問題）。
4. **PASS_C 10 檔**：可同步啟動 paper trading（依 SPEC 3 個月觀察期）。
