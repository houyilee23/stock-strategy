# 訊號日誌（Signal Journal）模組

## 為什麼存在

每天的 signals 輸出是「當下決策」，但：
- 限價單不一定成交（價格沒到掛單區）
- 沒辦法事後檢討「掛單策略是否合理」「哪些 template / tier 命中率高」

訊號日誌把每天的 BUY/SELL 訊號落帳成 CSV，事後用實際 OHLC 驗證「假設我真的掛了，會不會成交、成交後表現如何」。

寫入與驗證**完全分離** — signals 只負責記錄、validator 只負責看歷史價格，兩件事的時間錯開（落帳是 T 日傍晚，驗證是 T+1 之後資料抓回來才跑）。

## 三層模組

`src/journal/`（仿 `src/fetchers/` 模組化風格，每個檔案職責單一）：

| 檔案 | 職責 | 行數 |
|---|---|---|
| `schema.py`    | 欄位定義 + status 列舉 + journal_id / partition 規則 | ~70 |
| `storage.py`   | 月切 CSV 讀寫、upsert 去重、跨月合併 | ~85 |
| `writer.py`    | 從 `run_signals` 的 result_df 提取 BUY/SELL → 落帳 | ~115 |
| `validator.py` | 對 pending 訊號讀 OHLC 判定 filled / not_filled / expired | ~180 |
| `reporter.py`  | 讀多月份 CSV → 命中率、浮動報酬、依 account/template/tier 拆解 → Markdown | ~200 |
| `__init__.py`  | 公開 API：`log_signals` / `validate_all` / `write_report` | ~30 |

對外公開 API（從 `src.journal` import）：

```python
from src.journal import log_signals, validate_all, write_report
log_signals(result_df, account, stock_names)         # 落帳（已由 run_signals 自動呼叫）
validate_all(expiry_days=10)                          # 驗所有月份
write_report(start='2026-05', account='Takeshi')      # 產 Markdown 報表
```

## 資料夾與檔案

```
output/signal_journal/
├── 2026-05.csv             ← 月切 CSV，append-only，依 journal_id 去重
├── 2026-06.csv
└── reports/
    └── signal_perf_{account}_{range}_{ts}.md   ← 績效報表
```

## 欄位（共 29 欄）

| 階段 | 欄位 | 說明 |
|---|---|---|
| 落帳 | `journal_id` | `{signal_date}_{sid}_{account}_{action}` — 唯一鍵 |
| 落帳 | `signal_date` | T 日 = 該股 adjusted/raw 最後一筆日期（不是 wall-clock 日） |
| 落帳 | `logged_at` | 落帳的 ISO timestamp（debug 用） |
| 落帳 | `account`, `sid`, `name`, `template`, `tier`, `action` | 基本欄位 |
| 落帳 | `ref_close` | T 日收盤 |
| 落帳 | `limit_price` | BUY 掛單價（target_buy）|
| 落帳 | `stop_loss`, `take_profit` | SELL 出場條件 |
| 落帳 | `position_pct_max`, `market_regime` | 上下文 |
| 落帳 | `in_position`, `real_entry`, `real_shares` | T 日真實持倉狀態 |
| 落帳 | `reason` | generator 給的 reason 字串 |
| 驗證 | `status` | pending / filled / not_filled / expired / no_data |
| 驗證 | `validated_at`, `fill_date`, `fill_price`, `bars_to_fill` | 驗證結果 |
| 預留 | `exit_date`, `exit_price`, `exit_reason`, `realized_return`, `hold_days` | Phase 2 — 出場追蹤（先預留欄位） |

## 落帳邏輯（writer）

`run_signals` 跑完會自動呼叫 `log_signals(result_df, account)`：
- 只記 `action ∈ {BUY, SELL}` 的列（HOLD / N/A / ERROR 不進 journal）
- `signal_date = data/adjusted/{sid}.csv` 最後一筆日期 → 週末重跑同一份資料不會產生重複
- 依 `journal_id` upsert：已存在則 skip（不覆寫 validator 寫過的欄位）

## 驗證邏輯（validator）

對所有 `status=pending` 與 `status=not_filled` 的 row 重驗：

**BUY**：
- 有 `limit_price`：走訪 `signal_date` 之後的 bars，第一個 `low ≤ limit_price` 的 bar → filled
  - 若 `open ≤ limit_price`：fill_price = open（保守，常常開盤就跳低）
  - 否則 fill_price = limit_price
- 沒 `limit_price`（市價）：下一交易日 open 直接成交

**SELL**：
- 同時看 `take_profit` (high ≥ TP) 與 `stop_loss` (low ≤ SL)
- 同根都觸及 → 保守用 stop_loss（最壞情境）
- 兩者皆空（市價 SELL）→ 下一交易日 open 直接成交

**過期判定**：走完 `DEFAULT_EXPIRY_TRADING_DAYS = 10` 個交易日都沒觸發 → `expired`，
不到 10 但暫時不觸及 → `not_filled`（下次再驗有機會 fill）。

**「下一個交易日」就是 OHLC DataFrame 中 `index > signal_date` 的第一筆** —
週末 / 國定假日 / 颱風 / 停牌都自然被略過，不需要維護交易日曆。

## 績效報表（reporter）

```bash
python main.py journal report                              # 全部歷史，console + MD
python main.py journal report --account Takeshi            # 單一帳戶
python main.py journal report --start 2026-05 --end 2026-05  # 指定月份
```

報表內容：
- 整體摘要（總數 / 命中率 / 浮動報酬）
- 依 Account / Action / Tier / Template 拆解

**浮動 P&L 是代理值**（Phase 1）— 用「目前最新收盤 vs fill_price」近似已成交 BUY 的當下表現。
Phase 2 接上完整出場追蹤後改讀 `realized_return`。

## CLI

```bash
python main.py journal validate                # 驗所有月份的 pending / not_filled
python main.py journal report                  # 產整體績效 markdown
python main.py journal report --account Takeshi --start 2026-05
python main.py journal log                     # 提示（一般由 signals 自動呼叫）
```

## 與 daily_update.bat 的整合

```
[3/9] journal validate    ← 用今天抓回的 OHLC 驗證昨日掛單
[4/9] signals --list ...  ← 跑完自動 log_signals 落帳
```

順序很重要：validate 在 signals 之前，這樣昨日的 pending 會用今天剛抓回的最新 bar 驗。

## 限制與後續

- **浮動 P&L 是粗略代理**：BUY filled 後若隔天就漲停，浮動報酬會偏高但其實還沒出場。Phase 2 完整出場追蹤後改為 realized。
- **SELL 訊號沒有 limit_price 預設值**：generator 目前 SELL 不給目標價，validator 全部當市價處理（次日 open fill）。若未來 SELL 也加限價單機制，writer 不用改、validator 已支援。
- **不追蹤實際成交**：journal 是「假設」的，跟 `trades_{account}.csv` 的實際買賣紀錄是兩條獨立的線。對照兩者可以看出「我設定的策略掛單 vs 我實際買賣」的偏差。

## 過往 bug 與修法

- **pandas 3.x dtype 升級 raise TypeError**（5/24 修）：
  CSV 整欄空白會被讀成 float64，後續 `df.at[idx, 'validated_at'] = '2026-...'` 觸發 `Invalid value for dtype 'float64'`。
  fix：`validator.validate_partition()` 在寫入迴圈前先把 status / validated_at / fill_date / fill_price / bars_to_fill 全部 cast 成 object。
