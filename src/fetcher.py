"""DEPRECATED：本檔保留只為 backward compat。

新程式請從 `src.fetchers` 匯入。本檔是 thin shim，把全部 symbols re-export。

模組化新位置：
  - src/fetchers/twse.py        TWSE 抓取
  - src/fetchers/tpex.py        TPEX 抓取
  - src/fetchers/metadata.py    IPO + 市場別管理
  - src/fetchers/storage.py     raw CSV 寫入 / 缺漏月份
  - src/fetchers/coordinator.py dispatch + pipeline

加新市場時請動 src/fetchers/，本檔不需改動。
"""
from src.fetchers import (
    # 主要 API（main.py 用）
    fetch_stock, run_fetcher, fetch_monthly_data,
    # 儲存
    save_raw_data, get_missing_months, get_existing_date_range,
    # 個別市場單月（debug / tests）
    fetch_monthly_data_twse, fetch_monthly_data_tpex,
    # metadata path 常數（部分舊腳本用）
    IPO_PATH, MARKET_PATH,
)

# 私名稱（底線開頭）保持原樣 re-export，相容舊呼叫
from src.fetchers.metadata import (
    load_ipo as _load_ipo,
    save_ipo as _save_ipo,
    load_market as _load_market,
    save_market as _save_market,
    get_market as _get_market,
)

if __name__ == "__main__":
    run_fetcher()
