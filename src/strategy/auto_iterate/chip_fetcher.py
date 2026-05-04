"""Fetch and cache institutional chip data (FinMind TaiwanStockInstitutionalInvestorsBuySell)."""
import os
import time
import requests
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
CHIPS_DIR = os.path.join(BASE_DIR, "data", "chips")

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
CHIP_START  = "2013-01-01"
CHIP_END    = "2026-04-22"


def fetch_chip_data(sid: str, force: bool = False) -> pd.DataFrame:
    """Fetch chip data from FinMind; cache to data/chips/{sid}.csv.

    Returns DataFrame with columns foreign_net, trust_net (index = date).
    If cached file exists and force=False, loads from disk instead.
    """
    os.makedirs(CHIPS_DIR, exist_ok=True)
    path = os.path.join(CHIPS_DIR, f"{sid}.csv")

    if os.path.exists(path) and not force:
        df = pd.read_csv(path, parse_dates=["date"], index_col="date")
        return df

    r = requests.get(FINMIND_URL, params={
        "dataset":    "TaiwanStockInstitutionalInvestorsBuySell",
        "data_id":    sid,
        "start_date": CHIP_START,
        "end_date":   CHIP_END,
    }, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        raise RuntimeError(
            f"{sid} FinMind status={j.get('status')}: {j.get('msg','')}")

    raw = pd.DataFrame(j.get("data", []))
    if raw.empty:
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
    wide.to_csv(path)
    return wide


def load_chip_data(sid: str) -> pd.DataFrame:
    """Load cached chip data; returns empty DataFrame if not found."""
    path = os.path.join(CHIPS_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["date"], index_col="date")
