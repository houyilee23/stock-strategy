"""Fetch and cache institutional chip data (FinMind TaiwanStockInstitutionalInvestorsBuySell)."""
import os
import time
import requests
import pandas as pd
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
CHIPS_DIR = os.path.join(BASE_DIR, "data", "chips")

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
CHIP_START  = "2013-01-01"
# CHIP_END 動態用今天，避免 hardcode 過時（2026-05-19 修：原來寫死 2026-04-22 → 籌碼永遠不會更新）


def fetch_chip_data(sid: str, force: bool = False, refresh_if_stale_days: int = 1) -> pd.DataFrame:
    """Fetch chip data from FinMind; cache to data/chips/{sid}.csv.

    Returns DataFrame with columns foreign_net, trust_net (index = date).

    Behavior:
      - 若 cache 不存在 → 抓全範圍 (CHIP_START ~ today)
      - 若 cache 存在但 force=True → 強制重抓全範圍
      - 若 cache 存在且最新一筆距今超過 refresh_if_stale_days 天 → 從上次最新後一天接著抓
      - 否則直接讀 cache
    """
    os.makedirs(CHIPS_DIR, exist_ok=True)
    path = os.path.join(CHIPS_DIR, f"{sid}.csv")
    chip_end = date.today().strftime("%Y-%m-%d")

    # 既有 cache 的處理
    existing_df = None
    fetch_start = CHIP_START
    if os.path.exists(path) and not force:
        existing_df = pd.read_csv(path, parse_dates=["date"], index_col="date")
        if existing_df.empty:
            existing_df = None
        else:
            last_dt = existing_df.index.max()
            days_stale = (pd.Timestamp.today() - last_dt).days
            if days_stale <= refresh_if_stale_days:
                return existing_df  # cache 夠新，直接用
            # 增量抓：從 last_dt 隔天起
            fetch_start = (last_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            if fetch_start > chip_end:
                return existing_df  # 沒有新資料區間

    try:
        r = requests.get(FINMIND_URL, params={
            "dataset":    "TaiwanStockInstitutionalInvestorsBuySell",
            "data_id":    sid,
            "start_date": fetch_start,
            "end_date":   chip_end,
        }, timeout=60)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # FinMind 限速（402/403/429）→ 用既有 cache 撐過去，不影響策略執行
        if existing_df is not None and r.status_code in (402, 403, 429):
            return existing_df
        raise
    j = r.json()
    if j.get("status") != 200:
        if existing_df is not None:
            return existing_df
        raise RuntimeError(
            f"{sid} FinMind status={j.get('status')}: {j.get('msg','')}")

    raw = pd.DataFrame(j.get("data", []))
    if raw.empty:
        # 增量模式下新區間無資料是正常的（週末/假日）→ 直接回傳既有 cache
        if existing_df is not None:
            return existing_df
        raise RuntimeError(f"{sid} 籌碼資料為空")

    raw["date"] = pd.to_datetime(raw["date"])
    raw[["buy", "sell"]] = (raw[["buy", "sell"]]
                            .apply(pd.to_numeric, errors="coerce")
                            .fillna(0))
    raw["net"] = raw["buy"] - raw["sell"]

    pivot = raw[raw["name"].isin(["Foreign_Investor", "Investment_Trust"])].copy()
    wide = (pivot.pivot_table(index="date", columns="name",
                              values="net", aggfunc="sum")
            .fillna(0))
    wide.columns.name = None
    wide = wide.rename(columns={
        "Foreign_Investor": "foreign_net",
        "Investment_Trust": "trust_net",
    })
    for c in ("foreign_net", "trust_net"):
        if c not in wide.columns:
            wide[c] = 0.0

    wide = wide.sort_index()
    # 增量模式：合併既有 cache + 新抓到的
    if existing_df is not None:
        wide = pd.concat([existing_df, wide])
        wide = wide[~wide.index.duplicated(keep="last")].sort_index()
    wide.to_csv(path)
    return wide


def load_chip_data(sid: str) -> pd.DataFrame:
    """Load cached chip data; returns empty DataFrame if not found."""
    path = os.path.join(CHIPS_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["date"], index_col="date")
