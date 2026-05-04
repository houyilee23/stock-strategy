# Sonnet 修正回合 #4 — 改用還原股價（FinMind）

> Round 3 解了 portfolio mode 三個 bug，Katie MaxDD 從 -63% 降到 -31%。
> 但 Opus 隨後發現 **measurement instrument 本身壞了** —— 我們用 raw close 跑回測，
> 完全沒處理除權息、拆分、減資。這讓所有指標（CAGR、MaxDD、Alpha、regime）都不可信。
> 本輪用 FinMind 把資料和指標一次修對。

---

## 為什麼這輪一定要做

掃 `data/raw/` 全部股票，找出單日跳動 > 10%（台股漲跌停 ±10%，超過必然是價格事件不是市場波動），抓到 33 筆：

| 嚴重 case | 影響 |
|---|---|
| **0050 2025/06/18 -74.8%**（4:1 拆分）| baseline + regime 從 6/18 起完全失效 |
| **2408 南亞科 2014/09/09 +832%**（減資）| Takeshi 清單，這檔回測幾乎廢掉 |
| **2337 旺宏 2017/08/28 +124%**（減資）| Takeshi 清單 |
| **6271 同欣電 2020/11/30 +43%**（減資）| Takeshi 清單 |
| **2426 鼎元 2014/11/03 +61%**（減資）| Katie 清單 |
| 1227 佳格 / 9940 信義 各 5 次大除息 | Katie 高股息標的，每次 -10~-20% 被當虧損 |
| 1301 / 1303 / 2002 / 2303 / 2454 等多檔每年除息 | 全部都被汙染 |

具體被低估的程度：
- **0050 baseline CAGR 1.84%（程式算）→ ~22%（真實含息）**，低估約 20%
- 個股策略每年漏掉 3-5% 股息收益，累積 9 年 30-50% 不見

→ 我們前 3 個 round 修的方向都對，但**用一支歪掉的尺去微調**，必須先把尺修直。

---

## 為什麼用 FinMind？

- 開源台股資料 API（GitHub 4k+ star，台灣團隊維護）
- 有 `TaiwanStockPriceAdj` 表：**1994-10-01 ~ now，已算好還原權息**
- 有 `TaiwanStockDividend` 表：每檔每次除權息事件（金額、除息日、除權日）
- 完全免費（未註冊 300 req/hr，註冊後 600/hr）
- 我們需要量：80 檔 × 1 個 date range = 80 calls，遠低於 300/hr 上限 → **不需要註冊 token**

文件：https://finmind.github.io/tutor/TaiwanMarket/Technical/

---

## 必修任務

### 🔴 P0-10：寫 FinMind fetcher（取代 raw 為唯一資料源是錯的，要並存）

**位置**：新檔 `src/finmind_fetcher.py`

**設計原則**：
- **不破壞** `data/raw/`（手動下單時參考的就是 raw price）
- 新增 `data/adjusted/{sid}.csv`（還原股價，給策略訊號用）
- 新增 `data/dividends/{sid}.csv`（除權息事件表，給驗證用）

**核心函式**：

```python
import requests, pandas as pd, time

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

def fetch_adjusted_price(stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """抓單檔還原股價，欄位對齊我們現有 raw CSV 結構"""
    params = {
        "dataset": "TaiwanStockPriceAdj",
        "data_id": str(stock_id),
        "start_date": start_date,
        "end_date": end_date,
    }
    r = requests.get(FINMIND_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # FinMind 欄位 -> 我們的命名
    df = df.rename(columns={
        "Trading_Volume": "volume",
        "Trading_money": "turnover",
        "max": "high",
        "min": "low",
        "Trading_turnover": "transactions",
        "spread": "price_change",
    })
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d")
    cols = ["date", "open", "high", "low", "close", "volume", "turnover", "transactions", "price_change"]
    return df[[c for c in cols if c in df.columns]]


def fetch_dividend_events(stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """抓除權息事件（含現金股息、股票股利）"""
    params = {
        "dataset": "TaiwanStockDividend",
        "data_id": str(stock_id),
        "start_date": start_date,
        "end_date": end_date,
    }
    r = requests.get(FINMIND_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json().get("data", [])
    return pd.DataFrame(data) if data else pd.DataFrame()
```

