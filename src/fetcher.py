import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pandas as pd
import yaml
import time
import os
from datetime import date
from src.utils import (
    load_settings, setup_logger, ensure_dirs,
    get_trading_months, is_current_month,
    raw_file_path, PATHS
)

logger = setup_logger()

TWSE_HISTORY_URL  = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
TPEX_HISTORY_URL  = "https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php"

BASE_CFG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IPO_PATH    = os.path.join(BASE_CFG, "config", "stock_ipo.yaml")
MARKET_PATH = os.path.join(BASE_CFG, "config", "stock_market.yaml")

COLUMNS = ["date", "open", "high", "low", "close", "volume", "turnover", "transactions", "price_change"]


# ── IPO 日期管理 ──────────────────────────────────────────────

def _load_ipo() -> dict:
    if not os.path.exists(IPO_PATH):
        return {}
    with open(IPO_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in data.items() if not str(k).startswith("#")}


def _earliest_from_raw(stock_id: str) -> str | None:
    """讀取本地 raw CSV，回傳最早日期的 YYYY-MM，找不到回傳 None"""
    path = raw_file_path(stock_id)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype={"date": str}, usecols=["date"])
        if df.empty:
            return None
        earliest = df["date"].dropna().min()   # 格式 YYYYMMDD
        if len(earliest) == 8:
            return f"{earliest[:4]}-{earliest[4:6]}"
    except Exception:
        pass
    return None


def _save_ipo(stock_id: str, year: int, month: int):
    """
    記錄股票最早可下載的月份。

    優先順序：
      1. raw CSV 最早日期（最可靠，實際有資料的最早月份）
      2. 本次 fetch 的第一次成功月份（raw CSV 不存在時使用）

    注意：raw CSV 的值可能比現有 yaml 記錄「更晚」（例如手動填了錯誤的早期日期），
    此時仍以 raw CSV 為準更新，因為那才是真正有資料的起點。
    """
    raw_earliest = _earliest_from_raw(stock_id)

    if raw_earliest:
        # raw CSV 是最可靠的依據，直接使用
        final = raw_earliest
    else:
        # 沒有本地 raw 資料，用本次 fetch 的第一次成功月份
        final = f"{year}-{month:02d}"

    ipo_data = _load_ipo()
    existing = ipo_data.get(str(stock_id))

    if existing == final:
        return  # 無需更新

    ipo_data[str(stock_id)] = final
    # 全部正規化成字串 key，避免 0050 被 YAML 當八進位轉成 40
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
    # key 一律加引號，避免 "0050" 被 YAML 當八進位 40 / "0xxxx" 出問題
    lines = "".join(f'"{k}": "{v}"\n' for k, v in sorted(ipo_data.items()))
    with open(IPO_PATH, "w", encoding="utf-8") as f:
        f.write(header + lines)

    if existing:
        logger.info(f"  [{stock_id}] IPO 記錄更新：{existing} → {final}")
    else:
        logger.info(f"  [{stock_id}] IPO 記錄寫入：{final}")


# ── 市場別管理（TWSE / TPEX）─────────────────────────────────

def _load_market() -> dict:
    if not os.path.exists(MARKET_PATH):
        return {}
    with open(MARKET_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in data.items() if not str(k).startswith("#")}


def _save_market(stock_id: str, market: str):
    """記錄股票的市場別"""
    data = _load_market()
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
    lines = "".join(f"{k}: {v}\n" for k, v in sorted(data.items()))
    with open(MARKET_PATH, "w", encoding="utf-8") as f:
        f.write(header + lines)
    logger.info(f"  [{stock_id}] 市場別已記錄：{market}")


def _get_market(stock_id: str) -> str:
    """取得市場別，未知時回傳 'unknown'"""
    return _load_market().get(str(stock_id), "unknown")


# ── TPEX 資料抓取 ─────────────────────────────────────────────

