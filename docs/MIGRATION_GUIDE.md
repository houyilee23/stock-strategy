# 遷移到 GitHub + 家裡電腦自動更新 完整步驟

最後更新：2026-05-04

## 兩個階段（Phase A / Phase B）

| 階段 | 描述 | 何時切換 |
|---|---|---|
| **Phase A** | 家裡 PC 每天 21:00 自動更新，**只在本地產報告**，不 push GitHub | 一開始就用這個 |
| **Phase B** | 同樣流程 + 跑完 push 到 GitHub Pages，手機可看 web UI | Phase A 跑順 1~2 週、確認穩定後切 |

`scripts/daily_update.bat` 預設是 Phase A（git pull / push 已用 REM 註解掉）。
切到 Phase B：取消註解兩段 + 一次性 push + 開 GitHub Pages。

整體流程：

```
[公司 PC] 手動搬到家裡 PC（USB / 雲端硬碟）
    ↓
[家裡 PC] 環境設定 + 排程
    ↓
[Phase A] 每天 21:00 本地自動更新（1~2 週驗證穩定）
    ↓ user 可以在家裡 PC 用瀏覽器看 docs/index.html
    ↓
[切換到 Phase B] 一次性 git push + 開 GitHub Pages
    ↓
[手機] 開 houyilee23.github.io/stock-strategy 看 web UI
```

---

## Phase 1：公司 PC → GitHub（一次性）

### 1-1. 在 GitHub 建立 repo
1. 登入 GitHub → 右上角 `+` → `New repository`
2. 名稱：`stock-strategy`（自取）
3. 描述：可空
4. **Public**（你的決定）
5. **不要勾** `Add a README file` / `Add .gitignore` / `Choose a license`
   （我們已經本地有了）
6. 按 `Create repository`

### 1-2. 公司 PC 上初始化 git 並 push

開 Git Bash，在 `C:\TronFuture\lee\stock` 底下：

```bash
git init
git add .
git status   # 確認沒有 watchlists.yaml / trades_Takeshi.csv 進來
git commit -m "initial migration: cleaned structure + daily update tooling"
git branch -M main
git remote add origin https://github.com/houyilee23/stock-strategy.git
git push -u origin main
```

⚠️ 推之前再次確認 .gitignore 有擋住敏感檔（我已經寫好了，但檢查一下心安）：
```bash
git ls-files | grep -E "watchlists|trades_|positions_snapshot"
```
這個指令應該沒輸出。**有輸出代表敏感檔被推上去了，立刻停止 git rm --cached 它再 commit**。

### 1-3. 確認 GitHub 上看得到
打開 `https://github.com/houyilee23/stock-strategy`：
- 應該看到 README.md 渲染出來，含「今日訊號」三個帳戶區塊
- 點任一檔代號（例如 2360）應該可開到 `output/reports/per_stock/2360.md`

---

## Phase 2：家裡 PC 環境設定（一次性）

### 2-1. 必裝軟體
- **Anaconda** 或 Miniconda（Python 3.11/3.12）
- **Git for Windows**（會附帶 Git Bash）

### 2-2. clone repo
開命令提示字元或 Git Bash：
```bash
cd C:\TronFuture\lee
git clone https://github.com/houyilee23/stock-strategy.git stock
cd stock
```

### 2-3. 安裝 Python 相依
```bash
pip install -r requirements.txt
```

### 2-4. 建立家裡端的個人 watchlists.yaml
公司 PC 上的 `config/watchlists.yaml` 是 gitignore 不會推上來。
家裡 PC 上要自己建立：
```bash
copy config\watchlists.example.yaml config\watchlists.yaml
notepad config\watchlists.yaml
```
編輯成你自己的清單（或直接從公司 PC 複製過去）。

### 2-5. 確認 Python 路徑
打開 `CLAUDE.md` 看 Python 路徑那一行：
```
C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe
```
家裡 PC 的 Anaconda 路徑可能不同，更新成實際路徑。

### 2-6. 修改 daily_update.bat 中的 PYTHON / REPO 變數
打開 `scripts/daily_update.bat`：
```batch
set PYTHON=C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe
set REPO=C:\TronFuture\lee\stock
```
改成家裡 PC 實際路徑。

### 2-7. 手動跑一次測試
```bash
scripts\daily_update.bat
```
跑完後檢查：
- `logs/daily_<日期>.log` 內容
- `git log -1` 看是否有新 commit
- GitHub 網頁刷新 → 看 README 是否有更新

---

## Phase 3：Windows 工作排程器設定

### 3-1. 開啟工作排程器
按 `Win + R` → 輸入 `taskschd.msc` → Enter

### 3-2. 建立工作（不是「基本工作」）
右側「建立工作...」（為了能設定喚醒等進階選項）

#### 一般 (General) 頁籤
- 名稱：`股票每日更新`
- 描述：每天 21:00 自動 update + push 到 GitHub
- 勾「**不論使用者是否登入均執行**」← 這樣鎖定畫面也會跑
- 勾「**以最高權限執行**」
- 設定：Windows 11

#### 觸發程序 (Triggers) 頁籤
- 新增 → 開始工作：「依排程」
- 每日，從今天 21:00 起
- 重複進行的工作：每 1 天

#### 動作 (Actions) 頁籤
- 新增 → 啟動程式
- 程式或指令碼：`C:\TronFuture\lee\stock\scripts\daily_update.bat`
- 開始位置（重要！）：`C:\TronFuture\lee\stock`

#### 條件 (Conditions) 頁籤
- 「**啟動工作以喚醒電腦**」← **務必勾**（讓睡眠中的筆電醒來跑）
- 「只有在電腦使用 AC 電源時才開始工作」← 選用，看你筆電在不在電源
- 「只有在下列網路連線中才開始」← 不勾，預設