**CLI 整合**：
- `main.py` 新增 `fetch-adjusted` 子命令（不要動現有 `fetch`，那個抓 raw）
- `python main.py fetch-adjusted --list research --start 2010-01-01`
- 自動 sleep 2 秒/檔避免被限速

### 🔴 P0-11：抓所有 80 檔的還原資料

執行：
```bash
python main.py fetch-adjusted --all --start 2010-01-01
```

**驗證**：
- `data/adjusted/` 下應有 80 個 CSV（`exception` 4 檔不抓）
- 抓完後拿 0050 對照：`data/raw/0050.csv` 6/18 開盤 47.5，`data/adjusted/0050.csv` 同日應該是 ~190 元（拆分回推還原）
- 拿 1227 佳格對照：raw 在 2010/08/02 跌 -10.9%（除息日），adjusted 該日無顯著跌幅

### 🔴 P0-12：策略訊號改用 adj_close

**改動範圍**：

1. **`scripts/round3_report.py` 的 `load_stock()`**：改讀 `data/adjusted/{sid}.csv`
2. **`src/strategy/runner.py`**：策略路徑改用 adjusted
3. **`src/strategy/signals/regime.py`**：偵測 0050 用 adjusted（這支讓 6/18 後 regime 不再壞）
4. **`src/strategy/runner.py:_calc_benchmark_cagr`**：baseline 用 adjusted

**保留 raw 的用途**：
- `python main.py signals` 顯示給用戶看的「今日進場價」要用 raw（手動下單看到的價格）
- `positions` 模組評估持倉成本/市值用 raw

### 🔴 P0-13：補 portfolio 層的 in_market_cagr

**位置**：`src/strategy/backtest/result.py`

`PortfolioResult` 已有 `in_market_pct` (有持倉日數佔比)，但沒有 `in_market_cagr`。
Round 3 結果顯示 Katie 利用率只有 41%，CAGR 4.73% 是被 60% 現金稀釋過的，無法判斷策略本身好壞。

新增：
```python
@property
def in_market_cagr(self) -> float:
    """只算有持倉時段的年化報酬"""
    if self.equity_curve.empty:
        return float("nan")
    # 用每日 holdings 字典判斷該日是否有持倉
    eq = self.equity_curve
    in_market_mask = pd.Series(
        [bool(self.holdings_history.get(d, {})) for d in eq.index],
        index=eq.index,
    )
    if not in_market_mask.any():
        return float("nan")
    # 取有持倉那段的子序列，跨段斷點處用 forward-fill 接續
    # 簡化版：daily return 只算 in-market 那天，乘起來年化
    daily_ret = eq.pct_change().fillna(0)
    in_market_ret = daily_ret[in_market_mask]
    total_growth = (1 + in_market_ret).prod()
    in_market_days = len(in_market_ret)
    if in_market_days <= 0:
        return float("nan")
    years = in_market_days / 252  # 252 交易日/年
    return total_growth ** (1 / years) - 1
```

**注意**：engine 必須記錄 `holdings_history: dict[date, dict[sid, shares]]`，目前 engine 不一定有，需要看 `engine.py:run_portfolio` 是否補欄位。

### 🔴 P0-14：除權息事件驗證

寫 `scripts/verify_adjustment.py`：
1. 掃 `data/raw/` 找所有單日 |chg| > 10% 的事件（共 33 筆已知）
2. 對照 `data/dividends/{sid}.csv`，每筆事件查當日是否有除權除息記錄
3. 列出「raw 跳動但 dividend 表沒對應紀錄」的事件 → 可能是 split / 減資 / M&A，需手動補

預期能涵蓋 ~80% 事件，剩 20% 應該是減資 / 拆分（FinMind 可能有獨立的 `TaiwanStockSplitPrice` 表，可一起查）。

無法解釋的 case 列出來給 Opus 評估。

---

## 同時要做的驗證

