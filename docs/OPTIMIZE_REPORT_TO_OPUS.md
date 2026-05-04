# Optimize Round 1 報告

## TL;DR
- 跑了 37 trials，耗時 0.7 分鐘
- 最佳 in-sample score = 6.3112，out-of-sample score = -10.0000
- overfit 警訊：有
- 建議套用 best_params：否（理由見下方）

## 最佳參數 diff

| 參數 | 目前 | 最佳 | 變化 |
|---|---|---|---|
| atr_period | 14 | 10 | ✓ |
| atr_stop_k | 2.5 | 2.75 | ✓ |
| bollinger_k | 2.0 | 1.75 | ✓ |
| bollinger_period | 20 | 25 | ✓ |
| ma_long | 200 | 250 | ✓ |
| ma_short | 50 | 100 | ✓ |
| max_hold_days | 120 | 120 |  |
| rsi_overbought | 80 | 75 | ✓ |
| rsi_oversold | 40 | 50 | ✓ |
| rsi_period | 14 | 21 | ✓ |
| trend_break_days | 2 | 5 | ✓ |
| volume_ma_period | 20 | 10 | ✓ |
| volume_min_ratio | 0.8 | 1.4 | ✓ |

## In-Sample vs Out-of-Sample

| 指標 | Train (2017-2022) | Test (2023-2026) | 衰減 |
|---|---|---|---|
| median PF    | 6.311 | 2.339 | -62.9% |
| median MaxDD | 8.6% | 5.9% | -30.6% |
| n_active     | 3 | 1 | — |

## Top-5 Trial 對照

| trial | score | ma_long | ma_short | rsi_period | rsi_oversold | bollinger_period | bollinger_k | volume_ma_period | volume_min_ratio | atr_period | atr_stop_k | trend_break_days | rsi_overbought | max_hold_days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 43 | 6.3112 | 250.0 | 100.0 | 21.0 | 50.0 | 25.0 | 1.75 | 10.0 | 1.4 | 10.0 | 2.75 | 5.0 | 75.0 | 120.0 |
| 44 | 5.8818 | 250.0 | 100.0 | 21.0 | 50.0 | 25.0 | 1.75 | 10.0 | 1.4 | 10.0 | 3.0 | 5.0 | 75.0 | 120.0 |
| 19 | 5.5616 | 250.0 | 100.0 | 21.0 | 50.0 | 25.0 | 2.0 | 10.0 | 1.5 | 10.0 | 2.75 | 4.0 | 75.0 | 120.0 |
| 20 | 5.5616 | 250.0 | 100.0 | 21.0 | 50.0 | 25.0 | 1.75 | 10.0 | 1.5 | 10.0 | 2.75 | 5.0 | 75.0 | 120.0 |
| 22 | 5.5616 | 250.0 | 100.0 | 21.0 | 50.0 | 25.0 | 1.75 | 10.0 | 1.5 | 10.0 | 2.75 | 5.0 | 75.0 | 120.0 |

## 我的判斷

- overfit 警訊：**有（test < train × 0.5）**
- top-5 敏感性：低（穩定）
- 參數差異：共 12 個參數與目前 strategy.yaml 不同

- 不建議：**暫不套用 best_params**
  - 原因：out-of-sample 績效衰減超過 50%，有 overfit 風險；test 段只有 1 檔有效交易，樣本不足
  - 建議：繼續收集資料，下次優化加入更多歷史或調整 search_space

## 下一步
- 人工 review best_params.yaml，決定是否手動套入 config/strategy.yaml
- 若套用後跑 `python main.py backtest --all` 驗證全 universe 效果
- 本次 run_id：`20260423_133513`
