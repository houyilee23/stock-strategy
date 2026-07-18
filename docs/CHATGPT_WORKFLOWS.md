# ChatGPT 用戶完整工作流指南

本文檔包含所有常見工作流的完整步驟和 troubleshooting。

---

## 工作流 A：每日訊號產生（日常工作）

### 時間成本
- 第一次：15-20 分鐘（包括 fetch 全歷史）
- 之後每天：3-5 分鐘

### 步驟

#### Step 1：抓股價數據（第一次或一周一次）
```bash
python main.py fetch
```
**輸出**：`data/raw/`（TWSE/TPEX）
**等待時間**：
- 第一次：5-10 分鐘（2010-2026 全歷史）
- 之後：1-2 分鐘（新增資料）

#### Step 2：抓調整因子（可選，月初跑一次）
```bash
python main.py fetch-adjusted
```
**輸出**：`data/adjusted/`
**包含**：除權息、拆分、減資等事件

#### Step 3：抓月營收（可選，月初跑）
```bash
python main.py fetch-revenue
```
**輸出**：`data/revenue/`
**來源**：FinMind API

#### Step 4：一鍵更新（推薦：用這個）
```bash
python main.py update --all
```
相當於執行 Step 1-3，可一次完成。

#### Step 5：產訊號
```bash
# 產 Takeshi 帳戶訊號
python main.py signals --list Takeshi

# 或產 Katie 帳戶
python main.py signals --list Katie

# 或掃整個 watchlist
python main.py signals --list universe
```

**輸出**：`output/reports/latest/signals_Takeshi.md` 等

#### Step 6：驗證結果
打開報告檔，檢查：
- [ ] 有買進建議嗎？
- [ ] 有賣出建議嗎？
- [ ] 推薦的進出價格合理嗎？

---

## 工作流 B：修改策略參數

**場景**：想改某個帳戶的風險限制、時間參數等

### Step 1：打開 `config/strategy.yaml`

### Step 2：找到對應帳戶段（例 Takeshi）
```yaml
Takeshi:
  max_drawdown: 30          # ← 改這些參數
  min_win_rate: 50
  holding_days: 5
  max_position_size: 100000
```

### Step 3：修改參數
例如，改最大回撤容忍度從 30% 改到 40%：
```yaml
Takeshi:
  max_drawdown: 40          # ← 改成 40
```

### Step 4：保存，重新產訊號
```bash
python main.py signals --list Takeshi
```

### Step 5：檢查變化
```bash
# 比較新舊報告
# output/reports/latest/signals_Takeshi.md (新)
# output/reports/2026/07/17_signals_Takeshi.md (舊，如果有)
```

**Troubleshooting**：
- Q：改了參數但訊號沒變？
  - A：刪除 `output/reports/latest/signals_Takeshi.md`，重新跑
  - A：檢查 YAML 縮排（Python 對縮排敏感）

---

## 工作流 C：新增股票到觀察清單

**場景**：想開始追蹤某支股票

### Step 1：打開 `config/watchlists.yaml`

### Step 2：找到對應帳戶
```yaml
Takeshi:
  - "2330"  # 台積電
  - "3661"  # 志超
  # ← 在這裡加新的
```

### Step 3：加入新股票（記得加引號）
```yaml
Takeshi:
  - "2330"
  - "3661"
  - "3034"  # ← 新增聯發科
```

### Step 4：保存，重新產訊號
```bash
python main.py signals --list Takeshi
```

### Step 5：檢查新股票有沒有出現在報告裡
打開 `output/reports/latest/signals_Takeshi.md`，搜尋 "3034"。

**Troubleshooting**：
- Q：新股票出現在報告但沒有訊號？
  - A：可能是 IPO 日期太近（少於 1 年資料）
  - A：檢查 `output/errors/{today}.csv` 有沒有錯誤

---

## 工作流 D：查詢個股詳細回測

**場景**：想看某支股票在某個策略下的完整回測

### Step 1：查詢個股回測 markdown
```bash
# 方法 1：直接打開
# output/reports/per_stock/2330.md
```

### 方法 2：用 CLI 工具查詢
```bash
python -m src.strategy.auto_iterate.view_backtest 2330 Takeshi
```

輸出包括：
- 進出訊號點位
- 逐筆交易記錄
- 勝率、平均獲利、最大回撤
- 年度績效表

### Step 2：驗證訊號
- [ ] 進場時機是否合理？
- [ ] 持有天數是否符合預期？
- [ ] 風險收益比是否可接受？

**Troubleshooting**：
- Q：會不會看到 2025 年的交易但今天是 2026 年？
  - A：不會。訊號系統有時間防穿越機制，確保只用過去資料

---

