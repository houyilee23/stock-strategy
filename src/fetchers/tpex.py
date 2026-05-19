"""TPEX（上櫃）單月日線抓取。

★ 端點（2026-05-19 更新）：
    POST https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock
    form data: code=<sid>&date=YYYY/MM/01

舊端點 st43_result.php 已被 TPEX 移除（回 404）。新端點是櫃買中心
「個股日成交資訊」頁面所使用的 API（從 HTML form 反推得到）。

回傳格式：
{
  "stat": "ok",
  "tables": [{
    "title":    "個股日成交資訊",
    "subtitle": "5371 中光電 113年05月",
    "fields":   ["日 期","成交張數","成交仟元","開盤","最高","最低","收盤","漲跌","筆數"],
    "data":     [["113/05/02","21,429","2,050,925","100.50",...], ...]
  }]
}

★ 單位注意：TPEX 是「張」(1000 股) 與「仟元」(1000 NTD)，本模組統一轉成
   TWSE 用的「股數」與「元」，使下游 CSV 對兩個市場一致。
"""
from __future__ import annotations
import time
import requests
import urllib3
import pandas as pd
from src.utils import setup_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger()

TPEX_STOCK_URL = "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"

# HTTP header：TPEX 後端會擋掉沒帶 user-agent 的請求
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

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
    """解析新版 TPEX 回傳；欄位順序：
      [0] 日期 (民國 YYY/MM/DD)
      [1] 成交張數 (千股) → ×1000 得股數
      [2] 成交仟元 (千 NTD) → ×1000 得元
      [3] 開盤  [4] 最高  [5] 最低  [6] 收盤
      [7] 漲跌  [8] 筆數
    """
    if not data or data.get("stat") != "ok":
        return pd.DataFrame()
    tables = data.get("tables", [])
    if not tables:
        return pd.DataFrame()
    aa_data = tables[0].get("data", [])
    if not aa_data:
        return pd.DataFrame()

    rows = []
    for r in aa_data:
        if len(r) < 9:
            continue
        try:
            # 民國年 "113/05/02" → 西元 "20240502"
            parts = str(r[0]).strip().split("/")
            if len(parts) != 3:
                continue
            ad_year = int(parts[0]) + 1911
            date_str = f"{ad_year}{int(parts[1]):02d}{int(parts[2]):02d}"

            c = _to_float(r[6])
            if c is None:
                continue  # 無收盤價（停牌等）

            # 注意單位轉換：TPEX 給張、仟元 → 統一成股數、元（與 TWSE 一致）
            vol_lots = _to_int(r[1])    # 張
            turn_kntd = _to_int(r[2])   # 千元

            rows.append({
                "date":         date_str,
                "open":         _to_float(r[3]) or c,
                "high":         _to_float(r[4]) or c,
                "low":          _to_float(r[5]) or c,
                "close":        c,
                "volume":       vol_lots * 1000,
                "turnover":     turn_kntd * 1000,
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
    """抓 TPEX 單月日線資料。

    用 POST，date 帶 AD 格式 YYYY/MM/01。
    """
    data = None
    payload = {"code": str(stock_id), "date": f"{year}/{month:02d}/01"}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(TPEX_STOCK_URL, data=payload,
                                 headers=HEADERS, timeout=30, verify=False)
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
