# ChatGPT 快速上手指南

本文檔為 ChatGPT 用戶設計。如果你用 Claude，請改讀 `CLAUDE.md`。

---

## 30 秒快速認識

這是一個**台股個股選股策略系統**，核心功能：
- **訊號模式**（Takeshi）：每天對股票清單產生進出建議
- **組合模式**（Katie）：選出 top-N 檔進行配置回測
- **自動優化**（auto_iterate）：每周自動測試 65 個策略模板，找最佳參數

每日流程：抓今天股價 → 執行策略 → 產訊號 + 報告 → 上傳 GitHub

---

## 環境設定

### Python 版本
```
Python 3.13（Microsoft Store 版本推薦）
Windows 11 環境，路徑：D:\stock
```

### 檢查環境
打開 Windows PowerShell，切到 `D:\stock`：
```powershell
cd D:\stock
python --version
pip list | findstr pandas  # 檢查 pandas 版本
```

若 Python 不在 PATH，下載 [Microsoft Store 版本](https://www.microsoft.com/en-us/p/python/9nblggh4nns1)。

### 安裝依賴
```bash
pip install -r requirements.txt
```

---

## 第一次執行

### 1. 抓股價資料
```bash
python main.py fetch
```
第一次執行會抓 2010-2026 年全歷史資料（耗時 5-10 分鐘）。

### 2. 產生今日訊號
```bash
python main.py signals --list Takeshi
```
輸出位置：`output/reports/latest/signals_Takeshi.md`

### 3. 查看結果
用文本編輯器打開報告，或用 GitHub App 查看 HTML：
- 網址：`docs/index.html`（本地瀏覽器）
- GitHub Pages：`https://houyilee23.github.io/stock-strategy`（需啟用，見 Phase B）

---

## 常見工作流

### 工作流 1：每日更新（每天 18:00 自動跑）

**Windows 排程器設定**（見 `docs/MIGRATION_GUIDE.md`）

手動執行：
```bash
# [1] 抓今天股價 + 整週調整因子
python main.py update --all

# [2] 驗證昨日掛單是否成交
python main.py journal validate

# [3] 產訊號 + 自動記到日誌
python main.py signals --list Takeshi
python main.py signals --list Katie
python main.py signals --list universe

# [4] 產報告
python scripts/build_per_stock_reports.py
python scripts/build_html.py

# [5] 從 Excel 同步個人持倉（可選）
python scripts/sync_positions_from_excel.py
```

### 工作流 2：修改策略參數

所有參數在 `config/strategy.yaml`，不要 hardcode。

例如修改 Takeshi 的風險限制：
```yaml
# config/strategy.yaml
Takeshi:
  max_drawdown: 30       # ← 改這裡
  min_win_rate: 50
  holding_days: 5
```

改完後，重新產訊號：
```bash
python main.py signals --list Takeshi
```

### 工作流 3：新增股票到觀察清單

```yaml
# config/watchlists.yaml
Takeshi:
  - "2330"  # 台積電
  - "3661"  # 志超
  - "3034"  # 聯發科
```

重新產訊號即可。

### 工作流 4：測試新策略模板

見 `docs/ARCHITECTURE.md` 的「策略模板新增流程」。
快速版本：
1. 在 `src/strategy/auto_iterate/templates/` 新增函數
2. 更新 `TEMPLATE_GENERATORS` registry
3. 執行：`python main.py auto_iterate --template <name> --stocks 2330 2412`

### 工作流 5：大規模重新訓練（auto_iterate）

用 Optuna 自動搜尋所有模板的最佳參數：
```bash
python main.py auto_iterate \
  --stocks 2330 2412 3661 \
  --n-trials 100 \
  --n-processes 4
```

輸出：`output/auto_iterate/<run_id>/`

---

## 檔案速查表

| 想做的事 | 編輯哪些檔案 | 更多資訊 |
|---|---|---|
| 改參數 | `config/strategy.yaml` | 詳見檔案註解 |
| 新增股票 | `config/watchlists.yaml` | 只改這一個 |
| 新增策略 | `src/strategy/auto_iterate/templates/` | 見 ARCHITECTURE.md |
| 改 Tier 規則 | `src/strategy/auto_iterate/tiering.py` | 429 行，單檔 |
| 改報告格式 | `scripts/build_html.py` | 產 HTML 入口 |
| 改訊號驗證 | `src/journal/validator.py` | 日誌欄位在 `src/journal/schema.py` |

---

## 常見問題

### Q：為什麼 fetch 這麼慢？
A：第一次要抓 16 年歷史，之後每天只抓新增資料（1 分鐘內）。

### Q：訊號為什麼沒出現？
A：
1. 檢查 `config/watchlists.yaml` 有沒有加股票
2. 檢查 `output/errors/` 有沒有錯誤紀錄
3. 股票 IPO 日期前無訊號（見 `src/fetchers/metadata.py`）

### Q：能不能手動改某檔股票的建議 Tier？
A：
```bash
python scripts/retier_run_dir.py <run_id>  # 對舊 run 重新評級
python scripts/retier_recommendations.py   # 對現有 recommendations.yaml 改級
```
詳見 `docs/ARCHITECTURE.md`。

### Q：怎麼知道訊號對不對？
A：
```bash
# 看個股 backtest 細節
python -m src.strategy.auto_iterate.view_backtest 2330 Takeshi
```
或打開 `output/reports/per_stock/2330.md`。

### Q：能不能改變 Phase A→B？
A：Phase A = 本地跑，Phase B = 上傳 GitHub Pages。
- 改 `scripts/daily_update.bat`：取消註解 `[1]` 與 `[7]` 行
- 在 GitHub repo 設定啟用 GitHub Pages
- 詳見 `docs/MIGRATION_GUIDE.md`

---

## 關鍵檔案地圖

```
D:\stock/
├── main.py                                # ← 入口（python main.py --help）
├── config/
│   ├── strategy.yaml                      # ← 改參數
│   └── watchlists.yaml                    # ← 改股票清單
├── docs/
│   ├── ARCHITECTURE.md                    # ← 架構細節（改程式前必讀）
│   ├── SPEC_strategy_system.md            # ← 設計規格
│   └── MIGRATION_GUIDE.md                 # ← Windows 排程器設定
├── src/
│   ├── strategy/
│   │   └── auto_iterate/                  # ← 策略優化
│   │       ├── templates/                 # ← 65 個策略模板
│   │       └── runner.py
│   └── fetchers/                          # ← 股價抓取（TWSE/TPEX）
├── scripts/
│   ├── daily_update.bat                   # ← 每日排程入口
│   └── build_html.py                      # ← 產報告
└── output/
    └── reports/latest/                    # ← 今日訊號（看這裡）
```

---

## 快速驗證清單

跑完 `python main.py signals` 後，檢查：

- [ ] 有沒有新產生的 `output/reports/latest/signals_*.md`？
- [ ] 有沒有錯誤在 `output/errors/`？
- [ ] 報告裡的股票數量合理嗎？
- [ ] 推薦的進出價格在合理範圍嗎？

---

## 下一步

### 立即開始
1. `python main.py fetch`（第一次 5-10 分鐘）
2. `python main.py signals --list Takeshi`（1-2 分鐘）
3. 打開 `output/reports/latest/signals_Takeshi.md`

### 深入了解
- `docs/ARCHITECTURE.md` — 系統架構（改程式必讀）
- `docs/SPEC_strategy_system.md` — 完整設計規格
- `docs/SIGNAL_JOURNAL.md` — 訊號日誌 + 績效報表

### 進階操作
- `python main.py auto_iterate` — 自動優化（需 GPU 加速，或耐心等待）
- `python scripts/audit_templates.py` — 審計策略績效
- 見 `docs/MIGRATION_GUIDE.md` 啟用 GitHub Pages

---

**最後更新**：2026-07-18  
**建議**：遇到問題先查 `docs/ARCHITECTURE.md` → 再看 `docs/SPEC_strategy_system.md`
