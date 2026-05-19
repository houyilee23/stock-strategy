# Retrain 排程設定

本機已有的排程任務：

| 任務名 | 觸發 | 內容 |
|---|---|---|
| `TaiwanStockDaily` | 每天 18:00 | `scripts\daily_update.bat`（fetch + signals + push） |

## 擬議：擴大歷史區間 retrain（每週一次）

```cmd
schtasks /create ^
    /tn "stock_retrain_extended_weekly" ^
    /tr "D:\stock\scripts\retrain_extended_history.bat" ^
    /sc weekly /d SUN ^
    /st 02:00 ^
    /ru SYSTEM
```

**為什麼週日 02:00：**

- 距離週日台股無交易 → 不會跟 daily_update.bat 衝突
- 預估全 universe retrain ~8-24 hr → 不會延伸到週一 18:00 的 daily
- 凌晨 02:00 CPU 全閒

## 一次性執行（不排程）

```cmd
REM 在當前 shell 跑（可看即時 log）
D:\stock\scripts\retrain_extended_history.bat

REM 跑 pilot（先驗證流程 OK）
D:\stock\scripts\retrain_extended_history.bat --pilot

REM 背景跑（不擋 shell）
start /b D:\stock\scripts\retrain_extended_history.bat
```

## 查 / 刪排程

```cmd
schtasks /query /tn "stock_retrain_extended_weekly" /v
schtasks /delete /tn "stock_retrain_extended_weekly" /f
```

## 觸發後檢查

```bash
# 該 retrain run dir
ls output/auto_iterate/ | tail -1

# 結構化索引（會自動更新）
cat output/auto_iterate/INDEX.csv | tail -3

# 當日 log
ls logs/retrain_*.log | tail -1
```
