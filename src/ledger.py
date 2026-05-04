import os
import csv
import yaml
import pandas as pd
from collections import deque
from datetime import date
from src.utils import BASE_DIR, raw_file_path, setup_logger

logger = setup_logger()

DATA_DIR      = os.path.join(BASE_DIR, "data")
SNAPSHOT_PATH = os.path.join(BASE_DIR, "output", "positions_snapshot.csv")

TRADES_COLUMNS = ["date", "stock_id", "action", "price", "shares", "note"]

BUY_FEE_RATE  = 0.001425
SELL_FEE_RATE = 0.001425
SELL_TAX_RATE = 0.003

DEFAULT_ACCOUNT = "Takeshi"


# ── Path helpers ───────────────────────────────────────────────────────────────

def trades_path(account: str = DEFAULT_ACCOUNT) -> str:
    return os.path.join(DATA_DIR, f"trades_{account}.csv")


def queue_path(account: str = DEFAULT_ACCOUNT) -> str:
    return os.path.join(DATA_DIR, f"queue_{account}.yaml")


def snapshot_path(account: str = DEFAULT_ACCOUNT) -> str:
    return os.path.join(BASE_DIR, "output", f"positions_snapshot_{account}.csv")


# ── trades I/O ────────────────────────────────────────────────────────────────

def load_trades(account: str = DEFAULT_ACCOUNT) -> pd.DataFrame:
    path = trades_path(account)
    if not os.path.exists(path):
        return pd.DataFrame(columns=TRADES_COLUMNS)
    lines = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(line)
    if len(lines) <= 1:
        return pd.DataFrame(columns=TRADES_COLUMNS)
    from io import StringIO
    df = pd.read_csv(StringIO("".join(lines)),
                     dtype={"stock_id": str, "action": str, "note": str})
    df["date"]   = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["price"]  = pd.to_numeric(df["price"],  errors="coerce")
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce").fillna(0).astype(int)
    df["note"]   = df["note"].fillna("")
    return df


def append_trade(trade_date: str, stock_id: str, action: str,
                 price: float, shares: int, note: str = "",
                 account: str = DEFAULT_ACCOUNT):
    path = trades_path(account)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(TRADES_COLUMNS)
        writer.writerow([trade_date, stock_id, action.upper(),
                         round(price, 2), shares, note])
    logger.info(f"[trades:{account}] {action.upper()} {stock_id}  "
                f"{trade_date}  {price} × {shares}")


# ── 手續費 / 交易稅 ────────────────────────────────────────────────────────────

def calc_fees(action: str, price: float, shares: int) -> float:
    amount = price * shares
    if action.upper() == "BUY":
        return round(amount * BUY_FEE_RATE)
    else:
        return round(amount * (SELL_FEE_RATE + SELL_TAX_RATE))


# ── FIFO 計算 ──────────────────────────────────────────────────────────────────

def compute_open_positions(trades: pd.DataFrame) -> list[dict]:
    lots: dict[str, deque] = {}
    for _, row in trades.sort_values("date").iterrows():
        sid    = str(row["stock_id"])
        action = str(row["action"]).upper()
        price  = float(row["price"])
        shares = int(row["shares"])
        if action == "BUY":
            lots.setdefault(sid, deque()).append({
                "open_date":  row["date"],
                "open_price": price,
                "shares":     shares,
                "note":       row.get("note", ""),
            })
        elif action == "SELL":
            remaining = shares
            if sid not in lots:
                continue
            while remaining > 0 and lots[sid]:
                lot = lots[sid][0]
                if lot["shares"] <= remaining:
                    remaining -= lot["shares"]
                    lots[sid].popleft()
                else:
                    lot["shares"] -= remaining
                    remaining = 0
            if not lots[sid]:
                del lots[sid]
    return [{"stock_id": sid, **lot}
            for sid, dq in lots.items()
            for lot in dq]


