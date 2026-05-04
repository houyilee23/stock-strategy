# Holdout Validation — Regime Filter 對比報告

**對象**: 2308×donchian_breakout, 2330×donchian_breakout  
**比較**: regime_filter=False（原）vs True（0050 close > MA200）  
**params**: 凍結，不重新 tune  

## Regime Filter 說明

entry 條件新增第 4 條：
```
0050.close > SMA(0050.close, 200)   # 大盤在 200MA 之上才允許進場
```
預期效果：2018/2022 熊市期間 0050 跌破 MA200，自動阻擋進場，
使 B/C 段 n_trades ≈ 0（INSUFFICIENT）而非虧損進場。

## A 段（2014-2016）對比

**標準**：expectancy >= 1% AND PF >= 1.0 AND n >= 3  
**期望**：regime_filter=True 的 A 段通過率不應下降（2014-2016 牛市為主）

| Stock | Filter | A_pass | n | exp | PF | DD |
|-------|--------|--------|---|-----|----|----|
| 2308 | False | ✓ | n=5 exp=4.1% PF=1.84 dd=-23.4% |
| 2308 | True | ✓ | n=5 exp=4.1% PF=1.87 dd=-23.2% |
| 2330 | False | ✓ | n=6 exp=4.4% PF=3.90 dd=-15.2% |
| 2330 | True | ✓ | n=6 exp=1.9% PF=1.37 dd=-27.7% |

## B 段（2018 熊市）對比

**標準**：PF >= 0.8 AND MaxDD <= 40%  
**期望**：regime_filter=True → n_trades 降低（被 MA200 過濾），PF 提升或 INSUFFICIENT

| Stock | Filter | B_pass | n | exp | PF | DD |
|-------|--------|--------|---|-----|----|----|
| 2308 | False | ✗ | n=2 exp=-3.5% PF=0.28 dd=-18.6% |
| 2308 | True | ✗ | n=2 exp=-3.5% PF=0.28 dd=-12.6% |
| 2330 | False | ✗ | n=2 exp=-1.9% PF=0.14 dd=-10.1% |
| 2330 | True | ✗ | n=2 exp=-1.9% PF=0.14 dd=-10.1% |

## C 段（2022 熊市）對比

**標準**：PF >= 0.8 AND MaxDD <= 40%  
**期望**：同 B 段

| Stock | Filter | C_pass | n | exp | PF | DD |
|-------|--------|--------|---|-----|----|----|
| 2308 | False | ✗ | n=1 exp=17.2% PF=? dd=-8.1% |
| 2308 | True | ✗ | n=0 exp=N/A PF=? dd=0.0% |
| 2330 | False | ✗ | n=0 exp=N/A PF=? dd=0.0% |
| 2330 | True | ✗ | n=0 exp=N/A PF=? dd=0.0% |

## 總評對比

| Stock | Template | Filter=False | Filter=True |
|-------|----------|-------------|------------|
| 2308 | donchian_breakout | **SURVIVES-BEAR-ONLY** | **SURVIVES-BEAR-ONLY** |
| 2330 | donchian_breakout | **SURVIVES-BEAR-ONLY** | **SURVIVES-BEAR-ONLY** |

## 結論

- **2308** 無改善（SURVIVES-BEAR-ONLY → SURVIVES-BEAR-ONLY）→ regime filter 對此股無效
- **2330** 無改善（SURVIVES-BEAR-ONLY → SURVIVES-BEAR-ONLY）→ regime filter 對此股無效