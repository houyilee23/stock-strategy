"""TWSE / TPEX 股價抓取（模組化版本）。

模組結構（每個 < 150 行，方便維護）：
  - metadata.py    IPO + 市場別 YAML 管理
  - twse.py        TWSE 上市單月抓取（單一職責）
  - tpex.py        TPEX 上櫃單月抓取（單一職責）
  - storage.py     raw CSV 合併寫入 + 缺漏月份計算
  - coordinator.py dispatch + auto-detect + batch pipeline

加新市場（例：興櫃）只需新增 src/fetchers/emerging.py + coordinator.MARKETS 加一行。
其他模組完全不用動 → 符合「token-efficient 維護」目標。

對外公開 API（原 src/fetcher.py 都有）：
  fetch_stock(sid, start, end, sleep, retries)   — 單檔
  run_fetcher(stock_ids=None)                   — 批次（main.py 用）
  fetch_monthly_data(sid, year, month, retries) — 單月（測試用）
  save_raw_data(sid, df)                        — 直接寫檔
"""
from src.fetchers.coordinator import (
    fetch_stock, run_fetcher, fetch_monthly_data, MARKETS,
)
from src.fetchers.storage import (
    save_raw_data, get_missing_months, get_existing_date_range,
)
from src.fetchers.metadata import (
    load_ipo, save_ipo, load_market, save_market, get_market,
    IPO_PATH, MARKET_PATH,
)
from src.fetchers import twse as _twse
from src.fetchers import tpex as _tpex

# 個別市場的單月抓取（測試 / debug 用）
fetch_monthly_data_twse = _twse.fetch_monthly
fetch_monthly_data_tpex = _tpex.fetch_monthly

__all__ = [
    # 主要 API
    "fetch_stock", "run_fetcher", "fetch_monthly_data",
    # 儲存
    "save_raw_data", "get_missing_months", "get_existing_date_range",
    # metadata
    "load_ipo", "save_ipo", "load_market", "save_market", "get_market",
    "IPO_PATH", "MARKET_PATH",
    # 個別市場（debug）
    "fetch_monthly_data_twse", "fetch_monthly_data_tpex",
    "MARKETS",
]
