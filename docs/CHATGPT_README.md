# ChatGPT 用戶文檔索引

👋 歡迎！本文檔引導你找到合適的文檔。

---

## 我該讀哪個？

### 🚀 30 分鐘快速開始
→ **[CHATGPT_QUICKSTART.md](CHATGPT_QUICKSTART.md)**
- 系統是什麼
- 環境檢查
- 第一次執行
- 常見工作流

### 📋 交接檢查清單
→ **[CHATGPT_HANDOFF_CHECKLIST.md](CHATGPT_HANDOFF_CHECKLIST.md)**
- 30 分鐘上手清單
- 日常操作速查
- 常見問題
- 應急聯絡

### 📚 完整工作流指南
→ **[CHATGPT_WORKFLOWS.md](CHATGPT_WORKFLOWS.md)**
- 工作流 A：每日訊號
- 工作流 B：改參數
- 工作流 C：新增股票
- 工作流 D：查回測
- ... 共 11 個工作流

### 🏗️ 系統架構（深度）
→ **[ARCHITECTURE.md](ARCHITECTURE.md)**
- 模組總覽
- 資料流圖
- 檔案速查表

### 📖 設計規格（參考）
→ **[SPEC_strategy_system.md](SPEC_strategy_system.md)**
- 完整設計規格
- Tier 規則細節
- 訊號時序

### 🔧 技術文檔（ChatGPT 版本）
→ **[CHATGPT_CLAUDE_MD.md](CHATGPT_CLAUDE_MD.md)**
- CLAUDE.md 移除 Claude 工具特異部分
- 環境設定
- 約束與設計原則

### 🚢 部署指南
→ **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**
- Windows 排程器設定
- GitHub Pages 啟用

### 📊 訊號日誌模組
→ **[SIGNAL_JOURNAL.md](SIGNAL_JOURNAL.md)**
- 交易日誌結構
- 驗證邏輯
- 績效報表

---

## 按進度選檔案

### 第 1 天（入門）
1. 📋 **CHATGPT_HANDOFF_CHECKLIST.md** — 讀「30 分鐘上手清單」部分
2. 🚀 **CHATGPT_QUICKSTART.md** — 完整讀一遍
3. 執行第一次 `python main.py fetch` + `signals`

### 第 2 天（練習）
1. 📚 **CHATGPT_WORKFLOWS.md** — 工作流 A-D（日常操作）
2. 嘗試修改參數、新增股票
3. 查詢個股回測

### 第 3 天（深度）
1. 🏗️ **ARCHITECTURE.md** — 前半段（模組總覽 + 資料流）
2. 📚 **CHATGPT_WORKFLOWS.md** — 工作流 E-K（進階 + troubleshooting）

### 第 4 天（運維）
1. 🚢 **MIGRATION_GUIDE.md** — Windows 排程器設定
2. 設定每日自動更新
3. 啟用 GitHub Pages

### 第 5+ 天（自主）
1. 📚 **CHATGPT_WORKFLOWS.md** — 工作流 F（auto_iterate）
2. 🏗️ **ARCHITECTURE.md** — 全部讀完
3. 📖 **SPEC_strategy_system.md** — 按需查詢

---

## 我要... 怎麼辦？

| 我要... | 讀這個 |
|---|---|
| 快速上手 | CHATGPT_QUICKSTART.md |
| 每天產訊號 | CHATGPT_WORKFLOWS.md → 工作流 A |
| 改策略參數 | CHATGPT_WORKFLOWS.md → 工作流 B |
| 新增股票 | CHATGPT_WORKFLOWS.md → 工作流 C |
| 查個股回測 | CHATGPT_WORKFLOWS.md → 工作流 D |
| 驗證交易成交 | CHATGPT_WORKFLOWS.md → 工作流 E |
| 自動優化參數 | CHATGPT_WORKFLOWS.md → 工作流 F |
| 設定自動更新 | CHATGPT_WORKFLOWS.md → 工作流 H |
| 啟用 GitHub Pages | CHATGPT_WORKFLOWS.md → 工作流 I |
| 新增策略 | CHATGPT_WORKFLOWS.md → 工作流 J |
| 除錯問題 | CHATGPT_WORKFLOWS.md → 工作流 K |
| 理解系統架構 | ARCHITECTURE.md |
| 理解 Tier 規則 | SPEC_strategy_system.md |
| 排程器設定 | MIGRATION_GUIDE.md |
| 交易日誌 | SIGNAL_JOURNAL.md |

---

## 與 ChatGPT 互動的最佳方式

