import requests
import pandas as pd
import time
from src.utils import load_settings, setup_logger, PATHS

logger = setup_logger()

TWSE_STOCK_LIST_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TWSE_COMPANY_URL = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"


def fetch_twse_stock_list() -> pd.DataFrame:
    """從 TWSE OpenAPI 抓取全部上市股票清單"""
    logger.info("抓取 TWSE 上市股票清單...")
    try:
        resp = requests.get(TWSE_STOCK_LIST_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data)
        logger.info(f"取得 {len(df)} 筆股票資料")
        return df
    except Exception as e:
        logger.error(f"抓取股票清單失敗：{e}")
        return pd.DataFrame()


def fetch_twse_pe_list() -> pd.DataFrame:
    """從 TWSE 抓取本益比/殖利率資料（含市值參考）"""
    try:
        resp = requests.get(TWSE_COMPANY_URL, timeout=30)
        resp.raise_for_status()
        return pd.DataFrame(resp.json())
    except Exception as e:
        logger.warning(f"抓取本益比資料失敗：{e}")
        return pd.DataFrame()


def apply_filters(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """套用篩選條件"""
    auto_cfg = config.get("auto", {})

    # 排除 ETF（名稱含"ETF"或代號開頭為00者）
    if auto_cfg.get("exclude_etf", True):
        df = df[~df["Code"].str.startswith("00")]
        if "Name" in df.columns:
            df = df[~df["Name"].str.contains("ETF|基金", case=False, na=False)]

    # 只保留純數字4位代號（排除特殊股）
    df = df[df["Code"].str.match(r"^\d{4}$")]

    # 成交量篩選
    min_vol = auto_cfg.get("min_avg_volume_thousand", 0)
    if "TradeVolume" in df.columns and min_vol > 0:
        df = df.copy()
        df["TradeVolume"] = pd.to_numeric(df["TradeVolume"].str.replace(",", ""), errors="coerce")
        df = df[df["TradeVolume"] >= min_vol * 1000]

    df = df.reset_index(drop=True)
    limit = auto_cfg.get("limit", 20)
    return df.head(limit)


def build_stock_list(config: dict) -> pd.DataFrame:
    """依 mode 建立最終股票清單"""
    mode = config.get("mode", "manual")
    manual_add = config.get("manual_add", [])
    manual_exclude = [str(s) for s in config.get("manual_exclude", [])]

    rows = []

    if mode in ("auto", "mixed"):
        raw_df = fetch_twse_stock_list()
        time.sleep(2)
        if not raw_df.empty:
            filtered = apply_filters(raw_df, config)
            for _, row in filtered.iterrows():
                code = str(row.get("Code", "")).strip()
                name = str(row.get("Name", "")).strip()
                if code and code not in manual_exclude:
                    rows.append({"stock_id": code, "name": name, "added_by": "auto"})

    if mode in ("manual", "mixed"):
        existing_ids = {r["stock_id"] for r in rows}
        for code in manual_add:
            code = str(code).strip()
            if code not in manual_exclude and code not in existing_ids:
                rows.append({"stock_id": code, "name": "", "added_by": "manual"})

    df = pd.DataFrame(rows, columns=["stock_id", "name", "added_by"])
    df = df[~df["stock_id"].isin(manual_exclude)]
    return df.drop_duplicates(subset="stock_id").reset_index(drop=True)


def run_screener():
    settings = load_settings()
    config = settings["screener"]

    logger.info("=== 股票篩選開始 ===")
    df = build_stock_list(config)

    if df.empty:
        logger.error("篩選結果為空，請檢查 settings.yaml")
        return df

    df.to_csv(PATHS["stock_list"], index=False, encoding="utf-8-sig")
    logger.info(f"股票清單已儲存：{PATHS['stock_list']}（共 {len(df)} 支）")
    logger.info(f"清單：{df['stock_id'].tolist()}")
    return df


if __name__ == "__main__":
    run_screener()