## 工作流 E：驗證日誌交易成交（每日 18:00 跑）

**場景**：昨天掛進出單，今天確認是否成交

### Step 1：驗證
```bash
python main.py journal validate
```

**原理**：
- 讀 `output/journal/trades_*.csv`（昨日掛單）
- 用今日 OHLC 核對是否成交
- 更新 status（pending → filled 或 cancelled）

### Step 2：查詢
```bash
python main.py journal view --date 2026-07-18
```

輸出：
```
Date       Stock  Status  Entry    Exit     P&L
2026-07-18 2330   filled  123.45   125.50   +170
2026-07-18 3661   pending -        -        -
```

### Step 3：產績效報表
```bash
python main.py journal report --period month
```

輸出：
- 本月勝率
- 平均獲利
- 累計 P&L
- Sharpe ratio

---

## 工作流 F：自動優化策略參數（auto_iterate）

**場景**：想測試所有 65 個模板，找最佳參數

**時間成本**：
- 10 檔股票 × 100 trials：2-4 小時（有 GPU）
- 沒 GPU：4-8 小時

### Step 1：可選——自行挑選股票清單
```bash
# 預設用 config/watchlists.yaml，或自行指定
python main.py auto_iterate \
  --stocks 2330 2412 3661 1101 1216 \
  --n-trials 100 \
  --n-processes 4
```

### Step 2：監控進度
會產出 `output/auto_iterate/<run_id>/` 目錄，包含：
- `per_stock_best.yaml` — 每檔股票最佳模板
- `comparison.csv` — 全部 (股票, 模板) 的比較表
- `summary.md` — 摘要報告

### Step 3：套用結果（可選）
```bash
# 把新訓練結果升級為現有推薦
python scripts/apply_retrain_upgrades.py <run_id>
```

會更新：`config/per_stock_recommendations.yaml`

### Step 4：檢視結果
```bash
# 查看最佳 10 檔股票
head -10 output/auto_iterate/<run_id>/per_stock_best.yaml
```

**Troubleshooting**：
- Q：跑得太慢？
  - A：改 `--n-processes 2` (少用 CPU)
  - A：改 `--n-trials 50` (試驗次數少)
  - A：只測 5-10 檔股票

- Q：有 GPU（CUDA），能加速嗎？
  - A：見 `requirements.txt` 和 `src/strategy/auto_iterate/runner.py`

- Q：跑到一半停了？
  - A：Optuna 會自動 resume（見 `<run_id>/<template>.db`）
  - A：重新跑 `auto_iterate` 就繼續

---

## 工作流 G：調整 Tier 規則後重評

**場景**：改了 `tiering.py` 的 Tier 規則，想對舊結果重新評級

### 場景 1：重評某個舊 run
```bash
python scripts/retier_run_dir.py output/auto_iterate/run_20260515
```

會重新評級 `per_stock_best.yaml` 的每檔股票，輸出新檔案。

### 場景 2：重評現有推薦
```bash
python scripts/retier_recommendations.py
```

會重新評級 `config/per_stock_recommendations.yaml`。

**Troubleshooting**：
- Q：改了 Tier 規則，哪個命令最快生效？
  - A：改完 `tiering.py` → 跑 `retier_recommendations.py` → 重新產訊號

---

## 工作流 H：設定每日自動更新（Windows 排程器）

**場景**：想每天 18:00 自動跑 fetch + 產訊號 + push GitHub

### Step 1：設定排程

開啟 Windows 工作排程器：
```bash
# 按 Win 鍵，搜尋「工作排程器」
```

### Step 2：新增工作
- **名稱**：`TaiwanStockDaily`
- **觸發程序**：每天 18:00
- **操作**：執行 `scripts/daily_update.bat`

詳見 `docs/MIGRATION_GUIDE.md` 完整截圖。

### Step 3：檢查執行
工作排程器會在 18:00 跑 `daily_update.bat`，流程：
1. git pull（Phase B 才啟用）
2. fetch + adjust + revenue
3. signals
4. build reports
5. git push（Phase B 才啟用）

**Troubleshooting**：
- Q：排程沒跑？
  - A：檢查「工作排程器」→ 「工作排程程式庫」，找 `TaiwanStockDaily`
  - A：查看「上次執行時間」和「上次執行結果」

- Q：跑了但沒 push GitHub？
  - A：這是 Phase A 行為（預設）。啟用 Phase B 見下方

---

## 工作流 I：啟用 Phase B（GitHub Pages）

**場景**：想在手機上看訊號（需要 GitHub Pages）

### Step 1：準備 GitHub 帳戶
- Fork 或建立公開 repo `houyilee23/stock-strategy`
- 確認已連結 git（見 `docs/MIGRATION_GUIDE.md`）