### ✅ 最有效的提問方式

```
我想 [具體目標]

現在的狀況：
- 我已經 [做了什麼]
- 結果是 [什麼狀況]
- 錯誤訊息是 [if any]

我希望 [預期結果]

可以 [具體幫忙方向嗎？]
```

### 📎 給 ChatGPT 提供這些資訊會更有幫助

- **相關的文件路徑**（例：`config/strategy.yaml` 的某段）
- **錯誤訊息**（整個 error log）
- **已試過什麼**（避免重複建議）
- **系統信息**（Python 版本、OS 等）

### 📝 例子

❌ **不好的提問**
```
訊號為什麼沒出現？
```

✅ **好的提問**
```
我新增了股票 3034 到 config/watchlists.yaml 的 Takeshi 帳戶。
跑了 `python main.py signals --list Takeshi`，
但報告裡找不到 3034。

output/errors/2026-07-18.csv 裡有：
stock_id,date,operation,error_message
3034,2026-07-18,backtest,"IPO 日期不在範圍內"

是因為這支股票太新嗎？該怎麼解決？
```

---

## 常見快捷方式

### 環境檢查
```bash
# 確認 Python
python --version

# 確認依賴
pip list | findstr pandas

# 檢查主要檔案
dir data/raw/
dir output/reports/latest/
```

### 日常命令
```bash
# 抓股價 + 產訊號（最常用）
python main.py update --all && python main.py signals --list Takeshi

# 驗證交易
python main.py journal validate && python main.py journal report --period month

# 查某檔股票的回測
python -m src.strategy.auto_iterate.view_backtest 2330 Takeshi
```

### 查錯誤
```bash
# 最新錯誤
type output/errors/2026-07-18.csv

# 按日期查
dir output/errors/
```

---

## 文檔間關係圖

```
你在這裡（README）
    │
    ├─→ 🚀 CHATGPT_QUICKSTART.md（30 分鐘入門）
    │       │
    │       └─→ 執行命令、看報告
    │
    ├─→ 📋 CHATGPT_HANDOFF_CHECKLIST.md
    │       │
    │       ├─→ 交接清單
    │       └─→ 常見問題速查
    │
    ├─→ 📚 CHATGPT_WORKFLOWS.md（日常工作）
    │       │
    │       ├─→ 工作流 A-E 每天用
    │       ├─→ 工作流 F-I 每周/月 用
    │       └─→ 工作流 J-K 進階 + debug
    │
    ├─→ 🏗️ ARCHITECTURE.md（系統深度理解）
    │       │
    │       ├─→ 模組總覽
    │       ├─→ 資料流
    │       └─→ 檔案速查表
    │
    ├─→ 📖 SPEC_strategy_system.md（設計規格）
    │       │
    │       └─→ Tier 規則、訊號時序等深度細節
    │
    ├─→ 🔧 CHATGPT_CLAUDE_MD.md（技術概述）
    │       └─→ 約束、設計原則、重要檔案
    │
    ├─→ 🚢 MIGRATION_GUIDE.md（運維）
    │       └─→ 排程器、GitHub Pages
    │
    └─→ 📊 SIGNAL_JOURNAL.md（交易日誌）
            └─→ 驗證邏輯、績效報表
```

---

## 我卡住了怎麼辦？

### 第一步：自助查詢
1. 查 **CHATGPT_WORKFLOWS.md → 工作流 K（處理錯誤）**
2. 查 **CHATGPT_HANDOFF_CHECKLIST.md → 常見問題**
3. 檢查 `output/errors/{date}.csv`

### 第二步：給 ChatGPT 提問
準備以下資訊：
- 我在做什麼（工作流或命令）
- 實際結果（完整 error log）
- 預期結果
- 已試過什麼

### 第三步：查詢原使用者
如果以上都解決不了，聯繫原使用者。

---

## 文檔維護說明

本文檔組於 **2026-07-18** 建立，包含：

- ✅ CHATGPT_QUICKSTART.md — 30 秒 + 常見工作流
- ✅ CHATGPT_WORKFLOWS.md — 11 個完整工作流 + troubleshooting
- ✅ CHATGPT_HANDOFF_CHECKLIST.md — 交接清單 + 快速參考
- ✅ CHATGPT_CLAUDE_MD.md — CLAUDE.md 簡化版
- ✅ CHATGPT_README.md — 本檔（導引索引）

**更新間隔**：按需（功能改變時更新）

---

**開始吧！** 👉 建議先讀 [CHATGPT_QUICKSTART.md](CHATGPT_QUICKSTART.md)
