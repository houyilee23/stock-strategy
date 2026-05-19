"""個股 metadata 管理：IPO 月份 + 市場別（TWSE/TPEX）。

兩份 YAML 都是「程式自動維護 + 使用者可手動編輯」的設定檔：
  - config/stock_ipo.yaml     最早可下載月份（fetch 時跳過上市前）
  - config/stock_market.yaml  市場別（避免每次都 fallback 試 TWSE→TPEX）

設計理念：把這些「需要持久化記住的狀態」抽出來，跟抓取邏輯解耦，方便
測試與替換（例如未來改用 SQLite）。
"""
from __future__ import annotations
import os
import yaml
import pandas as pd

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IPO_PATH    = os.path.join(BASE_DIR, "config", "stock_ipo.yaml")
MARKET_PATH = os.path.join(BASE_DIR, "config", "stock_market.yaml")


# ── IPO 月份 ─────────────────────────────────────────────────

def load_ipo() -> dict:
    """回傳 {sid: "YYYY-MM"}，找不到檔案回傳 {}。"""
    if not os.path.exists(IPO_PATH):
        return {}
    with open(IPO_PATH, "r", encoding="utf-8") as f:
        return {str(k): str(v) for k, v in (yaml.safe_load(f) or {}).items()
                if not str(k).startswith("#")}


def _earliest_from_raw(stock_id: str) -> str | None:
    """從本地 raw CSV 推算最早月份 "YYYY-MM"，無資料回 None。"""
    from src.utils import raw_file_path
    path = raw_file_path(stock_id)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype={"date": str})
        if df.empty or "date" not in df.columns:
            return None
        d = df["date"].min()
        if not isinstance(d, str) or len(d) < 6:
            return None
        return f"{d[:4]}-{d[4:6]}"
    except Exception:
        return None


def save_ipo(stock_id: str, year: int, month: int):
    """記錄 IPO 月份；以 raw CSV 已有最早日期與本次值取較小者。"""
    final = f"{year:04d}-{month:02d}"
    earliest = _earliest_from_raw(stock_id)
    if earliest and earliest < final:
        final = earliest

    ipo_data = load_ipo()
    existing = ipo_data.get(str(stock_id))
    if existing == final:
        return

    ipo_data[str(stock_id)] = final
    ipo_data = {str(k): str(v) for k, v in ipo_data.items()}
    header = (
        "# ============================================================\n"
        "# 個股最早可下載資料的月份\n"
        "# 格式：股票代號: \"YYYY-MM\"\n"
        "#\n"
        "# 此檔案由程式自動維護（首次成功下載時寫入），也可手動修改。\n"
        "# 作用：fetch 時自動跳過上市前的月份，避免無效請求。\n"
        "# ============================================================\n\n"
    )
    lines = "".join(f'"{k}": "{v}"\n' for k, v in sorted(ipo_data.items()))
    with open(IPO_PATH, "w", encoding="utf-8") as f:
        f.write(header + lines)


# ── 市場別 (TWSE / TPEX) ────────────────────────────────────

def load_market() -> dict:
    """回傳 {sid: 'twse'|'tpex'}。"""
    if not os.path.exists(MARKET_PATH):
        return {}
    with open(MARKET_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in data.items() if not str(k).startswith("#")}


def save_market(stock_id: str, market: str):
    """記錄股票的市場別（twse / tpex）。"""
    data = load_market()
    if data.get(str(stock_id)) == market:
        return
    data[str(stock_id)] = market
    header = (
        "# ============================================================\n"
        "# 個股市場別設定\n"
        "# twse = 上市（台灣證券交易所）\n"
        "# tpex = 上櫃（櫃檯買賣中心）\n"
        "# 程式自動偵測並寫入，也可手動設定。\n"
        "# ============================================================\n\n"
    )
    lines = "".join(f'{k}: {v}\n' for k, v in sorted(data.items()))
    with open(MARKET_PATH, "w", encoding="utf-8") as f:
        f.write(header + lines)


def get_market(stock_id: str) -> str:
    """回傳 'twse' / 'tpex' / 'unknown'。"""
    return load_market().get(str(stock_id), "unknown")
