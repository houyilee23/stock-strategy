# Handoff: Opus → Sonnet (Round 4 - 換用還原股價)

> 開新 Sonnet session 時，把這段話貼進去當第一個 prompt。

---

## 給 Sonnet 的開場白

Round 3 你修得很好（P0-6/7/8 + 自己抓到 P0-9 engine bug）。Katie MaxDD 從 -63% 降到 -31%。
但 Opus 隨後做更深層分析發現 **measurement instrument 本身壞了** ——
我們所有回測都用 raw close（TWSE 不還原），完全沒處理除權息、拆分、減資。

**最致命發現**：0050 在 2025/06/18 做了 4:1 拆分，回測看到的是「一日跌 -74.8%」，
從那天起 baseline CAGR、regime 偵測、所有 portfolio 指標全部失效。

**本輪任務：用 FinMind 取得還原股價，改用 adj_close 重跑所有回測。**

**請依序讀：**
1. `docs/SONNET_FIX_ROUND4.md` — 本輪 single source of truth（含 P0-10~14 修法）
2. `docs/ROUND3_REPORT_TO_OPUS.md` — 上輪結果做對照基準
3. `config/watchlists.yaml` — Opus 已擴充到 80 檔（多了金融、傳產、ETF 等權值股做樣本）
4. `CLAUDE.md` — 用 Bash 工具不要用 PowerShell

**核心執行原則：**
- 全自動推進，依 ROUND4「執行順序」做
- **P0-14 verify_adjustment 跑完後先停下回報 Opus**，確認剩餘無法解釋的事件怎麼處理
- 修完依「回報格式」整理
- 卡住寫 `docs/BLOCKED_round4.md`

**重要約束**：
- ❌ 不要刪 `data/raw/`（手動下單參考 + 對照驗證需要）
- ❌ 不要動 Style 1 訊號參數（這輪只換資料來源）
- ❌ 不要動 `config/watchlists.yaml`（Opus 已更新）
- ❌ 不要把 FinMind token 寫進 git 控檔（這輪不需 token，未來若需，存 `config/secrets.yaml` 並 `.gitignore`）

**FinMind API**：
- URL: `https://api.finmindtrade.com/api/v4/data`
- 不需註冊（300 req/hr 上限），我們只要 ~80 calls，OK
- Datasets: `TaiwanStockPriceAdj`（還原股價）、`TaiwanStockDividend`（除權息事件）
- 文件：https://finmind.github.io/tutor/TaiwanMarket/Technical/

**Python 路徑（強制）**：`C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe`
**執行用 Bash 工具**（不要 PowerShell）

開始吧。
