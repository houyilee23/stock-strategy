# Holdout Validation 跨期驗證報告

**run_id**: `20260423_151107`  
**PASS pairs 驗證數**: 10  
**驗證段**: A=2014-2016（資料不足 2017 前）/ B=2018 / C=2022  
**params**: 凍結自 optuna 最佳解，不重新優化  

## 驗證標準

| 段 | 通過條件 |
|----|---------|
| A（2014-2016，樣本稀） | expectancy >= 1% AND PF >= 1.0 AND n >= 3 |
| B（2018，震盪熊市） | PF >= 0.8 AND MaxDD <= 40% |
| C（2022，熊市）   | PF >= 0.8 AND MaxDD <= 40% |

## 總評定義

| 總評 | 說明 |
|------|------|
| ROBUST | A/B/C 全過 |
| TRAINED-FIT | A 不過（params 對 2017-2023 訓練期過擬合）|
| BEAR-FRAGILE | B 或 C 不過（熊市失效）|
| SURVIVES-BEAR-ONLY | A 不過，B/C 過（熊市可用但更早期不行）|

---

## 完整結果表

| Stock | Template | A_pass | A_exp/PF/n/DD | B_pass | B_PF/DD | C_pass | C_PF/DD | 總評 |
|-------|----------|--------|--------------|--------|---------|--------|---------|------|
| 1560 | trend_pullback | ✗ | -5.5%/?/n=5/-28.8% | ✗ | ?/-8.5% | ✗ | ?/-11.3% | **TRAINED-FIT** |
| 1802 | donchian_breakout | ✗ | -5.3%/?/n=2/-10.4% | ✗ | ?/0.0% | ✗ | ?/-13.2% | **TRAINED-FIT** |
| 2308 | donchian_breakout | ✓ | 4.1%/1.84/n=5/-23.4% | ✗ | 0.28/-18.6% | ✗ | ?/-8.1% | **SURVIVES-BEAR-ONLY** |
| 2330 | donchian_breakout | ✓ | 4.4%/3.90/n=6/-15.2% | ✗ | 0.14/-10.1% | ✗ | ?/0.0% | **SURVIVES-BEAR-ONLY** |
| 2360 | chip_momentum | ✗ | -3.3%/?/n=2/-6.5% | ✗ | ?/-17.2% | ✗ | ?/-19.6% | **TRAINED-FIT** |
| 2383 | chip_momentum | ✗ | -3.3%/0.15/n=10/-29.9% | ✗ | ?/-17.9% | ✗ | ?/-8.5% | **TRAINED-FIT** |
| 3017 | chip_momentum | ✗ | -3.2%/0.29/n=6/-38.6% | ✗ | ?/0.0% | ✗ | 0.26/-31.2% | **TRAINED-FIT** |
| 3711 | chip_momentum | ✗ | N/A/?/n=0/N/A | ✗ | ?/0.0% | ✗ | ?/-11.2% | **TRAINED-FIT** |
| 6515 | trend_pullback | ✗ | N/A/?/n=0/N/A | ✗ | ?/N/A | ✗ | ?/-14.1% | **TRAINED-FIT** |
| 6770 | chip_momentum | ✗ | N/A/?/n=0/N/A | ✗ | ?/N/A | ✗ | ?/-16.8% | **TRAINED-FIT** |

---

## 分組推薦

### 第一線：ROBUST（A/B/C 全過，直接接訊號模式）

（無）

### 第二線：TRAINED-FIT（A 不過，但 B/C 過 → 可用，縮小部位）

- 1560×trend_pullback  ← params 可能過擬合 2017-2023，縮小至半倉
- 1802×donchian_breakout  ← params 可能過擬合 2017-2023，縮小至半倉
- 2360×chip_momentum  ← params 可能過擬合 2017-2023，縮小至半倉
- 2383×chip_momentum  ← params 可能過擬合 2017-2023，縮小至半倉
- 3017×chip_momentum  ← params 可能過擬合 2017-2023，縮小至半倉
- 3711×chip_momentum  ← params 可能過擬合 2017-2023，縮小至半倉
- 6515×trend_pullback  ← params 可能過擬合 2017-2023，縮小至半倉
- 6770×chip_momentum  ← params 可能過擬合 2017-2023，縮小至半倉

### 第三線：BEAR-FRAGILE（B 或 C 熊市失效 → 牛市可用，需手動退場機制）

（無）

### 其他：SURVIVES-BEAR-ONLY（A 不過，B/C 過）

- 2308×donchian_breakout
- 2330×donchian_breakout

---

*驗證耗時：0.5 分鐘，共 30 個 backtest*