def compute_closed_trades(trades: pd.DataFrame) -> list[dict]:
    lots: dict[str, deque] = {}
    closed = []
    for _, row in trades.sort_values("date").iterrows():
        sid    = str(row["stock_id"])
        action = str(row["action"]).upper()
        price  = float(row["price"])
        shares = int(row["shares"])
        if action == "BUY":
            lots.setdefault(sid, deque()).append({
                "open_date":  row["date"],
                "open_price": price,
                "shares":     shares,
            })
        elif action == "SELL":
            if sid not in lots:
                continue
            remaining      = shares
            total_sell_fee = calc_fees("SELL", price, shares)
            while remaining > 0 and lots[sid]:
                lot     = lots[sid][0]
                matched = min(lot["shares"], remaining)
                ratio   = matched / shares
                buy_fee  = calc_fees("BUY", lot["open_price"], matched)
                sell_fee = round(total_sell_fee * ratio)
                gross    = round((price - lot["open_price"]) * matched)
                net_pnl  = gross - buy_fee - sell_fee
                pnl_pct  = round((price / lot["open_price"] - 1) * 100, 2)
                closed.append({
                    "stock_id":    sid,
                    "open_date":   lot["open_date"],
                    "close_date":  row["date"],
                    "open_price":  lot["open_price"],
                    "close_price": price,
                    "shares":      matched,
                    "gross_pnl":   gross,
                    "fees":        buy_fee + sell_fee,
                    "net_pnl":     net_pnl,
                    "pnl_pct":     pnl_pct,
                })
                if lot["shares"] <= remaining:
                    remaining -= lot["shares"]
                    lots[sid].popleft()
                else:
                    lot["shares"] -= remaining
                    remaining = 0
            if sid in lots and not lots[sid]:
                del lots[sid]
    return closed


# ── 現金與 NAV 計算 ────────────────────────────────────────────────────────────

def compute_available_cash(trades: pd.DataFrame) -> float:
    cash = 0.0
    for _, row in trades.sort_values("date").iterrows():
        action = str(row["action"]).upper()
        price  = float(row["price"])
        shares = int(row["shares"])
        if action == "DEPOSIT":
            cash += price * shares
        elif action == "WITHDRAW":
            cash -= price * shares
        elif action == "BUY":
            cash -= price * shares + calc_fees("BUY", price, shares)
        elif action == "SELL":
            cash += price * shares - calc_fees("SELL", price, shares)
    return cash


def get_account_nav(account: str = DEFAULT_ACCOUNT) -> float:
    """計算帳戶最新 NAV = 可用現金 + 持倉市值（用最新收盤價）"""
    trades   = load_trades(account)
    cash     = compute_available_cash(trades)
    open_pos = compute_open_positions(trades)
    nav      = cash
    for pos in open_pos:
        price = latest_close(pos["stock_id"])
        nav  += pos["shares"] * (price if price else pos["open_price"])
    return round(nav, 2)


# ── 最新收盤價 ────────────────────────────────────────────────────────────────

def latest_close(stock_id: str) -> float | None:
    path = raw_file_path(stock_id)
    if not os.path.exists(path):
        return None
    try:
        df    = pd.read_csv(path, dtype=str)
        df["date"] = pd.to_datetime(df["date"])
        close = pd.to_numeric(df.sort_values("date")["close"].iloc[-1], errors="coerce")
        return float(close) if pd.notna(close) else None
    except Exception:
        return None


# ── 持倉快照 CSV ──────────────────────────────────────────────────────────────

def save_snapshot(open_positions: list[dict], account: str = DEFAULT_ACCOUNT):
    path = snapshot_path(account)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = []
    for p in open_positions:
        cur = latest_close(p["stock_id"])
        if cur is not None:
            unreal = round((cur - p["open_price"]) * p["shares"])
            pct    = round((cur / p["open_price"] - 1) * 100, 2)
        else:
            unreal = pct = None
        rows.append({
            "stock_id":       p["stock_id"],
            "open_date":      p["open_date"],
            "open_price":     p["open_price"],
            "shares":         p["shares"],
            "current_price":  cur,
            "unrealized_pnl": unreal,
            "pnl_pct":        pct,
            "note":           p.get("note", ""),
        })
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"快照已更新：{path}")


# ── queue.yaml I/O ────────────────────────────────────────────────────────────

def load_queue(account: str = DEFAULT_ACCOUNT) -> list:
    path = queue_path(account)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("queue", [])


def save_queue(queue: list, account: str = DEFAULT_ACCOUNT):
    path = queue_path(account)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({"queue": queue}, f,
                  allow_unicode=True, default_flow_style=False, sort_keys=False)
