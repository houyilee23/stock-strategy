"""TWSE（上市）單月日線抓取。

端點：https://www.twse.com.tw/exchangeReport/STOCK_DAY
參數：response=json, date=YYYYMMDD, stockNo=股票代號
回傳：當月所有交易日的日線 OHLCV

設計：單一職責 — 只負責 TWSE。失敗回空 DataFrame，由 coordinator 決定後續動作。
"""
from __future__ import annotations
import time
import requests
import urllib3
import pandas as pd
from src.utils import setup_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger()

TWSE_HISTORY_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"

COLUMNS = ["date", "open", "high", "low", "close",
           "volume", "turnover", "transactions", "price_change"]


def _parse_response(data: dict) -> pd.DataFrame:
    """解析 TWSE JSON：stat='OK' 才有 data 陣列；民國年→西元年。"""
    if not data or data.get("stat") != "OK":
        return pd.DataFrame()
    raw_rows = data.get("data", [])
    if not raw_rows:
        return pd.DataFrame()

    rows = []
    for r in raw_rows:
        try:
            # 日期格式："114/04/01"（民國/月/日）
            parts = r[0].strip().split("/")
            ad_year = int(parts[0]) + 1911
            date_str = f"{ad_year}{int(parts[1]):02d}{int(parts[2]):02d}"

            rows.append({
                "date":         date_str,
                "volume":       int(r[1].replace(",", "")),
                "turnover":     int(r[2].replace(",", "")),
                "open":         float(r[3].replace(",", "")),
                "high":         float(r[4].replace(",", "")),
                "low":          float(r[5].replace(",", "")),
                "close":        float(r[6].replace(",", "")),
                "price_change": r[7].replace(",", ""),
                "transactions": int(r[8].replace(",", "")),
            })
        except (ValueError, IndexError):
            continue

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["date"] = df["date"].astype(str)
    return df


def fetch_monthly(stock_id: str, year: int, month: int,
                  retries: int = 2) -> pd.DataFrame:
    """抓 TWSE 單月日線資料。

    嘗試該月前 5 天的日期作 query date（TWSE 任一存在日期都會回傳整月）。
    全部失敗回空 DataFrame。

    韌性策略（2026-06-04 加入，避免 TWSE 慢時拖死整個 pipeline）：
      - timeout 30s → 8s（正常回應 <1s；超過 8s 視同 TWSE 異常）
      - retries 3 → 2
      - day 範圍 10 → 5
      - 連續 2 天 query 全 timeout → 放棄該月，不再蠻幹
    """
    consecutive_timeout_days = 0
    for day in range(1, 6):
        date_param = f"{year}{month:02d}{day:02d}"
        params = {"response": "json", "date": date_param, "stockNo": stock_id}
        day_all_failed = True  # 該 day 是否每次嘗試都因 exception 失敗
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(TWSE_HISTORY_URL, params=params,
                                    timeout=8, verify=False)
                resp.raise_for_status()
                df = _parse_response(resp.json())
                day_all_failed = False
                if not df.empty:
                    return df
                break  # 該日期 query 沒資料 → 試下一個 day
            except Exception as e:
                logger.warning(f"  [{stock_id}] TWSE {year}/{month:02d}/{day:02d} "
                               f"第{attempt}次失敗：{e}")
                if attempt < retries:
                    time.sleep(2)
        if day_all_failed:
            consecutive_timeout_days += 1
            if consecutive_timeout_days >= 2:
                logger.warning(f"  [{stock_id}] TWSE {year}/{month:02d} "
                               f"連續 {consecutive_timeout_days} 天全 timeout，放棄此月")
                return pd.DataFrame()
        else:
            consecutive_timeout_days = 0
    return pd.DataFrame()
