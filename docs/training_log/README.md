# Training Log

本目錄保存每次 auto_iterate retrain 的執行紀錄與重要決策，方便日後回頭
分析「哪次跑了什麼、為什麼這樣設定、結果有沒有比上次好」。

## 檔案結構

```
docs/training_log/
├── README.md                          ← 本檔（總覽）
├── YYYY-MM-DD.md                      ← 該日所有 retrain 的逐筆紀錄
└── SCHEDULE.md                        ← 自動排程設定
```

每次跑 `scripts/retrain_extended_history.py` 都會自動 append 一段到當日
log 檔，內容包括：訓練/測試區間、trials/pair、universe、結果碼、耗時。

## 結構化索引

`output/auto_iterate/INDEX.csv` 與 `INDEX.md` 把每個 run dir 的
summary.md 解析、彙整：

| 欄位 | 說明 |
|---|---|
| run_id | 自動產出（YYYYMMDD_HHMMSS） |
| started_at | run dir 名稱推算 |
| kind | merged / full_retrain / batch_retrain / phase / small_test |
| train_start / train_end | 訓練區間 |
| test_start / test_end | 測試區間 |
| n_pairs | (stock × template) pairs |
| n_pass / n_fail / n_dd_breach / n_insufficient | verdict 分布 |
| elapsed_min | 耗時（分鐘） |
| benchmark_0050_test_cagr | 0050 同期 CAGR |

更新：跑 `python scripts/build_run_index.py`（retrain_extended_history.py
跑完會自動 call 一次）。

## 為什麼有「擴大歷史區間」這個任務？

原訓練視窗 **2017-01-01 ~ 2023-12-31** 完全錯過：

- **2011 歐債危機**（台股 -28%）
- **2015 中港股災 + 8 月閃崩**（台股 -19%）
- **2018-2019 中美貿易戰小空頭**

→ 目前的 tier 是「過度樂觀的近期 fit」，未經長期 robustness 驗證。

新視窗（`retrain_extended_history.py` 預設）：

- **Train 2010-01-01 ~ 2020-12-31**（11 年，含三段壓力）
- **Test 2021-01-01 ~ 2026-04-22**（5.3 年 OOS）

跑完後可比較：哪些 tier S/A 在加入長歷史後降級、哪些反而升級。

## 如何啟動 retrain

### 手動（前景跑，可中斷）

```bash
# 完整 retrain（全 universe × 全 templates × 100 trials，預計 8-24 hr）
python scripts/retrain_extended_history.py

# Pilot：只跑 Takeshi list（26 檔 × 全 templates × 100 trials，預計 1-2 hr）
python scripts/retrain_extended_history.py --pilot

# 自訂：只跑 5 個指定 templates
python scripts/retrain_extended_history.py --templates T1,T4,T6,T9 --trials 80

# Resume（從上次中斷續跑）
python scripts/retrain_extended_history.py --resume 20260520_023045
```

### 排程（Windows Task Scheduler）

詳見 `SCHEDULE.md`。建議每週一次（週日凌晨）。

## 跑完後檢查清單

1. **看 `output/auto_iterate/<新 run_id>/summary.md`** — verdict 分布
2. **看 `INDEX.md`** — 跟舊區間比，PASS 比例變化
3. **用 `scripts/compare_recommendations.py`** 比較新舊 recommendations.yaml
4. **決定是否套用**：`scripts/apply_retrain_upgrades.py <new_run_id>`
5. **若 tier 變動大，重 publish HTML**：`scripts/build_html.py`
