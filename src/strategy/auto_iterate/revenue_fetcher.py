"""Fetch and cache Taiwan monthly revenue data
(FinMind dataset = TaiwanStockMonthRevenue).

台灣上市櫃公司依規定每月 10 號前公布上月營收 → 我們把 announcement_date
保守設為 (FinMind 'date' + 10 天)，做為訊號可用日 T。

Cache to data/monthly_revenue/{sid}.csv (utf-8-sig).

CSV columns:
    date                       FinMind 原始 date（為「revenue 期月之次月 1 號」）
    revenue_year               營收年（例：2023）
    revenue_month              營收月（例：12，代表 2023/12 月營收）
    revenue                    當月營收（NTD）
    announcement_date          訊號可用日（保守 = date + 10 天）
    revenue_growth_yoy_pct     YoY 成長率（小數，0.30 = +30%）。同月份比上一年。
                               若上一年同月份缺資料 → NaN
"""
import os
import time
import datetime as _dt
import requests
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
REV_DIR = os.path.join(BASE_DIR, "data", "monthly_revenue")

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
DEFAULT_START = "2015-01-01"

# 未註冊版 300 req/hr → 每 12 秒一個 call 才安全
SLEEP_SEC = 12.0

# 公布期限：法規規定每月 10 號前公布上月營收 → +10 天保守可用
ANNOUNCEMENT_LAG_DAYS = 10


def _compute_yoy(df: pd.DataFrame) -> pd.Series:
    """以 (revenue_year, revenue_month) 為主鍵，計算 YoY。

    回傳對齊原 df 順序的 Series（小數），無前一年資料則為 NaN。
    """
    key = list(zip(df["revenue_year"], df["revenue_month"]))
    rev_map = dict(zip(key, df["revenue"].astype(float)))
    yoys = []
    for y, m, cur in zip(df["revenue_year"], df["revenue_month"], df["revenue"]):
        prev = rev_map.get((int(y) - 1, int(m)))
        if prev is None or prev <= 0 or pd.isna(prev):
            yoys.append(float("nan"))
        else:
            yoys.append(float(cur) / float(prev) - 1.0)
    return pd.Series(yoys, index=df.index, dtype=float)