### Step 2：啟用 GitHub Pages
GitHub 後台：
- Settings → Pages
- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

### Step 3：修改 `daily_update.bat`

找到這幾行：
```batch
REM git pull
REM python scripts/build_html.py
REM git add commit push
```

改成：
```batch
git pull
python scripts/build_html.py
git add commit push
```

### Step 4：測試
手動跑一次：
```bash
./scripts/daily_update.bat
```

檢查：
- [ ] GitHub 上有新 commit？
- [ ] GitHub Pages 網址有新內容？（通常等 1-2 分鐘）

**手機查看**：
```
https://houyilee23.github.io/stock-strategy
```

---

## 工作流 J：新增策略模板

**場景**：想設計全新的進場邏輯

### 複雜度：★★★（進階工作）

完整步驟見 `docs/ARCHITECTURE.md` 的「策略模板新增流程」。

快速版本：

#### Step 1：在 templates 目錄新增函數

`src/strategy/auto_iterate/templates/core_t1_t9.py` 或 `reversal_dips.py`：
```python
def my_new_strategy(stock, close, params, **kwargs):
    """
    Args:
        stock: Series, 股票代碼
        close: Series, 收盤價
        params: dict, 搜尋空間裡的參數
    Returns:
        entry_signals: DataFrame, 進場訊號 (1=買, 0=hold, -1=賣)
    """
    # 計算指標
    ma20 = close.rolling(20).mean()
    
    # 產訊號
    signals = pd.Series(0, index=close.index)
    signals[close > ma20] = 1
    signals[close < ma20] = -1
    
    return signals
```

#### Step 2：註冊到 `TEMPLATE_GENERATORS`

`templates/__init__.py`：
```python
TEMPLATE_GENERATORS = {
    'my_new_strategy': my_new_strategy,
    ...
}
```

#### Step 3：定義搜尋空間

`templates/search_spaces.py`：
```python
SEARCH_SPACES['my_new_strategy'] = {
    'ma_period': (10, 50),
    'threshold': (0.01, 0.05),
}
```

#### Step 4：測試
```bash
python main.py backtest 2330 my_new_strategy
```

#### Step 5：加入 auto_iterate
```bash
python main.py auto_iterate --template my_new_strategy --stocks 2330
```

---

## 工作流 K：處理錯誤

**場景**：某支股票無法抓取或訊號產不出來

### 步驟

#### Step 1：檢查錯誤日誌
```bash
# 今日錯誤
cat output/errors/2026-07-18.csv

# 可能看到
# stock_id,date,operation,error_message
# 2330,2026-07-18,fetch,"Connection timeout"
```

#### Step 2：根據錯誤排查

**A. Fetch 錯誤**
```bash
# 重新抓該股票
python main.py fetch --stock 2330

# 檢查是否存在
ls data/raw/2330.csv
```

**B. 訊號產生失敗**
```bash
# 檢查該股票的日期範圍
python -c "import pandas as pd; df = pd.read_csv('data/raw/2330.csv'); print(df[['date']].min(), df[['date']].max())"
```

**C. 策略模板錯誤**
```bash
# 單獨測試
python main.py backtest 2330 Takeshi --verbose
```

會輸出詳細 traceback。

#### Step 3：常見問題

| 錯誤 | 解決方案 |
|---|---|
| `IPO 日期不在範圍內` | 檢查 `src/fetchers/metadata.py`，該股票 IPO 月份是否正確 |
| `缺少調整因子` | 跑 `python main.py fetch-adjusted` |
| `缺少月營收` | 跑 `python main.py fetch-revenue` |
| `參數超出搜尋空間` | 檢查 `config/strategy.yaml` 的參數是否在 `templates/search_spaces.py` 定義的範圍內 |

---

## 快速參考表

| 我想... | 執行 |
|---|---|
| 每天產訊號 | `python main.py update --all && python main.py signals --list Takeshi` |
| 查一檔股票詳細回測 | `python -m src.strategy.auto_iterate.view_backtest 2330 Takeshi` |
| 驗證昨日成交 | `python main.py journal validate` |
| 看本月績效 | `python main.py journal report --period month` |
| 訓練全部模板 | `python main.py auto_iterate --n-trials 100` |
| 改進場規則 | 編輯 `src/strategy/auto_iterate/tiering.py` + `retier_recommendations.py` |
| 新增觀察股票 | 編輯 `config/watchlists.yaml` + 重新產訊號 |
| 新增策略 | `templates/` 新檔 + `__init__.py` 註冊 + `search_spaces.py` 加參數 |

---

**最後更新**：2026-07-18  
**反饋**：遇到問題，先查 `output/errors/` 和本檔的 Troubleshooting 段落
