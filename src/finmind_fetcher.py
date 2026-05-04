"""
P0-10：FinMind 還原股價 fetcher（免費版）
- TaiwanStockPriceAdj 是付費表 → 我們改用免費的事件表自己算還原
- data/dividends/{sid}.csv   -- 除權息事件
- data/splits/{sid}.csv      -- 拆分（TaiwanStockSplitPrice）
- data/reductions/{sid}.csv  -- 減資（TaiwanStockCapitalReductionReferencePrice）
- data/adjusted/{sid}.csv    -- 自算的還原股價（同 raw 欄位 + close_adj）

不破壞 data/raw/（手動下單 / positions 模組仍用 raw）。
未註冊 FinMind 限速 300 req/hr，每檔 3 個 API call → 80 檔 = 240 calls，OK。
"""

import os
import time
import requests
import pandas as pd
from src.utils import log_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
ADJ_DIR = os.path.join(BASE_DIR, "data", "adjusted")
DIV_DIR = os.path.join(BASE_DIR, "data", "dividends")
SPL_DIR = os.path.join(BASE_DIR, "data", "splits")
RED_DIR = os.path.join(BASE_DIR, "data", "reductions")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

DEFAULT_START = "2010-01-01"
SLEEP_SEC = 1.5          # 每個 API call sleep（兩個 dataset 之間）


# ── 核心 API 函式（免費表）────────────────────────────────────

