import unicodedata
from datetime import date
from src.utils import setup_logger
from src.ledger import (
    load_trades, append_trade, compute_open_positions, compute_closed_trades,
    latest_close, save_snapshot, compute_available_cash, calc_fees,
    DEFAULT_ACCOUNT,
)

logger = setup_logger()


def _w(s: str, width: int) -> str:
    dw = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in str(s))
    return " " * max(0, width - dw) + str(s)


def _dw(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in str(s))


# ── 開倉 ──────────────────────────────────────────────────────────────────────

def open_position(stock_id: str, price: float, shares: int,
                  trade_date: str | None = None, note: str = "",
                  account: str = DEFAULT_ACCOUNT) -> dict:
    entry_date = trade_date or date.today().strftime("%Y-%m-%d")
    append_trade(entry_date, stock_id, "BUY", price, shares, note=note, account=account)
    cost = price * shares
    logger.info(f"[{account}][開倉] {stock_id}  {entry_date}  成本≈{cost:,.0f}")
    return {"stock_id": stock_id, "open_date": entry_date,
            "open_price": price, "shares": shares}


# ── 平倉 ──────────────────────────────────────────────────────────────────────

def close_position(stock_id: str, price: float | None = None,
                   shares: int | None = None, trade_date: str | None = None,
                   account: str = DEFAULT_ACCOUNT) -> bool:
    trades   = load_trades(account)
    open_pos = compute_open_positions(trades)
    pos_list = [p for p in open_pos if p["stock_id"] == stock_id]

    if not pos_list:
        logger.error(f"[{account}] 找不到 {stock_id} 的未平倉部位")
        return False

    if price is None:
        price = latest_close(stock_id)
        if price is None:
            logger.error(f"無法取得 {stock_id} 最新收盤價，請手動指定價格")
            return False
        logger.info(f"  使用最新收盤價：{price}")

    total_open   = sum(p["shares"] for p in pos_list)
    close_shares = shares or total_open
    if close_shares > total_open:
        logger.error(f"平倉股數 {close_shares} 超過持倉 {total_open}，取消")
        return False

    exit_date = trade_date or date.today().strftime("%Y-%m-%d")
    avg_cost  = sum(p["open_price"] * p["shares"] for p in pos_list) / total_open
    pnl       = round((price - avg_cost) * close_shares)
    pnl_pct   = round((price / avg_cost - 1) * 100, 2)

    append_trade(exit_date, stock_id, "SELL", price, close_shares,
                 note="手動平倉", account=account)
    logger.info(f"[{account}][平倉] {stock_id}  {exit_date}  損益≈{pnl:+,} ({pnl_pct:+.2f}%)")
    return True


# ── 列出持倉 ──────────────────────────────────────────────────────────────────

def list_positions(account: str = DEFAULT_ACCOUNT):
    trades   = load_trades(account)
    open_pos = compute_open_positions(trades)

    print(f"\n=== 目前持倉 [{account}] ===")
    if not open_pos:
        print("  （無持倉）")
        save_snapshot([], account=account)
        return

    hdr = (f"{_w('代號',6)}  {_w('開倉日',10)}  {_w('成本',8)}  {_w('股數',6)}  "
           f"{_w('現價',8)}  {_w('未實現損益',12)}  {_w('損益%',7)}  備註")
    print(hdr)
    print("-" * _dw(hdr))

    total_pnl = 0
    for p in sorted(open_pos, key=lambda x: x["open_date"]):
        cur = latest_close(p["stock_id"])
        if cur is not None:
            buy_fee  = calc_fees("BUY",  p["open_price"], p["shares"])
            sell_fee = calc_fees("SELL", cur,              p["shares"])
            gross    = round((cur - p["open_price"]) * p["shares"])
            pnl      = gross - buy_fee - sell_fee
            pct      = pnl / (p["open_price"] * p["shares"]) * 100
            cur_str  = f"{cur:.2f}"
            pnl_str  = f"{pnl:+,}"
            pct_str  = f"{pct:+.2f}%"
            total_pnl += pnl
        else:
            cur_str = pnl_str = pct_str = "N/A"
        print(f"{p['stock_id']:>6}  {p['open_date']:>10}  {p['open_price']:>8.2f}  "
              f"{p['shares']:>6}  {cur_str:>8}  {pnl_str:>12}  {pct_str:>7}  "
              f"{p.get('note', '')}")

    mkt_value = sum(
        (latest_close(p["stock_id"]) or p["open_price"]) * p["shares"]
        for p in open_pos
    )
    cash      = compute_available_cash(trades)
    total_nav = mkt_value + cash

    print(f"\n  未實現損益：{total_pnl:+,} 元")
    print(f"  ────────────────────────────────")
    print(f"  持倉市值  ：NT${mkt_value:>12,.0f}")
    print(f"  可用現金  ：NT${cash:>12,.0f}")
    print(f"  總資產    ：NT${total_nav:>12,.0f}")
    save_snapshot(open_pos, account=account)
    print(f"  快照已存：output/positions_snapshot_{account}.csv")