def fetch_revenue_data(
    sid: str,
    start_date: str = DEFAULT_START,
    end_date: str | None = None,
    force: bool = False,
    timeout: int = 60,
) -> pd.DataFrame:
    """Fetch monthly revenue from FinMind; cache to data/monthly_revenue/{sid}.csv.

    Returns DataFrame with columns:
      date, revenue_year, revenue_month, revenue,
      announcement_date, revenue_growth_yoy_pct

    若 cache 已存在且 force=False，直接讀 cache。
    Empty FinMind response → 寫空檔（含 header）並回傳空 DataFrame。
    """
    os.makedirs(REV_DIR, exist_ok=True)
    path = os.path.join(REV_DIR, f"{sid}.csv")

    if os.path.exists(path) and not force:
        try:
            df = pd.read_csv(path, parse_dates=["date", "announcement_date"])
            return df
        except Exception:
            pass  # 損毀 → 重抓

    if end_date is None:
        end_date = _dt.date.today().strftime("%Y-%m-%d")

    r = requests.get(FINMIND_URL, params={
        "dataset":    "TaiwanStockMonthRevenue",
        "data_id":    str(sid),
        "start_date": start_date,
        "end_date":   end_date,
    }, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        raise RuntimeError(
            f"{sid} FinMind status={j.get('status')}: {j.get('msg', '')}")

    raw = pd.DataFrame(j.get("data", []))
    if raw.empty:
        # 寫空 header 也算 cache，避免重複打 API
        empty = pd.DataFrame(columns=[
            "date", "revenue_year", "revenue_month", "revenue",
            "announcement_date", "revenue_growth_yoy_pct",
        ])
        empty.to_csv(path, index=False, encoding="utf-8-sig")
        return empty

    raw["date"] = pd.to_datetime(raw["date"])
    raw["revenue_year"]  = pd.to_numeric(raw["revenue_year"], errors="coerce").astype("Int64")
    raw["revenue_month"] = pd.to_numeric(raw["revenue_month"], errors="coerce").astype("Int64")
    raw["revenue"]       = pd.to_numeric(raw["revenue"], errors="coerce")

    raw = raw.dropna(subset=["revenue_year", "revenue_month", "revenue"])
    raw = raw.sort_values(["revenue_year", "revenue_month"]).reset_index(drop=True)

    # announcement_date：保守取 FinMind date + 10 天（每月 10 號前公布完成）
    raw["announcement_date"] = raw["date"] + pd.Timedelta(days=ANNOUNCEMENT_LAG_DAYS)
    raw["revenue_growth_yoy_pct"] = _compute_yoy(raw)

    out = raw[[
        "date", "revenue_year", "revenue_month", "revenue",
        "announcement_date", "revenue_growth_yoy_pct",
    ]].copy()
    out.to_csv(path, index=False, encoding="utf-8-sig")
    return out


def load_revenue_data(sid: str) -> pd.DataFrame:
    """Load cached monthly revenue; returns empty DataFrame if not found.

    DataFrame is ordered by (revenue_year, revenue_month) ascending.
    """
    path = os.path.join(REV_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, parse_dates=["date", "announcement_date"])
        return df
    except Exception:
        return pd.DataFrame()


def fetch_all_revenue(stock_ids: list, start_date: str = DEFAULT_START,
                      end_date: str | None = None,
                      skip_existing: bool = True) -> dict:
    """Batch fetch monthly revenue. Sleeps 12s between calls (rate limit).

    skip_existing: True → 已有 cache 的跳過。
    Returns {"success": [...], "failed": [...], "rate_limited": False}。
    若發生 429 / FinMind quota 用盡，提早收手（不再打 API），保留進度。
    """
    if end_date is None:
        end_date = _dt.date.today().strftime("%Y-%m-%d")

    print(f"\n{'='*64}")
    print(f"  FinMind fetch-revenue: {len(stock_ids)} 檔  ({start_date} ~ {end_date})")
    print(f"  rate-limit sleep: {SLEEP_SEC}s/call (未註冊上限 300 req/hr)")
    print(f"{'='*64}")

    results: dict = {"success": [], "failed": [], "skipped": [], "rate_limited": False}
    total = len(stock_ids)
    api_calls = 0

    for i, sid in enumerate(stock_ids, 1):
        sid = str(sid)
        path = os.path.join(REV_DIR, f"{sid}.csv")
        if skip_existing and os.path.exists(path):
            print(f"  [{i:3d}/{total}] {sid}: cache 已存在，跳過")
            results["skipped"].append(sid)
            results["success"].append(sid)
            continue

        print(f"  [{i:3d}/{total}] {sid}...", end=" ", flush=True)
        try:
            df = fetch_revenue_data(sid, start_date=start_date,
                                    end_date=end_date, force=False)
            api_calls += 1
            if df.empty:
                print("[WARN] 無營收資料 (可能是 ETF/新股)")
            else:
                yoy_avail = df["revenue_growth_yoy_pct"].notna().sum()
                print(f"OK rows={len(df)} yoy_available={yoy_avail}")
            results["success"].append(sid)
        except requests.HTTPError as e:
            sc = getattr(e.response, "status_code", None)
            if sc in (402, 429):
                print(f"[RATE-LIMIT] {sc} → 提早結束，保留 {i-1} 進度")
                results["failed"].append(sid)
                results["rate_limited"] = True
                break
            print(f"FAIL HTTP {sc}: {e}")
            results["failed"].append(sid)
        except Exception as e:
            print(f"FAIL: {e}")
            results["failed"].append(sid)

        # 每次 API call 後 sleep；skip_existing 已 continue 不會 sleep
        if i < total:
            time.sleep(SLEEP_SEC)

    print(f"\n{'='*64}")
    print(f"  成功：{len(results['success'])}  失敗：{len(results['failed'])}  "
          f"跳過(已存在)：{len(results['skipped'])}  api_calls：{api_calls}")
    if results["rate_limited"]:
        print(f"  [INFO] FinMind quota 觸發 rate-limit，未抓檔可稍後重跑")
    print(f"{'='*64}")
    return results
