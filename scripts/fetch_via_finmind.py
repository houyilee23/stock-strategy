"""Fallback raw 抓取：用 FinMind TaiwanStockPrice 補某些 TWSE/TPEX 月查詢無資料的股票

機制：
  TWSE/TPEX 的 monthly endpoint 對某些股票（5347, 6488 等）回傳空，
  但 FinMind 的 TaiwanStockPrice 有完整歷史。本腳本用 FinMind 拉資料、
  轉換為與 fetcher.py 寫入 raw 相同的 CSV 格式，然後跑既有的 fetch-adjusted。

用法：
  python scripts/fetch_via_finmind.py <sid> [<sid> ...]
"""
import os
import sys
import time
import argparse
import requests
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
START = "2010-01-01"
COLUMNS = ["date", "open", "high", "low", "close", "volume",
            "turnover", "transactions", "price_change"]


def fetch_finmind_raw(sid: str) -> pd.DataFrame | None:
    """從 FinMind 拉 TaiwanStockPrice，轉成 raw 格式。"""
    end = time.strftime("%Y-%m-%d")
    r = requests.get(FINMIND_URL, params={
        "dataset": "TaiwanStockPrice", "data_id": sid,
        "start_date": START, "end_date": end,
    }, timeout=120)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        return None
    data = j.get("data", [])
    if not data:
        return None

    # 欄位對應：FinMind → raw
    rows = []
    for d in data:
        date_str = d["date"].replace("-", "")  # YYYY-MM-DD → YYYYMMDD
        rows.append({
            "date": date_str,
            "open": d.get("open"),
            "high": d.get("max"),
            "low": d.get("min"),
            "close": d.get("close"),
            "volume": d.get("Trading_Volume"),
            "turnover": d.get("Trading_money"),
            "transactions": d.get("Trading_turnover"),
            "price_change": d.get("spread"),
        })
    df = pd.DataFrame(rows, columns=COLUMNS)
    df = df.sort_values("date").drop_duplicates("date", keep="last")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sids", nargs="+", help="股票代號")
    args = ap.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    success, failed = [], []

    for sid in args.sids:
        print(f"\n[{sid}] FinMind 抓取...")
        try:
            df = fetch_finmind_raw(sid)
        except Exception as e:
            print(f"  ✗ FinMind 異常：{e}")
            failed.append(sid)
            continue
        if df is None or df.empty:
            print(f"  ✗ 無資料")
            failed.append(sid)
            continue
        path = os.path.join(RAW_DIR, f"{sid}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  ✓ {len(df)} rows → {path} (first {df.iloc[0]['date']}, last {df.iloc[-1]['date']})")
        success.append(sid)

    print(f"\n總結：成功 {len(success)} / 失敗 {len(failed)}")
    if success:
        print(f"\n下一步：跑 adjusted")
        print(f"  python main.py fetch-adjusted {' '.join(success)}")


if __name__ == "__main__":
    main()