### Sanity gate 補強

```python
# tests/test_sanity_gates.py 新增
def test_0050_adj_cagr_reasonable():
    """0050 還原股價 CAGR 應落在 5%~25%（含拆分還原）"""
    df = pd.read_csv("data/adjusted/0050.csv")
    # ... compute CAGR
    assert 0.05 <= cagr <= 0.25, f"0050 adj CAGR={cagr:.1%} 異常"

def test_no_extreme_jumps_in_adj():
    """還原後不應有單日 > 30% 的跳動（除非真的是熔斷級事件）"""
    for sid in TEST_LIST:
        df = pd.read_csv(f"data/adjusted/{sid}.csv")
        max_jump = df["close"].pct_change().abs().max()
        assert max_jump < 0.30, f"{sid} adj 最大跳動 {max_jump:.1%}"
```

### 重跑 Round 3 比對

```bash
python scripts/round3_report.py
```
再加一份 `scripts/round4_report.py`（複製 round3 但改讀 adjusted），印出對照表：

| 指標 | Round 3（raw）| Round 4（adj）| 差異 |
|---|---|---|---|
| 0050 baseline CAGR | 1.84% | ?% | |
| Katie portfolio CAGR | 4.73% | ?% | |
| Katie in_market_cagr | N/A | ?% | （新指標）|
| Katie MaxDD | -31.35% | ?% | |
| Katie Alpha | +2.89% | ?% | |
| Takeshi MaxDD | -44.04% | ?% | |
| Takeshi 利用率 | 25.51% | ?% | |

---

## 執行順序

1. P0-10 寫 finmind_fetcher（30 分）
2. P0-11 抓 80 檔 adjusted + dividend（5 分執行）
3. P0-14 verify_adjustment 對照舊 33 筆 → 列出無法解釋的（10 分）
   → **這裡停下回報 Opus**，確認剩餘 case 怎麼處理
4. P0-12 改用 adj_close（30 分）
5. P0-13 加 in_market_cagr（10 分）
6. 重跑 round3 + round4 對照（5 分）
7. sanity gate 全跑

---

## 不要做的事

- ❌ 不要刪 `data/raw/`（手動下單參考 + verify_adjustment 對照需要）
- ❌ 不要修 `config/watchlists.yaml`（Opus 已更新到 80 檔）
- ❌ 不要動 Style 1 的訊號參數（這輪只換資料來源，不調策略）
- ❌ 不要為了讓 sanity gate 過而調門檻
- ❌ 不要把 token 寫進 git 控制的檔案（這輪不需要 token，但若將來要用，存 `config/secrets.yaml` 並加 `.gitignore`）

---

## 預期結果

| 指標 | Round 3 | Round 4 預期 |
|---|---|---|
| 0050 baseline CAGR | 1.84% | **15-25%**（含拆分還原 + 含息）|
| Katie portfolio CAGR | 4.73% | 可能下降（Alpha 比錯對手）或上升（個股訊號變準）|
| Katie in_market_cagr | N/A | **應 > 8%** 才算策略有 edge |
| 各檔 MaxDD | 偏高 | **下降**（除權息日不再被當虧損）|
| Regime 6/18 後 | 異常 BEAR | **正常 BULL/BEAR 切換** |

如果 in_market_cagr 還是輸 0050 baseline → 個股訊號真的不夠強，再考慮調 Style 1。
如果勝過 → portfolio 層加大資金利用率（top_n、cash_reserve_pct 調整）才有意義。

---

## 回報格式

修完提供：

1. P0-10 ~ P0-14 各自改了什麼檔案、什麼行（diff 摘要）
2. `verify_adjustment.py` 輸出：33 筆價格事件中，FinMind dividend 表能解釋幾筆，不能解釋的列表
3. Round 3 vs Round 4 對照表（上面那張）
4. Sanity gate 全跑結果
5. 主觀判斷：策略 in_market_cagr 是否勝過真實 0050 含息報酬？
6. 卡住寫 `docs/BLOCKED_round4.md`

---

*Opus 設計、Sonnet 實作。Round 4 啟動。*
