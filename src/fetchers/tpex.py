"""TPEX（上櫃）單月日線抓取。

端點：https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php
參數：l=zh-tw, d=YYYY/MM（西元年）, s=0,asc,0, o=json, id=股票代號
回傳：aaData 陣列，每列 9 欄

設計：與 twse.py 完全平行，無需理解對方就能維護。
未來若 TPEX 改 API 端點，只需動本檔。
"""
from __future__ import annotations
import time
import requests
import urllib3
import pandas as pd
from src.utils import setup_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger()

TPEX_HISTORY_URL = (
    "https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php"
)

COLUMNS = ["date", "open", "high", "low", "close",
           "volume", "turnover", "transactions", "price_change"]


def _clean(v) -> str | None:
    """移除千位逗號；'--' / 'N/A' 等視同無資料。"""
    s = str(v).replace(",", "").strip()
    return s if s not in ("", "--", "---", "N/A") else None


def _to_float(v) -> float | None:
    s = _clean(v)
    try:
        return float(s) if s else None
    except ValueError:
        return None


def _to_int(v) -> int:
    s = _clean(v)
    try:
        return int(s) if s else 0
    except ValueError:
        return 0


def _parse_response(data: dict) -> pd.DataFrame:
    """解析 TPEX aaData。aaData 欄位順序：
      [0] 日期 (民國 YYY/MM/DD)
      [1] 成交股數
      [2] 成交金額
      [3] 開盤價
      [4] 最高價
      [5] 最低價
      [6] 收盤價
      [7] 漲跌
      [8] 成交筆數
    """
    if not data:
        return pd.DataFrame()
    aa_data = data.get("aaData", [])
    if not aa_data:
        return pd.DataFrame()

    rows = []
    for r in aa_data:
        if len(r) < 9:
            continue
        try:
            # 民國年 "113/04/01" → 西元 "20240401"
            parts = str(r[0]).strip().split("/")
            if len(parts) != 3:
                continue
            ad_year = int(parts[0]) + 1911
            date_str = f"{ad_year}{int(parts[1]):02d}{int(parts[2]):02d}"

            c = _to_float(r[6])
            if c is None:
                continue  # 無收盤價（停牌等）

            rows.append({
                "date":         date_str,
                "open":         _to_float(r[3]) or c,
                "high":         _to_float(r[4]) or c,
                "low":          _to_float(r[5]) or c,
                "close":        c,
                "volume":       _to_int(r[1]),
                "turnover":     _to_int(r[2]),
                "transactions": _to_int(r[8]),
                "price_change": _clean(r[7]) or "0",
            })
        except (ValueError, IndexError):
            continue

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["date"] = df["date"].astype(str)
    return df


def fetch_monthly(stock_id: str, year: int, month: int,
                  retries: int = 3) -> pd.DataFrame:
    """抓 TPEX 單月日線資料。"""
    params = {
        "l": "zh-tw",
        "d": f"{year}/{month:02d}",
        "s": "0,asc,0",
        "o": "json",
        "id": str(stock_id),
    }
    data = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(TPEX_HISTORY_URL, params=params,
                                timeout=30, verify=False)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            logger.warning(f"  [{stock_id}] TPEX {year}/{month:02d} "
                           f"第{attempt}次失敗：{e}")
            if attempt < retries:
                time.sleep(5)
    if not data:
        return pd.DataFrame()
    return _parse_response(data)
