# 項目交接清單（給 ChatGPT 用戶）

交接日期：2026-07-18  
交接對象：同事（ChatGPT 用戶）

---

## 快速 30 分鐘上手清單

使用 ChatGPT 作為開發助手時，依序完成：

### 第 1 天：環境 + 基本流程（30 分鐘）

- [ ] 確認 Python 3.13 已安裝
  ```bash
  python --version  # 應該看到 3.13.x
  ```

- [ ] 安裝依賴
  ```bash
  cd D:\stock
  pip install -r requirements.txt
  ```

- [ ] 跑第一次 fetch（可能需要 5-10 分鐘）
  ```bash
  python main.py fetch
  ```

- [ ] 產第一份訊號
  ```bash
  python main.py signals --list Takeshi
  ```

- [ ] 打開報告檢查
  ```
  output/reports/latest/signals_Takeshi.md
  ```

### 第 2 天：常見工作流（1 小時）

- [ ] 讀懂 `docs/CHATGPT_QUICKSTART.md`（15 分鐘）
- [ ] 讀懂檔案速查表（10 分鐘）
- [ ] 嘗試修改 `config/strategy.yaml` 的一個參數（10 分鐘）
- [ ] 嘗試新增一支股票到 `config/watchlists.yaml`（10 分鐘）
- [ ] 觀察訊號變化（15 分鐘）

### 第 3 天：深入了解（2-3 小時）

- [ ] 讀 `docs/ARCHITECTURE.md` 前半段（30 分鐘）
- [ ] 讀 `docs/CHATGPT_WORKFLOWS.md` 工作流 A-D（45 分鐘）
- [ ] 用 `python main.py journal validate` 驗證交易（15 分鐘）
- [ ] 試試 auto_iterate 在 5 檔股票上跑（1-2 小時）

### 第 4 天：運維（可選）

- [ ] 設定 Windows 排程器（工作流 H）
- [ ] 啟用 GitHub Pages（工作流 I）
- [ ] 驗證每日自動更新能否跑

---

## 項目核心信息

### 是什麼？
台股個股選股策略系統，包含：
- **訊號模式**：每天對股票清單產生進出建議
- **組合模式**：組合配置回測
- **自動優化**：Optuna 搜尋最佳模板參數

### 用來幹什麼？
- 選股：用 Takeshi/Katie 帳戶的訊號篩選候選股
- 驗證：用 journal 模組追蹤實際交易成交情況
- 改進：用 auto_iterate 定期重訓練，提升策略績效

### 目標
7~10 年年化打贏 0050，MaxDD ≤ 30%

### 雙帳戶系統

| 帳戶 | 風格 | 用途 | 特徵 |
|---|---|---|---|
| Takeshi | 積極 | 個股進出建議 | 高勝率，短持期 |
| Katie | 保守 | 組合配置 | 分散風險，定期調整 |
| universe | 掃描 | 全 watchlist 掃一遍 | 發現新機會 |

---

## 文件導讀

### 必讀（第一周）

1. **`docs/CHATGPT_QUICKSTART.md`**（15 分鐘）
   - 30 秒認識系統
   - 常見工作流（複製貼上即可用）
   - 常見問題

2. **`docs/ARCHITECTURE.md`** 前半段（30 分鐘）
   - 模組總覽
   - 主要資料流
   - 檔案速查表

### 重點（第二周）

3. **`docs/CHATGPT_WORKFLOWS.md`**（按需讀）
   - 工作流 A-E：日常操作
   - 工作流 F-H：進階操作
   - 工作流 J-K：故障排查

4. **`docs/SPEC_strategy_system.md`**（參考）
   - 完整設計規格
   - Tier 規則細節
   - 訊號時序

### 維運（可選）

5. **`docs/MIGRATION_GUIDE.md`**
   - Windows 排程器設定
   - GitHub Pages 啟用

6. **`docs/SIGNAL_JOURNAL.md`**
   - 訊號日誌結構
   - 交易驗證邏輯

---

## 關鍵配置檔案

### 修改頻率排序

| 檔案 | 修改頻率 | 影響範圍 | 例子 |
|---|---|---|---|
| `config/watchlists.yaml` | 高（每周） | 訊號範圍 | 新增股票 |
| `config/strategy.yaml` | 中（月 1-2 次） | 策略參數 | 改 max_drawdown |
| `src/strategy/auto_iterate/tiering.py` | 低（季 1-2 次） | Tier 規則 | 改 S-tier 門檻 |
| `templates/` | 低（年 1-2 次） | 策略集合 | 新增模板 |

### 絕對不要改

❌ `src/strategy/auto_iterate/backtest_one.py`  
❌ `src/fetchers/` (除非加新市場)  
❌ `config/per_stock_recommendations.yaml` (由 auto_iterate 產出)

---

