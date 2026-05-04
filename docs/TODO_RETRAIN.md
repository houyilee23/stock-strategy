# TODO：重新訓練 auto_iterate（家裡 PC 處理）

最後更新：2026-05-04

## 為什麼要重訓？

2026-05-04 的 session 中把回測起點從 `2017-01-01` 延長到 `2010-01-01` 後發現：

**2360 致茂 17 年完整年度交易分布**揭露：
```
2010-2015：5 年中 4 負（勝率 0%~50%）  ← 策略適應不良
2016-2020：5 年中 1 負                    ← 開始穩定
2021：    1 個負年
2022-2026：5 年全正（勝率 75%~100%）     ← 黃金期
```

**核心問題**：
- 目前 `config/per_stock_recommendations.yaml` 中的 Tier 與 `best_params` 都是 `merged_20260426_120034` 那次跑的
- 那次的 train 期 = 2017-2022、test 期 = 2023-2024
- 完全沒看過 2010-2016 的市場
- 加上去之後，許多 A-tier 個股的 PF / 勝率可能下降，部分可能掉到 B 或 C

換句話說：**目前的 Tier 是「過度樂觀的近期 fit」，未通過長期 robustness check。**

---

## 重訓的目標

把訓練/測試窗口擴大，挑出**真正穩定的 template + params**：

### 建議新窗口（A 方案）
```
train 期：2010-01-01 ~ 2020-12-31   (11 年，含 2011 歐債、2015 中港股災、2018-2019 小空頭)
test 期： 2021-01-01 ~ 2026-04-30   (5 年 OOS)
```

### 替代方案（B：滾動驗證）
```
fold 1: train 2010-2015 → test 2016-2018
fold 2: train 2010-2018 → test 2019-2021
fold 3: train 2010-2021 → test 2022-2024
取三個 fold 都穩定的標的才升 Tier
```

A 方案最簡單；B 方案最嚴謹但工程量大。我建議先試 A。

---

## 執行步驟

### 1. 修改 train/test 窗口
編輯 `src/strategy/auto_iterate/runner.py` 或 CLI 參數：

```bash
python main.py auto_iterate \
    --universe all \
    --trials-per-pair 80 \
    --train-start 2010-01-01 \
    --train-end 2020-12-31 \
    --test-start 2021-01-01 \
    --test-end 2026-04-30
```

⚠️ 注意 `main.py:cmd_auto_iterate` 已支援 `--train-start` flag，看 `main.py:309` 起。

### 2. 預估時間
- 80 stocks × 9 templates × 80 trials × 11 年資料 ≈ **2~5 小時**
- 看家裡 PC CPU 而定。可以晚上跑、隔天看結果。
- `auto_iterate` 支援 resume：中斷不怕，加 `--resume <run_id>` 接著跑。

### 3. 跑完後

```bash
# 把結果 merge（如果分多個 run）
python -m src.strategy.auto_iterate.merge_runs <run_id_1> [<run_id_2>...]

# 重新生成 per_stock_recommendations.yaml
python -m src.strategy.auto_iterate.final_report <merged_run_id>
```

`config/per_stock_recommendations.yaml` 會被覆寫成新的 Tier 表。

### 4. 驗證

跑 signals 看新 Tier 分佈：
```bash
python main.py signals --list research
```
觀察：
- 哪些原本 A-tier 掉到 B/C/F？（這些是「過去 5 年好運」的標的）
- 哪些原本 F-tier 升上來？（11 年都穩定的可能浮現）
- S-tier 還剩幾檔？（極可能只剩 0~1 檔）

### 5. 跑完整套 daily_update.bat 重新生成所有報告

```bash
scripts\daily_update.bat
```

→ README、per_stock markdown、docs/index.html、docs/stock/*.html 全部會用新 Tier 重畫。

---

## 心理準備

**重訓後可能會看到的「壞消息」**：

1. **大部分 A-tier 變 B 或 C** — 11 年穩定比 5 年穩定難很多
2. **S-tier 可能消失** — 2317 鴻海原本是唯一 S，11 年驗證可能掉到 A 或 B
3. **F-tier 數量增加** — 更多檔被認定為「策略不適合」
4. **Tradeable 標的減少** — Takeshi/Katie/research 中可進場的可能從 28 檔降到 15-20 檔
5. **整體預期 CAGR 下調** — 但這是真實的，不是悲觀

**好消息**：
- 留下來的 A/B-tier 是**真的穩定**，未來 confidence 提升
- 部位上限可以更安心地照建議放
- 失敗模式更被 capture（早期負年告訴你策略在哪種市場會崩）

---

## 與限價單機制的關係（重要）

2026-05-04 已實作**限價單機制 v0.1**（[docs/LIMIT_ORDER_V0_1.md](LIMIT_ORDER_V0_1.md)）：
- 2 個 template 支援：`low_vol_pullback`、`mean_reversion`
- 信號 T 收盤後輸出隔日掛單目標價（target_buy / target_tp / target_sl）
- Backtester 用 OCO 限價單模擬真實成交
- 全部用 adj_close 跑（與 BNH benchmark 公平比較）

**結果**：MaxDD 大幅降低（2360 -32% → -15%、1560 -26% → -11.5%），持倉期 CAGR 大幅提升（2360 15% → 46%、1560 41% → 112%）。

**對重訓的影響**：
- 目前的 `best_params` 是用**舊機制 + raw exec** 優化的，未必是新機制下最佳
- 重訓建議納入「限價單機制 + adj-only」一起跑，找出新機制下的真實 robust 參數
- 重訓時也建議擴展更多 template 支援限價單（donchian_breakout、trend_pullback、bollinger_squeeze）

**順序建議**：
```
1. 先跑 1~2 週 Phase A，驗證限價單訊號實單可用
2. 擴展更多 template 加入限價單機制（每個 ~ 1 小時）
3. 一次性大重訓：2010+ 資料 + 限價單 + 所有可預掛 template
4. 部署新 best_params + 切到 Phase B
```

## 何時做？

**不急**。建議：

1. **先讓 Phase A 跑一週**，驗證 daily_update.bat 穩定運作
2. **再花一個週末**（兩個夜晚）跑重訓
3. **跑完一週**觀察新 Tier 給的訊號是否符合預期
4. **再切到 Phase B** push GitHub，曝光給手機

---

## 相關檔案

- `src/strategy/auto_iterate/runner.py` — 主流程
- `src/strategy/auto_iterate/templates.py` — 9 個策略模板
- `src/strategy/auto_iterate/tiering.py` — Tier 評級邏輯
- `src/strategy/auto_iterate/final_report.py` — 寫 per_stock_recommendations.yaml
- `src/strategy/auto_iterate/merge_runs.py` — 合併多個 run
- `output/auto_iterate/merged_20260426_120034/` — **目前在用的 run，重訓前建議備份成 `archive/`**
- `config/per_stock_recommendations.yaml` — 目前的 Tier 表（會被覆寫）

## 重訓前的備份建議

```bash
# 備份目前的 merged run，避免 final_report 被覆寫後找不回
cp -r output/auto_iterate/merged_20260426_120034 archive/auto_iterate_2017train_baseline

# 備份目前的 recommendations
cp config/per_stock_recommendations.yaml archive/per_stock_recommendations_2017train.yaml
```

這樣重訓後可以 diff 對比「2017 train vs 2010 train」哪些 Tier 改變了。