#### 設定 (Settings) 頁籤
- 「允許隨選執行此工作」← 勾（你可以右鍵手動跑）
- 「如果工作執行時間超過下列時間，請停止工作」→ 改 1 小時
- 「如果失敗，每 30 分鐘重新啟動」→ 勾，最多 3 次

按 `確定` → 系統會問你密碼，輸入 Windows 登入密碼

### 3-3. 測試
1. 在工作排程器找到「股票每日更新」
2. 右鍵 → **執行**
3. 看 `logs/daily_<今日>.log` 是否有更新
4. GitHub 網頁是否有新 commit

### 3-4. 確認筆電會被喚醒
1. 把筆電關上（合蓋）→ 進入睡眠
2. 在工作排程器把觸發時間改成「現在 + 5 分鐘」
3. 等 5 分鐘
4. 打開蓋子 → 應該看到工作已執行（或正在執行）
5. 改回 21:00

⚠️ 如果筆電不喚醒：
- BIOS 中可能要開啟「Wake from Sleep」
- 控制台 → 電源選項 → 變更計畫設定 → 變更進階電源設定 → Sleep → 允許喚醒計時器 → 啟用

---

## Phase 4：手機設定

### 4-1. 安裝 GitHub Mobile App
- iOS：App Store 搜「GitHub」
- Android：Google Play 搜「GitHub」

### 4-2. 登入並書籤 repo
1. 登入 GitHub 帳號
2. 進入 `houyilee23/stock-strategy` repo
3. 點右上角的 ⭐ 加 star（也方便日後找）

### 4-3. 日常使用
- 每天打開 App → My work → Starred repositories → stock-strategy
- 直接看 README.md（自動渲染所有訊號表）
- 點任一檔代號 → 跳到該檔回測報告

---

## 持續維運注意事項

### 每天會自動發生的事
1. 21:00 排程觸發 → 筆電醒來
2. `daily_update.bat` 跑：
   - git pull（把 GitHub 上的更新拉下來，避免衝突）
   - 抓 raw + adjusted（約 5~10 分鐘）
   - 產 signals 報告（3 個帳戶）
   - 重產 per_stock 個股回測（80 多檔約 2~5 分鐘）
   - 重產 README.md
   - git commit + push
3. 跑完約 21:30 結束，筆電可繼續睡

### 排程沒跑成功怎麼辦？
1. 看 `logs/daily_<日期>.log` 找錯誤
2. 工作排程器中右鍵「執行」手動補跑
3. 如果是網路問題（FinMind / TWSE 不通），等隔天會自動重試

### 假日 / 颱風天 / 過年
**完全不用改設定**：
- TWSE 那天無資料 → fetcher 會 log warning + skip
- signals 也會跑，但表格內容跟前一天差不多（因為沒有新收盤資料）
- 不會壞、不會錯

### 何時該手動干預？
- 想加新股票到 watchlist → 編輯 `config/watchlists.yaml`（家裡 PC 上）
- 想重新跑優化 → 跑 `auto_iterate`（這個耗時很久，建議週末手動）
- 程式有 bug → 修 code 後 git push，下一次 daily_update 會 git pull 拿到

### 如何切到 Private repo（未來）
1. GitHub repo 頁 → Settings → Danger Zone → Change visibility → Private
2. 即時生效，公司 PC 從此就連不上（如你之前提過）
3. 家裡 PC 不影響（因為它有 git credential）
4. 手機 GitHub App 也不影響（自己帳號當然能看自己的 private repo）

---

## 檔案結構速覽

```
stock/
├── README.md              ← 手機入口（自動產生，每天 21:00 更新）
├── CLAUDE.md              ← 系統說明
├── main.py                ← CLI 入口
├── requirements.txt       ← Python 套件清單
├── .gitignore             ← 擋住 watchlists.yaml / trades_*.csv
│
├── config/
│   ├── strategy.yaml                ← 策略參數
│   ├── per_stock_recommendations.yaml ← 每檔最佳 template + tier
│   ├── stock_ipo.yaml               ← 各股 IPO 月份
│   ├── stock_market.yaml            ← TWSE / TPEX 分類
│   ├── watchlists.example.yaml      ← 範本（不含個人資料）
│   └── watchlists.yaml              ← [gitignore] 個人觀察清單
│
├── data/
│   ├── raw/                ← TWSE/TPEX 原始 OHLCV
│   ├── adjusted/           ← FinMind 還原股價
│   ├── dividends/、splits/  ← 除權息事件
│   ├── monthly_revenue/    ← 月營收
│   ├── chips/              ← 三大法人籌碼
│   └── trades_*.csv        ← [gitignore] 個人成交紀錄
│
├── src/
│   ├── fetcher.py          ← raw 抓取
│   ├── finmind_fetcher.py  ← 還原資料抓取
│   └── strategy/...        ← 訊號 / 回測 / 優化引擎
│
├── scripts/
│   ├── daily_update.bat              ← Windows 排程入口
│   ├── build_per_stock_reports.py    ← 產 per_stock/{sid}.md
│   └── update_readme.py              ← 產 README.md
│
├── output/
│   ├── reports/
│   │   ├── latest/                ← 永遠最新的訊號
│   │   ├── per_stock/             ← 每檔個股回測（手機點進來看）
│   │   └── 2026/04/、2026/05/...   ← 歷史歸檔（按月）
│   ├── auto_iterate/
│   │   └── merged_20260426_120034/ ← 唯一保留的 merged run
│   └── backtest/、optimize/       ← [gitignore] 暫存產物
│
├── archive/scripts/        ← 舊腳手架（保留追溯）
├── docs/                   ← 設計文件
└── tests/                  ← 單元測試
```