def _get_dataset(dataset: str, stock_id: str, start: str, end: str,
                 token: str = "", retries: int = 3) -> pd.DataFrame:
    """取單檔單 dataset，含重試 + 付費表偵測"""
    params = {"dataset": dataset, "data_id": str(stock_id),
              "start_date": start, "end_date": end}
    if token:
        params["token"] = token

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(FINMIND_URL, params=params, timeout=60)
            # 付費表會回 400 含 "Sponsor"
            if r.status_code == 400 and "Sponsor" in r.text:
                log_error("finmind", stock_id, f"{dataset} 是付費表")
                return pd.DataFrame()
            r.raise_for_status()
            j = r.json()
            if j.get("status") != 200:
                if attempt < retries:
                    time.sleep(5 * attempt)
                    continue
                return pd.DataFrame()
            return pd.DataFrame(j.get("data", []))
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(5 * attempt)
                continue
            log_error("finmind", stock_id, f"{dataset} HTTP error: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def fetch_dividend_events(stock_id: str, start: str, end: str, token: str = "") -> pd.DataFrame:
    """除權息事件（含現金股息、股票股利）。免費。"""
    return _get_dataset("TaiwanStockDividend", stock_id, start, end, token)


def fetch_split_events(stock_id: str, start: str, end: str, token: str = "") -> pd.DataFrame:
    """拆分事件（TaiwanStockSplitPrice）。免費。"""
    return _get_dataset("TaiwanStockSplitPrice", stock_id, start, end, token)


def fetch_reduction_events(stock_id: str, start: str, end: str, token: str = "") -> pd.DataFrame:
    """減資事件（TaiwanStockCapitalReductionReferencePrice）。免費。
    主要欄位：
      date                              減資基準日（恢復交易日）
      ClosingPriceonTheLastTradingDay   減資前最後收盤價
      PostReductionReferencePrice       減資後參考價
      ReasonforCapitalReduction         減資原因
    """
    return _get_dataset("TaiwanStockCapitalReductionReferencePrice",
                        stock_id, start, end, token)


# ── 還原股價計算（向後復權）──────────────────────────────────

def calc_adj_close(raw_close: pd.Series, dividends: pd.DataFrame,
                   splits: pd.DataFrame,
                   reductions: pd.DataFrame | None = None) -> pd.Series:
    """
    向後復權 (backward adjustment):
    從舊事件往新事件走，每個事件把「事件日(不含當日)之前」的歷史價格乘上 factor。
    現在的價格不動。

    - 除息: factor = (P_prev_close - cash_div) / P_prev_close
    - 除權: factor = 1 / (1 + stock_div / 10)
    - 拆分: factor = after_price / before_price        (拆分 factor < 1)
    - 減資: factor = after_price / before_price        (減資 factor > 1)
            事件來自 TaiwanStockCapitalReductionReferencePrice
            before = ClosingPriceonTheLastTradingDay
            after  = PostReductionReferencePrice
    """
    adj = raw_close.copy().astype(float)
    events = []

    # ── 除息（現金股息）──
    if not dividends.empty:
        for _, row in dividends.iterrows():
            ex_date_str = row.get("CashExDividendTradingDate") or ""
            cash_div = float(row.get("CashEarningsDistribution") or 0) + \
                       float(row.get("CashStatutorySurplus") or 0)
            if ex_date_str and cash_div > 0:
                ex_date = pd.to_datetime(ex_date_str)
                prev_idx = adj.index[adj.index < ex_date]
                if len(prev_idx) > 0:
                    p_prev = adj.loc[prev_idx[-1]]
                    if p_prev > 0 and cash_div < p_prev:
                        factor = (p_prev - cash_div) / p_prev
                        events.append((ex_date, factor))

            # ── 除權（股票股利）──
            stock_div = float(row.get("StockEarningsDistribution") or 0) + \
                        float(row.get("StockStatutorySurplus") or 0)
            if stock_div > 0:
                stock_ex = row.get("StockExDividendTradingDate") or ex_date_str
                if stock_ex:
                    ex_dt = pd.to_datetime(stock_ex)
                    factor_s = 1 / (1 + stock_div / 10)
                    events.append((ex_dt, factor_s))

    # ── 拆分（TaiwanStockSplitPrice）──
    if not splits.empty:
        for _, row in splits.iterrows():
            sp_date = pd.to_datetime(row["date"])
            before = float(row.get("before_price") or 0)
            after = float(row.get("after_price") or 0)
            if before > 0 and after > 0:
                factor = after / before
                events.append((sp_date, factor))

    # ── 減資（TaiwanStockCapitalReductionReferencePrice）──
    if reductions is not None and not reductions.empty:
        for _, row in reductions.iterrows():
            rd_date = pd.to_datetime(row["date"])
            before = float(row.get("ClosingPriceonTheLastTradingDay") or 0)
            after = float(row.get("PostReductionReferencePrice") or 0)
            if before > 0 and after > 0:
                factor = after / before
                events.append((rd_date, factor))

    events.sort(key=lambda x: x[0])
    for ed, factor in events:
        mask = adj.index < ed
        adj.loc[mask] = adj.loc[mask] * factor

    return adj


# ── 本地 raw 載入 ────────────────────────────────────────────

def _load_raw(sid: str) -> pd.DataFrame | None:
    path = os.path.join(RAW_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, dtype={"date": str})
    if df.empty or "close" not in df.columns:
        return None
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.sort_values("date").set_index("date")


# ── 儲存 ─────────────────────────────────────────────────────

def _save_csv(path: str, df: pd.DataFrame):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _save_adjusted(sid: str, raw: pd.DataFrame, adj_series: pd.Series):
    """寫 data/adjusted/{sid}.csv：保留 raw 全部欄位 + close_adj"""
    os.makedirs(ADJ_DIR, exist_ok=True)
    out = raw.copy()
    out["close_adj"] = adj_series
    out.index = out.index.strftime("%Y%m%d")
    out.index.name = "date"
    out.to_csv(os.path.join(ADJ_DIR, f"{sid}.csv"), encoding="utf-8-sig")


# ── 批次抓取 ────────────────────────────────────────────────

def fetch_one(sid: str, start: str, end: str, token: str = "") -> dict:
    """單檔：抓 dividend + split + reduction → 算 adj_close → 寫 4 個 CSV"""
    div = fetch_dividend_events(sid, start, end, token)
    time.sleep(SLEEP_SEC)
    spl = fetch_split_events(sid, start, end, token)
    time.sleep(SLEEP_SEC)
    red = fetch_reduction_events(sid, start, end, token)

    # 寫事件原始資料（即使空也寫，方便下游讀取）
    _save_csv(os.path.join(DIV_DIR, f"{sid}.csv"), div)
    _save_csv(os.path.join(SPL_DIR, f"{sid}.csv"), spl)
    _save_csv(os.path.join(RED_DIR, f"{sid}.csv"), red)

    # 算還原股價（需要本地 raw）
    raw = _load_raw(sid)
    if raw is None:
        return {"sid": sid, "div": len(div), "spl": len(spl), "red": len(red),
                "adj_rows": 0, "warn": "no raw"}

    adj_series = calc_adj_close(raw["close"], div, spl, red)
    _save_adjusted(sid, raw, adj_series)

    return {"sid": sid, "div": len(div), "spl": len(spl), "red": len(red),
            "adj_rows": len(adj_series), "warn": ""}


def fetch_all(stock_ids: list, start: str = DEFAULT_START,
              end: str = "today", token: str = "",
              skip_existing: bool = False) -> dict:
    """批次抓多檔。

    Args:
        stock_ids: 股票代號清單
        start: 起始日期（YYYY-MM-DD）
        end: 結束日期，"today" 表示今天
        token: FinMind token（空字串 = 未註冊，300 req/hr 上限）
        skip_existing: True = 已有 adjusted CSV 的跳過（增量模式）

    Returns:
        {"success": [...], "failed": [...], "no_raw": [...]}
    """
    from datetime import date as date_cls
    if end == "today":
        end = date_cls.today().strftime("%Y-%m-%d")

    print(f"\n{'='*64}")
    print(f"  FinMind fetch-adjusted: {len(stock_ids)} 檔  ({start} ~ {end})")
    print(f"{'='*64}")

    results = {"success": [], "failed": [], "no_raw": []}
    total = len(stock_ids)

    for i, sid in enumerate(stock_ids, 1):
        sid = str(sid)
        adj_path = os.path.join(ADJ_DIR, f"{sid}.csv")
        if skip_existing and os.path.exists(adj_path):
            print(f"  [{i:3d}/{total}] {sid}: 已存在，跳過")
            results["success"].append(sid)
            continue

        print(f"  [{i:3d}/{total}] {sid}...", end=" ", flush=True)

        try:
            r = fetch_one(sid, start, end, token)
        except Exception as e:
            print(f"FAIL: {e}")
            log_error("finmind", sid, str(e))
            results["failed"].append(sid)
            time.sleep(SLEEP_SEC)
            continue

        if r["warn"] == "no raw":
            print(f"[WARN] 缺 data/raw/{sid}.csv  (div={r['div']}, spl={r['spl']}, red={r['red']})")
            results["no_raw"].append(sid)
        else:
            print(f"OK  div={r['div']:>2}  spl={r['spl']}  red={r['red']}  adj_rows={r['adj_rows']}")
            results["success"].append(sid)

        time.sleep(SLEEP_SEC)

    print(f"\n{'='*64}")
    print(f"  成功: {len(results['success'])}  "
          f"缺 raw: {len(results['no_raw'])}  失敗: {len(results['failed'])}")
    if results["no_raw"]:
        print(f"  缺 raw 的需先跑: python main.py fetch <sids>")
        print(f"  list: {' '.join(results['no_raw'])}")
    if results["failed"]:
        print(f"  失敗清單: {' '.join(results['failed'])}")
    print(f"{'='*64}")
    return results