## 日常操作速查

### 每天 18:00 要跑的
```bash
python main.py update --all
python main.py signals --list Takeshi
# 手動檢查 output/reports/latest/signals_Takeshi.md
```

### 每周一次
```bash
python main.py signals --list Katie
python main.py signals --list universe
```

### 每月一次（可選）
```bash
python main.py auto_iterate --n-trials 100 --n-processes 4
# 找最佳模板參數，需要 2-4 小時
```

### 有問題時
```bash
# 檢查錯誤
cat output/errors/2026-07-18.csv

# 單檔驗證
python -m src.strategy.auto_iterate.view_backtest 2330 Takeshi

# 查日誌
python main.py journal validate
python main.py journal report --period month
```

---

## 常見問題（先讀這個）

### Q：ChatGPT 能幫忙什麼？
**A**：
- ✅ 解釋程式邏輯（讀 ARCHITECTURE.md 給 ChatGPT）
- ✅ 改參數（告訴 ChatGPT 想要什麼，它改 config 檔）
- ✅ 修 bug（提供 error log，它除錯）
- ✅ 新增功能（寫新策略、新報告等）
- ❌ 不能直接執行命令（你要複製貼上到 terminal）

### Q：訊號為什麼沒出現？
**A**：
1. 檢查 `config/watchlists.yaml` 有沒有加股票
2. 檢查 `output/errors/` 有沒有錯誤紀錄
3. 股票 IPO 日期太近（少於 1 年資料）

### Q：參數改了但訊號沒變？
**A**：
1. 確認 YAML 語法正確（縮排很重要）
2. 刪除舊報告：`rm output/reports/latest/signals_Takeshi.md`
3. 重新跑：`python main.py signals --list Takeshi`

### Q：怎麼知道策略對不對？
**A**：
```bash
python -m src.strategy.auto_iterate.view_backtest 2330 Takeshi
# 看逐筆交易、勝率、最大回撤
```

### Q：能不能自動下單？
**A**：不能。系統只產訊號，你要手動執行。這是刻意設計，避免自動錯誤。

### Q：GitHub Pages 如何啟用？
**A**：
1. Fork 或建立公開 repo
2. 在 GitHub 後台開啟 Pages（source = `/docs`）
3. 改 `scripts/daily_update.bat` 取消註解 git push 段
4. 手機看 `https://houyilee23.github.io/stock-strategy`

---

## 與 Claude Code 的區別

如果之前用過 Claude Code（本機助手），ChatGPT 有以下不同：

| 功能 | Claude Code | ChatGPT |
|---|---|---|
| 直接執行命令 | ✅ 可以 | ❌ 你要複製貼上 |
| 讀檔案 | ✅ 可以 | ✅ 可以（你上傳或給路徑） |
| 改檔案 | ✅ 可以直接改 | ⚠️ 你複製改好的內容，貼回去 |
| 看即時 terminal 輸出 | ✅ 可以 | ❌ 你告訴它結果 |
| 自動迴圈優化 | ✅ 可以 | ⚠️ 你描述問題，它給方案 |

**建議**：
- 簡單的查詢和理解 → ChatGPT 很好
- 複雜的 debug 迴圈（試 10 次才對）→ Claude Code 比較快
- 長期合作 → 混用：ChatGPT 寫方案，Claude Code 執行

---

## 應急聯絡

遇到卡不動的問題？

1. **檢查 `output/errors/`** — 系統自動記錄錯誤
2. **讀 `docs/CHATGPT_WORKFLOWS.md` 的 Troubleshooting** — 常見問題都有解
3. **給 ChatGPT 這些資訊**：
   ```
   問題：[你的問題]
   錯誤訊息：[output/errors/ 裡的內容]
   你試過：[你做過哪些步驟]
   預期結果：[希望看到什麼]
   ```

---

## 交接日期檢查清單

交接人（原使用者）：  
- [ ] 確認已跑完最後一次 auto_iterate
- [ ] 確認 GitHub repo 是最新
- [ ] 確認排程器設定無誤
- [ ] 複製此清單給同事

接手人（新使用者）：  
- [ ] 已讀 CHATGPT_QUICKSTART.md
- [ ] 已跑過一次 `fetch` + `signals`
- [ ] 已查看報告
- [ ] 已建立 ChatGPT 對話記錄用來追蹤問題
- [ ] 已設定本地開發環境

---

## 本月里程碑

**2026-07-18**：項目交接
- ✅ 整理 ChatGPT 文件
- ✅ 建立快速上手指南
- 待：同事接手驗證

**2026-08-18**：首月檢查（可選）
- 系統運作穩定度
- 訊號品質反饋
- 是否需要調整參數

---

**最後更新**：2026-07-18

如有問題，請回傳給原使用者或查詢 `docs/` 中的各檔案。
