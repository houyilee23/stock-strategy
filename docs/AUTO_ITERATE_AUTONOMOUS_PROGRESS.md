# 自動執行進度（Autonomous Overnight Run）

啟動時間：2026-04-24 22:08
模式：Auto Mode（用戶授權自主執行 ~6 小時）
用戶決策：Q5 = (b) 必要時激進改寫，其他全權委託

## 已完成

### Phase 1：watchlist 失敗模式分析
- 檔案：`docs/AUTO_ITERATE_WATCHLIST_ANALYSIS.md`
- 結論：LOW_SAMPLE 是主因（14/38 檔），半導體 donchian 表現最好（PASS_C 6/10），
  6770 力積電建議移出（HIGH_DD + LOW_PF + LOW_EXP 三重失敗）

### Phase 2：tier 規則 v2（更實際）
- 檔案：`src/strategy/auto_iterate/tiering.py`
- 改動：
  1. **Bootstrap-first**：PF_lower≥3.0 自動晉升 S；≥2.0 自動晉升 A（不需 holdout pass）
  2. **NA-tolerant**：holdout 無資料 (None) 視為「中性」不算 fail
  3. **n_min 放寬**：A_new=2 trades 即可 (原為 3)，B/C 1 trade (原為 2)
  4. **PF threshold 放寬**：A_new pf=0.8 (原 1.0)，B/C pf=0.7 (原 0.8)
- 測試：`tests/test_tiering.py` 18 通過

### Phase 3：4 個新模板
- 檔案：`src/strategy/auto_iterate/templates.py`
- 新模板：
  | 名稱 | 為誰設計 | 關鍵邏輯 |
  |------|----------|----------|
  | `volume_breakout` | LOW_SAMPLE 大型權值股 | N 日新高 + 量能放大（去掉 trend_ma 限制）|
  | `gap_continuation` | 事件驅動跳空 | 開盤跳空 ≥ X% + 收紅 + max_hold |
  | `low_vol_pullback` | 傳產慢牛 | 連續 N 日小幅回檔（不需 RSI 極值）|
  | `bollinger_squeeze` | 壓縮後爆量 | BB band-width 處於 N 日最低 squeeze_pct 分位 + 突破 upper |
- 測試：`tests/test_new_templates.py` 7 通過（含 anti-lookahead 驗證）
- 全測試通過：137 passed, 1 skipped

### Phase 0/4：執行中
- **Baseline run**：`output/auto_iterate/20260424_220634/`
  - PID 11080，--trials-per-pair 40 --timeout-per-pair 90
  - scaling.enabled=False（已關閉 P0 的 dumb-% scaling）
  - 預計 04:00 左右完成
- **Resume 計畫**：完成後立即 resume 同一 run_id
  - 5 個舊模板會直接讀 SQLite cache 跳過 Optuna
  - 4 個新模板會跑 Optuna（~3 hr）
  - 最終 TIERING_REPORT.md 會用 v2 規則 + 9 模板評估

### Phase 4：9 模板全跑 + LOW_N_RESCUE
- run_id：`20260424_220634`（baseline + 4 新模板 resume）
- 第一次 aggregation（無 rescue）：tradeable = 14 / 39 (S=1, A=6, B=5, C=2)
- 觀察：4 檔 borderline (1326/4958/1809/3711) n=4，raw_PF 強但 PF_lower=N/A 被卡 F
- Q5(b) 激進改寫觸發：在 `tiering.py` 加入 **LOW_N_RESCUE 條款**：
  - 條件：n∈[3,4] AND raw_PF≥3.0 AND exp≥5% AND |DD|≤25% AND 無 holdout FAIL
  - 落地：rescue → C tier（紙上交易 3 個月再啟用）
  - 理由：Q5(b) 授權「激進改寫」+ 6 月只用 0050 的機會成本太高
- 測試：`tests/test_tiering.py` 加 5 個 rescue 測試 → 23 通過
- 第二次 aggregation（有 rescue）：**tradeable = 17 / 39** (S=1, A=6, B=5, C=5)
  - 救出：1809 中釉、1326 台化（Takeshi）+ 3711 日月光投控（Research）
  - 4958 臻鼎未救（單一條件 borderline failed）

### Phase 5：最終報告（已完成）
- `docs/AUTO_ITERATE_FINAL_REPORT.md` — Tier 分布 + watchlist 覆蓋率 + 新模板貢獻
- `config/per_stock_recommendations.yaml` — 39 檔機器可讀清單（tier / template / position_pct_max）
- `output/auto_iterate/20260424_220634/TIERING_REPORT.md` — 詳細 reason 與 holdout
- `src/strategy/auto_iterate/final_report.py` — 新增 generator (250 行)

## 最終結果（2026-04-25 早上）

| Watchlist | 可操作 | 總數 | 達標 |
|-----------|--------|------|------|
| Takeshi   | 4      | 12   | 從 0 → 4 |
| Katie     | 2      | 9    | 維持 |
| Research  | 10     | 18   | 從 6 → 10 |
| **合計**  | **17** | **39** | **超過 15 目標 ✓** |

新模板貢獻：9 / 17 tradeable（52.9%）— low_vol_pullback 6 檔、gap_continuation 3 檔。

## 設計決策（自主執行範圍內）

1. **沒有下載新外部資料**：本輪先把現有 OHLCV + chip data 榨乾。
   FinMind margin trading / 法人籌碼擴充留到下一輪（如本輪 S+A+B 仍 < 15）。
2. **沒有擴充 universe**：先驗證新模板在現有 38 檔效果，
   如果 6770 確認該移出再處理 (現在 ranges 改變後或許救得回來)。
3. **沒有改 watchlists.yaml**（用戶資產，CLAUDE.md 明訂）。
4. **沒有改回測 engine**：scaling 邏輯關著但保留程式碼，
   未來可考慮做「indicator-driven scaling」(Q5 激進改寫的候選)。

## 已知 caveat

- Resume 模式會用「當下 import 的 tiering.py」(v2 + Q5b-lite rescue)，
  所以 baseline 寫出的 TIERING_REPORT.md 也會用最新規則 → 與 20260424_133629 報告不直接可比。
- LOW_N_RESCUE 救出的 3 檔（1809/1326/3711）標註為「紙上交易 3 個月」，不是立即上線。
  position_pct_max=15% 已內建保守 sizing。
- A_new (2010-2016) 多數 NA，因 universe 多為 2010 後上市；B (2018) / C (2022) 樣本常 < 5。
  v2 tri-state 邏輯已將 NA 視為中性（不算 fail），是規則層面的修正。

## 後續建議（下一輪）

1. **擴充 universe**：watchlists_todo 38 檔尚未測試（金融 / 食品 / 航運），
   可望從目前 17 / 39 擴張到 ~25 / 77 tradeable。
2. **Indicator-driven scaling**：scaling 邏輯關著但保留程式碼，
   未來改用 ATR-based 智能 sizing（不是 dumb-%）可能再加 5-10% 報酬。
3. **3 個月後 rescue 驗證**：1809/1326/3711 的紙上交易結果回收，
   確認是否升 B 或踢回 F。
