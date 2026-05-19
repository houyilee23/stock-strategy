"""統籌：依市場別 dispatch、自動偵測未知市場、整體 fetch pipeline。

加新市場（例：興櫃 emerging）只要：
  1. 寫 src/fetchers/emerging.py 提供 fetch_monthly(sid, y, m)
  2. 在 MARKETS dict 加一行
  3. 在 metadata.MARKET_PATH 註解補上 'emerging' 說明
其他 fetcher 模組完全不用動。
"""
from __future__ import annotations
import os
import time
import pandas as pd
from datetime import date
from src.utils import (
    load_settings, setup_logger, ensure_dirs,
    get_trading_months, is_current_month, PATHS,
)
from src.fetchers import metadata, storage
from src.fetchers import twse as twse_mod
from src.fetchers import tpex as tpex_mod

logger = setup_logger()

# 市場 dispatch 表：每個市場提供 fetch_monthly(sid, year, month, retries) 函式
MARKETS = {
    "twse": twse_mod.fetch_monthly,
    "tpex": tpex_mod.fetch_monthly,
}


def fetch_monthly_data(stock_id: str, year: int, month: int,
                       retries: int = 3) -> pd.DataFrame:
    """依市場別 dispatch；未知市場時自動偵測（TWSE → TPEX）。

    成功時若市場別原本未知 → 自動寫入 stock_market.yaml。
    """
    market = metadata.get_market(stock_id)
    if market in MARKETS:
        return MARKETS[market](stock_id, year, month, retries)

    # market == 'unknown'：依序試所有市場，第一個有資料的記下來
    for name, fn in MARKETS.items():
        df = fn(stock_id, year, month, retries)
        if not df.empty:
            metadata.save_market(stock_id, name)
            logger.info(f"  [{stock_id}] {name.upper()} 成功，已記錄市場別")
            return df
        if name != list(MARKETS.keys())[-1]:
            logger.info(f"  [{stock_id}] {name.upper()} 無資料，嘗試下一個市場...")

    logger.error(f"  [{stock_id}] {year}/{month:02d} 所有市場均無資料，跳過")
    return pd.DataFrame()


def fetch_stock(stock_id: str, start_date: str, end_date: str,
                sleep_seconds: int, max_retries: int):
    """單檔抓取 pipeline：算缺漏月份 → 逐月抓 → 立即寫檔（支援中斷續傳）。"""
    logger.info(f"[{stock_id}] 開始處理...")

    all_months = get_trading_months(start_date, end_date)

    # 依 IPO 記錄跳過上市前月份
    ipo_data = metadata.load_ipo()
    if stock_id in ipo_data:
        ipo_ym = ipo_data[stock_id]              # "YYYY-MM"
        ipo_year, ipo_month = int(ipo_ym[:4]), int(ipo_ym[5:7])
        before = len(all_months)
        all_months = [(y, m) for y, m in all_months
                      if (y, m) >= (ipo_year, ipo_month)]
        skipped = before - len(all_months)
        if skipped:
            logger.info(f"  [{stock_id}] 依 IPO 記錄跳過 {skipped} 個月（{ipo_ym} 之前）")

    missing = storage.get_missing_months(stock_id, all_months)
    if not missing:
        logger.info(f"  [{stock_id}] 所有資料已是最新，跳過")
        return

    market = metadata.get_market(stock_id)
    logger.info(f"  [{stock_id}] 需要下載 {len(missing)} 個月份"
                f"（共 {len(all_months)} 個月）"
                + (f"（{market.upper()}）" if market != "unknown" else ""))

    total_saved = 0
    consecutive_fail = 0
    first_success_ym = None

    for i, (year, month) in enumerate(missing):
        label = f"{year}/{month:02d}"
        current = "（當月）" if is_current_month(year, month) else ""
        logger.info(f"  [{stock_id}] 請求 {label}{current} ({i+1}/{len(missing)})")

        df = fetch_monthly_data(stock_id, year, month, retries=max_retries)
        if not df.empty:
            consecutive_fail = 0
            if first_success_ym is None:
                first_success_ym = (year, month)
            storage.save_raw_data(stock_id, df)
            total_saved += len(df)
            logger.debug(f"  [{stock_id}] {label} 儲存 {len(df)} 筆")
        else:
            consecutive_fail += 1
            logger.warning(f"  [{stock_id}] {label} 無資料（可能為上市前或假日）")
            if consecutive_fail >= 3 and first_success_ym is None:
                logger.info(f"  [{stock_id}] 連續 {consecutive_fail} 個月無資料，"
                            f"疑似上市前，繼續往後找...")

        if i < len(missing) - 1:
            time.sleep(sleep_seconds)

    if total_saved > 0:
        logger.info(f"  [{stock_id}] 本次共新增 {total_saved} 筆資料")
    else:
        logger.warning(f"  [{stock_id}] 本次未取得任何新資料")

    # 寫 IPO 記錄（從 raw CSV 推估 vs 本次第一筆 取較小者）
    ref_year, ref_month = first_success_ym if first_success_ym else (
        date.today().year, date.today().month)
    metadata.save_ipo(stock_id, ref_year, ref_month)


def run_fetcher(stock_ids: list = None):
    """批次抓取。

    - stock_ids=None → 從 stock_list.csv 讀，套 batch_size 限制
    - stock_ids 有值 → 全部處理（使用者明確指定，無 batch 限制）
    """
    settings = load_settings()
    cfg = settings["download"]
    start_date  = cfg["start_date"]
    end_date    = cfg["end_date"]
    batch_size  = cfg["batch_size"]
    sleep_secs  = cfg["sleep_seconds"]
    max_retries = cfg.get("max_retries", 3)

    ensure_dirs()
    explicit = stock_ids is not None

    if not explicit:
        if not os.path.exists(PATHS["stock_list"]):
            logger.error("stock_list.csv 不存在，請先執行 screener")
            return
        df_list = pd.read_csv(PATHS["stock_list"], dtype={"stock_id": str})
        stock_ids = df_list["stock_id"].tolist()

    # 計算 pending
    pending = []
    for sid in stock_ids:
        all_months = get_trading_months(start_date, end_date)
        if storage.get_missing_months(sid, all_months):
            pending.append(sid)

    if not pending:
        logger.info("所有股票資料均已是最新，無需下載")
        return

    to_process = pending if explicit else pending[:batch_size]
    logger.info("=== 資料抓取開始 ===")
    logger.info(f"待下載股票：{len(pending)} 支，本次處理：{len(to_process)} 支"
                + ("" if explicit else f"（batch_size={batch_size}，剩餘下次繼續）"))

    for i, sid in enumerate(to_process):
        fetch_stock(sid, start_date, end_date, sleep_secs, max_retries)
        if i < len(to_process) - 1:
            time.sleep(sleep_secs)

    logger.info("=== 資料抓取完成 ===")