def fetch_monthly_data_tpex(stock_id: str, year: int, month: int, retries: int = 3) -> pd.DataFrame:
    """
    抓取 TPEX 上櫃股票單月日線資料。
    使用 TPEX 傳統 Web API（st43），一次請求回傳整個月份的所有交易日資料。

    端點：https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php
    參數：l=zh-tw, d=YYYY/MM, s=0,asc,0, o=json, id=股票代號
    回傳欄位（aaData 陣列）：
      [0] 日期（民國年 YYY/MM/DD）
      [1] 成交股數
      [2] 成交金額
      [3] 開盤價
      [4] 最高價
      [5] 最低價
      [6] 收盤價
      [7] 漲跌
      [8] 成交筆數
    """
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
            resp = requests.get(TPEX_HISTORY_URL, params=params, timeout=30, verify=False)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            logger.warning(f"  [{stock_id}] TPEX {year}/{month:02d} 第{attempt}次失敗：{e}")
            if attempt < retries:
                time.sleep(5)

    if not data:
        return pd.DataFrame()

    aa_data = data.get("aaData", [])
    if not aa_data:
        return pd.DataFrame()

    def _clean(v):
        """移除千位逗號，無效值回傳 None"""
        s = str(v).replace(",", "").strip()
        return s if s not in ("", "--", "---", "N/A") else None

    def _to_float(v):
        s = _clean(v)
        try:
            return float(s) if s else None
        except ValueError:
            return None

    def _to_int(v):
        s = _clean(v)
        try:
            return int(s) if s else 0
        except ValueError:
            return 0

    rows = []
    for r in aa_data:
        if len(r) < 9:
            continue
        try:
            # 日期格式：民國年 "YYY/MM/DD"（例如 "113/04/01"）
            date_raw = str(r[0]).strip()
            parts = date_raw.split("/")
            if len(parts) == 3:
                ad_year = int(parts[0]) + 1911
                ad_date = f"{ad_year}{int(parts[1]):02d}{int(parts[2]):02d}"
            else:
                # 格式異常，跳過
                continue

            c = _to_float(r[6])
            if c is None:
                continue  # 無收盤價，跳過（停牌等）

            rows.append({
                "date":         ad_date,
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


def _parse_twse_response(data: dict, stock_id: str, year: int, month: int) -> pd.DataFrame:
    """解析 TWSE 回傳的 JSON 資料"""
    if not data or data.get("stat") != "OK":
        return pd.DataFrame()

    raw_rows = data.get("data", [])
    if not raw_rows:
        return pd.DataFrame()

    rows = []
    for r in raw_rows:
        try:
            # TWSE 日期格式為民國年，例如 "114/04/01"
            date_str = r[0].strip()
            parts = date_str.split("/")
            ad_year = int(parts[0]) + 1911
            date_formatted = f"{ad_year}{int(parts[1]):02d}{int(parts[2]):02d}"

            rows.append({
                "date":         date_formatted,
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


def fetch_monthly_data_twse(stock_id: str, year: int, month: int, retries: int = 3) -> pd.DataFrame:
    """請求 TWSE 單月歷史資料"""
    for day in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        date_param = f"{year}{month:02d}{day:02d}"
        params = {"response": "json", "date": date_param, "stockNo": stock_id}
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(TWSE_HISTORY_URL, params=params, timeout=30, verify=False)
                resp.raise_for_status()
                data = resp.json()
                df = _parse_twse_response(data, stock_id, year, month)
                if not df.empty:
                    return df
                break
            except Exception as e:
                logger.warning(f"  [{stock_id}] {year}/{month:02d}/{day:02d} 第{attempt}次失敗：{e}")
                if attempt < retries:
                    time.sleep(5)
    return pd.DataFrame()


def fetch_monthly_data(stock_id: str, year: int, month: int, retries: int = 3) -> pd.DataFrame:
    """
    自動判斷市場別，路由到對應的抓取函式。
    - 已知 twse → 直接用 TWSE
    - 已知 tpex → 直接用 TPEX
    - 未知 → 先試 TWSE，無資料再試 TPEX，並記錄結果
    """
    market = _get_market(stock_id)

    if market == "tpex":
        return fetch_monthly_data_tpex(stock_id, year, month, retries)

    # twse 或 unknown：先試 TWSE
    df = fetch_monthly_data_twse(stock_id, year, month, retries)
    if not df.empty:
        if market == "unknown":
            _save_market(stock_id, "twse")
        return df

    if market == "twse":
        # 已確認是 TWSE，失敗就是真的沒資料（IPO 前）
        logger.error(f"  [{stock_id}] {year}/{month:02d} TWSE 無資料，跳過")
        return pd.DataFrame()

    # market == "unknown"，TWSE 無資料 → 嘗試 TPEX
    logger.info(f"  [{stock_id}] TWSE 無資料，嘗試 TPEX...")
    df = fetch_monthly_data_tpex(stock_id, year, month, retries)
    if not df.empty:
        _save_market(stock_id, "tpex")
        logger.info(f"  [{stock_id}] TPEX 成功，已記錄為上櫃股票")
        return df

    logger.error(f"  [{stock_id}] {year}/{month:02d} TWSE 與 TPEX 均無資料，跳過")
    return pd.DataFrame()


def get_existing_date_range(stock_id: str):
    """讀取本地 raw 檔案中已有的日期範圍，回傳 (min_date_str, max_date_str) 或 None"""
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
    """
    比對 all_months 與本地已有資料，回傳需要請求的月份清單。
    當月永遠列入（資料每日更新）。
    本地最後一筆所在的月份也列入（補抓 tail-end，例如上次 fetch 後該月仍有交易日）。
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

    # 本地最大日期所在月份（例如最後一筆 20260424 → tail_ym=(2026,4)）
    max_date = max(existing_dates) if existing_dates else None
    tail_ym = (int(max_date[:4]), int(max_date[4:6])) if max_date and len(max_date) == 8 else None

    missing = []
    for year, month in all_months:
        if is_current_month(year, month):
            missing.append((year, month))
            continue
        if tail_ym == (year, month):
            # 本地最後一筆在這個月 → 重抓以補後段交易日
            missing.append((year, month))
            continue
        # 檢查該月是否有任何一天的資料存在
        prefix = f"{year}{month:02d}"
        has_data = any(d.startswith(prefix) for d in existing_dates)
        if not has_data:
            missing.append((year, month))

    return missing


def save_raw_data(stock_id: str, new_df: pd.DataFrame):
    """將新資料合併寫入 raw CSV（去除重複、依日期排序）"""
    path = raw_file_path(stock_id)

    if os.path.exists(path):
        try:
            existing = pd.read_csv(path, dtype={"date": str})
            combined = pd.concat([existing, new_df], ignore_index=True)
        except Exception:
            combined = new_df
    else:
        combined = new_df

    combined = combined.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    combined.to_csv(path, index=False, encoding="utf-8-sig")


def fetch_stock(stock_id: str, start_date: str, end_date: str, sleep_seconds: int, max_retries: int):
    """下載單支股票的歷史資料（含快取判斷與 IPO 過濾）"""
    logger.info(f"[{stock_id}] 開始處理...")

    all_months = get_trading_months(start_date, end_date)

    # 若已知 IPO 月份，跳過上市前的月份
    ipo_data = _load_ipo()
    if stock_id in ipo_data:
        ipo_ym = ipo_data[stock_id]          # 格式 "YYYY-MM"
        ipo_year, ipo_month = int(ipo_ym[:4]), int(ipo_ym[5:7])
        before = len(all_months)
        all_months = [(y, m) for y, m in all_months
                      if (y, m) >= (ipo_year, ipo_month)]
        skipped = before - len(all_months)
        if skipped:
            logger.info(f"  [{stock_id}] 依 IPO 記錄跳過 {skipped} 個月（{ipo_ym} 之前）")

    missing = get_missing_months(stock_id, all_months)

    if not missing:
        logger.info(f"  [{stock_id}] 所有資料已是最新，跳過")
        return

    market = _get_market(stock_id)
    # TPEX 每月需要逐日請求，耗時較長，改為逐月儲存以支援中斷續傳
    # TWSE 每月一次請求，也改為逐月儲存，行為一致
    save_per_month = True

    logger.info(f"  [{stock_id}] 需要下載 {len(missing)} 個月份（共 {len(all_months)} 個月）"
                + (f"（{market.upper()}）" if market != "unknown" else ""))

    total_saved    = 0
    consecutive_fail = 0
    first_success_ym = None

    for i, (year, month) in enumerate(missing):
        label   = f"{year}/{month:02d}"
        current = "（當月）" if is_current_month(year, month) else ""
        logger.info(f"  [{stock_id}] 請求 {label}{current} ({i+1}/{len(missing)})")

        df = fetch_monthly_data(stock_id, year, month, retries=max_retries)
        if not df.empty:
            consecutive_fail = 0
            if first_success_ym is None:
                first_success_ym = (year, month)
            if save_per_month:
                # 立即寫入，支援中斷後續傳
                save_raw_data(stock_id, df)
                total_saved += len(df)
                logger.debug(f"  [{stock_id}] {label} 儲存 {len(df)} 筆")
        else:
            consecutive_fail += 1
            logger.warning(f"  [{stock_id}] {label} 無資料（可能為上市前或假日）")
            if consecutive_fail >= 3 and first_success_ym is None:
                logger.info(f"  [{stock_id}] 連續 {consecutive_fail} 個月無資料，疑似上市前，繼續往後找...")

        if i < len(missing) - 1:
            time.sleep(sleep_seconds)

    if total_saved > 0:
        logger.info(f"  [{stock_id}] 本次共新增 {total_saved} 筆資料")
    else:
        logger.warning(f"  [{stock_id}] 本次未取得任何新資料")

    # 每次 fetch 結束後都更新 IPO 記錄：
    # _save_ipo 內部會讀取 raw CSV 取最早日期，與本次 first_success_ym 比較取最小值
    # 這樣即使本次只抓當月（快取跳過歷史），raw CSV 裡的歷史資料仍能修正記錄
    ref_year, ref_month = first_success_ym if first_success_ym else (
        date.today().year, date.today().month)
    _save_ipo(stock_id, ref_year, ref_month)


def run_fetcher(stock_ids: list = None):
    """
    執行資料抓取。
    - stock_ids 為 None → 從 stock_list.csv 讀取，套用 batch_size 限制
    - stock_ids 有指定  → 全部處理，忽略 batch_size（使用者明確指定）
    """
    settings = load_settings()
    cfg = settings["download"]

    start_date  = cfg["start_date"]
    end_date    = cfg["end_date"]
    batch_size  = cfg["batch_size"]
    sleep_secs  = cfg["sleep_seconds"]
    max_retries = cfg.get("max_retries", 3)

    ensure_dirs()

    # 使用者有明確指定股票 → 全部處理，不受 batch_size 限制
    explicit = stock_ids is not None

    if not explicit:
        if not os.path.exists(PATHS["stock_list"]):
            logger.error("stock_list.csv 不存在，請先執行 screener")
            return
        df_list = pd.read_csv(PATHS["stock_list"], dtype={"stock_id": str})
        stock_ids = df_list["stock_id"].tolist()

    # 找出尚未完整下載的股票
    pending = []
    for sid in stock_ids:
        all_months = get_trading_months(start_date, end_date)
        missing = get_missing_months(sid, all_months)
        if missing:
            pending.append(sid)

    if not pending:
        logger.info("所有股票資料均已是最新，無需下載")
        return

    # 明確指定時全部跑，否則套用 batch_size
    to_process = pending if explicit else pending[:batch_size]
    logger.info(f"=== 資料抓取開始 ===")
    logger.info(f"待下載股票：{len(pending)} 支，本次處理：{len(to_process)} 支"
                + ("" if explicit else f"（batch_size={batch_size}，剩餘下次繼續）"))

    for i, stock_id in enumerate(to_process):
        fetch_stock(stock_id, start_date, end_date, sleep_secs, max_retries)
        if i < len(to_process) - 1:
            time.sleep(sleep_secs)

    logger.info("=== 資料抓取完成 ===")


if __name__ == "__main__":
    run_fetcher()