# ── 歷史損益 ──────────────────────────────────────────────────────────────────

def list_history(account: str = DEFAULT_ACCOUNT):
    trades = load_trades(account)
    closed = compute_closed_trades(trades)

    print(f"\n=== 歷史已實現損益 [{account}] ===")
    if not closed:
        print("  （無已平倉記錄）")
        return

    hdr = (f"{_w('代號',6)}  {_w('開倉日',10)}  {_w('平倉日',10)}  {_w('買價',8)}  "
           f"{_w('賣價',8)}  {_w('股數',6)}  {_w('毛損益',10)}  {_w('手續費+稅',9)}  "
           f"{_w('淨損益',10)}  {_w('損益%',7)}")
    print(hdr)
    print("-" * _dw(hdr))

    total_net = 0
    for r in closed:
        print(f"{r['stock_id']:>6}  {r['open_date']:>10}  {r['close_date']:>10}  "
              f"{r['open_price']:>8.2f}  {r['close_price']:>8.2f}  {r['shares']:>6}  "
              f"{r['gross_pnl']:>+10,}  {r['fees']:>9,}  "
              f"{r['net_pnl']:>+10,}  {r['pnl_pct']:>+7.2f}%")
        total_net += r["net_pnl"]

    print(f"\n  合計已實現淨損益：{total_net:+,} 元")


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

def run_positions(sub: str, args: list):
    args    = list(args)
    account = _pop_flag(args, "--account") or DEFAULT_ACCOUNT

    if sub == "list":
        list_positions(account=account)

    elif sub == "history":
        list_history(account=account)

    elif sub == "open":
        if len(args) < 3:
            print("用法：positions open <代號> <開倉價> <股數> [--account 帳戶] [--date YYYY-MM-DD]")
            return
        stock_id   = args[0]
        price      = float(args[1])
        shares     = int(args[2])
        rest       = args[3:]
        trade_date = _pop_flag(rest, "--date")
        note       = _pop_flag(rest, "--note") or ""
        open_position(stock_id, price, shares, trade_date=trade_date,
                      note=note, account=account)

    elif sub == "close":
        if len(args) < 1:
            print("用法：positions close <代號> [平倉價] [--shares 股數] [--account 帳戶] [--date YYYY-MM-DD]")
            return
        stock_id   = args[0]
        rest       = list(args[1:])
        trade_date = _pop_flag(rest, "--date")
        shares_str = _pop_flag(rest, "--shares")
        shares     = int(shares_str) if shares_str else None
        price      = float(rest[0]) if rest else None
        close_position(stock_id, price=price, shares=shares,
                       trade_date=trade_date, account=account)

    else:
        print(f"未知子指令：{sub}")
        print("可用：list / history / open / close")


def _pop_flag(args: list, flag: str) -> str | None:
    if flag in args:
        idx = args.index(flag)
        val = args[idx + 1] if idx + 1 < len(args) else None
        args[idx:idx + 2] = []
        return val
    return None
