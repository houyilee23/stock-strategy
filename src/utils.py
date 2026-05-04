import os
import csv
import logging
import yaml
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATHS = {
    "config":     os.path.join(BASE_DIR, "config", "settings.yaml"),
    "raw":        os.path.join(BASE_DIR, "data", "raw"),
    "logs":       os.path.join(BASE_DIR, "logs"),
    "stock_list": os.path.join(BASE_DIR, "data", "stock_list.csv"),
}


def load_settings():
    with open(PATHS["config"], "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logger(name="stock"):
    today = date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(PATHS["logs"], f"{today}.log")
    os.makedirs(PATHS["logs"], exist_ok=True)

    settings = load_settings()
    level = getattr(logging, settings["output"]["log_level"], logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


def ensure_dirs():
    for key in ("raw", "logs"):
        os.makedirs(PATHS[key], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)


def get_trading_months(start_date: str, end_date: str) -> list:
    """回傳 start_date 到 end_date 之間所有年月的清單，格式 (year, month)"""
    if end_date == "today":
        end = date.today()
    else:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    start = start.replace(day=1)
    end = end.replace(day=1)

    months = []
    cur = start
    while cur <= end:
        months.append((cur.year, cur.month))
        cur += relativedelta(months=1)
    return months


def is_current_month(year: int, month: int) -> bool:
    today = date.today()
    return year == today.year and month == today.month


def raw_file_path(stock_id: str) -> str:
    return os.path.join(PATHS["raw"], f"{stock_id}.csv")


def log_error(module: str, stock_id: str, reason: str):
    """將執行錯誤記錄到 output/errors/YYYY-MM-DD.csv，供事後批次處理"""
    today    = date.today().strftime("%Y-%m-%d")
    err_dir  = os.path.join(BASE_DIR, "output", "errors")
    err_path = os.path.join(err_dir, f"{today}.csv")
    os.makedirs(err_dir, exist_ok=True)

    now       = datetime.now().strftime("%H:%M:%S")
    is_new    = not os.path.exists(err_path)
    with open(err_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "module", "stock_id", "reason"])
        if is_new:
            writer.writeheader()
        writer.writerow({"time": now, "module": module, "stock_id": stock_id, "reason": reason})

    # 同時輸出到 console
    print(f"  [跳過] {stock_id} ── {reason}（已記錄至 {err_path}）")
