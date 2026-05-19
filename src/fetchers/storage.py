"""Raw CSV 儲存：合併寫入、抓現有日期範圍、計算缺漏月份。

跟「從哪裡抓」「怎麼抓」完全解耦：拿到任何來源的 DataFrame 都能寫進去。
"""
from __future__ import annotations
import os
import pandas as pd
from src.utils import raw_file_path, is_current_month


def get_existing_date_range(stock_id: str) -> tuple[str, str] | None:
    """讀 raw CSV，回 (min_date, max_date) 字串或 None。"""
    path = raw_file_path(stock_id)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype={"date": str})
        if df.empty or "date" not in df.columns:
            return None
        return df["date"].min(), df["date"].max()
    except Exception:
        return None


def get_missing_months(stock_id: str, all_months: list) -> list:
    """比對本地 raw 已有資料，回傳需要重抓的 (year, month) 清單。

    規則：
      - 當月永遠列入（每日更新）
      - 本地最後一筆所在月份也列入（補抓 tail-end，避免月底資料漏抓）
      - 該月在 raw CSV 完全沒資料 → 列入
    """
    path = raw_file_path(stock_id)
    if not os.path.exists(path):
        return all_months

    try:
        df = pd.read_csv(path, dtype={"date": str})
        if df.empty:
            return all_months
        existing_dates = set(df["date"].tolist())
    except Exception:
        return all_months

    max_date = max(existing_dates) if existing_dates else None
    tail_ym = ((int(max_date[:4]), int(max_date[4:6]))
               if max_date and len(max_date) == 8 else None)

    missing = []
    for year, month in all_months:
        if is_current_month(year, month):
            missing.append((year, month))
            continue
        if tail_ym == (year, month):
            missing.append((year, month))
            continue
        prefix = f"{year}{month:02d}"
        if not any(d.startswith(prefix) for d in existing_dates):
            missing.append((year, month))
    return missing


def save_raw_data(stock_id: str, new_df: pd.DataFrame):
    """合併寫入 raw CSV，去除重複、依日期排序。"""
    path = raw_file_path(stock_id)
    if os.path.exists(path):
        try:
            existing = pd.read_csv(path, dtype={"date": str})
            combined = pd.concat([existing, new_df], ignore_index=True)
        except Exception:
            combined = new_df
    else:
        combined = new_df

    combined = (combined.drop_duplicates(subset="date")
                .sort_values("date")
                .reset_index(drop=True))
    combined.to_csv(path, index=False, encoding="utf-8-sig")
