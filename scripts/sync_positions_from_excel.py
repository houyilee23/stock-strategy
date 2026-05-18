"""從 Excel「投資款.xlsx」的「交易紀錄」sheet 同步到 trades_<account>.csv。

讀取使用者手動維護的 Excel 交易記錄表（個人實際持倉），轉換為系統內部的
trades CSV 格式，供 ledger + positions 模組使用。

Excel 預期格式（sheet[1] = 「交易紀錄」）：
  Col 1: 日期 (datetime)
  Col 2: 動作 (Buy / Sell / 其他如「股利收」)
  Col 3: 代號 (stock_id)
  Col 4: 名稱
  Col 5: 股數
  Col 6: 現金流（buy 為負，sell 為正）
  Col 7: 餘額
  Col 8: 平均成本（=現金流/股數，已含手續費/交易稅）
  Col 14: 備註

只匯入 Buy/Sell（其他動作如股利、轉帳跳過）。idempotent — 重複跑不會
產生重複交易（用 date+sid+action+shares 作 dedup key）。

用法：
  python scripts/sync_positions_from_excel.py [--account Personal] [--dry-run]
"""
from __future__ import annotations
import os
import sys
import csv
import argparse
from datetime import datetime, date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

DEFAULT_EXCEL = r"D:\Users\houyi\OneDrive\文件\投資款.xlsx"
DEFAULT_ACCOUNT = "Personal"
TRANSACTION_SHEET_INDEX = 1  # 交易紀錄 sheet


def parse_excel(excel_path: str) -> list[dict]:
    """讀 Excel → list of {date, stock_id, action, price, shares, note}.

    只包含 Buy / Sell。其他動作（股利收、轉帳）略過。
    """
    try:
        import openpyxl
    except ImportError:
        print("[ERR] openpyxl 未安裝。執行：pip install openpyxl")
        sys.exit(2)

    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    if TRANSACTION_SHEET_INDEX >= len(wb.worksheets):
        print(f"[ERR] Excel 不含 sheet index {TRANSACTION_SHEET_INDEX}")
        sys.exit(2)
    ws = wb.worksheets[TRANSACTION_SHEET_INDEX]

    trades = []
    skipped = {"non_buy_sell": 0, "missing_data": 0}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 8:
            continue
        dt, action, sid, name, shares, cashflow, balance, price = row[:8]
        note = row[13] if len(row) > 13 else None

        # 過濾：非 Buy/Sell 跳過
        if action not in ("Buy", "Sell"):
            skipped["non_buy_sell"] += 1
            continue

        # 必要欄位完整
        if dt is None or sid is None or shares is None or price is None:
            skipped["missing_data"] += 1
            continue

        # 標準化
        if isinstance(dt, datetime):
            date_str = dt.strftime("%Y-%m-%d")
        elif isinstance(dt, date):
            date_str = dt.strftime("%Y-%m-%d")
        else:
            date_str = str(dt)[:10]

        sid_str = str(sid).strip()
        shares_int = int(shares)
        price_float = float(price)
        action_upper = action.upper()  # BUY / SELL
        note_str = (str(note).strip() if note else "") or (str(name).strip() if name else "")

        trades.append({
            "date": date_str,
            "stock_id": sid_str,
            "action": action_upper,
            "price": round(price_float, 4),
            "shares": shares_int,
            "note": note_str,
        })

    print(f"  Excel 讀取：{len(trades)} 筆 Buy/Sell  (略過 {skipped['non_buy_sell']} 筆非交易、"
          f"{skipped['missing_data']} 筆缺欄位)")
    return trades


def load_existing_trades(csv_path: str) -> list[dict]:
    """讀取現有 trades CSV，回傳 list of dict（保留 BUY/SELL/DEPOSIT/WITHDRAW 全部）。"""
    if not os.path.exists(csv_path):
        return []
    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        # 跳過 # comment 行
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    if len(lines) <= 1:
        return []
    from io import StringIO
    reader = csv.DictReader(StringIO("".join(lines)))
    for r in reader:
        rows.append(r)
    return rows


def _trade_key(t: dict) -> tuple:
    """Dedup key: (date, stock_id, action, shares) — same day, same direction, same shares."""
    return (t["date"], str(t["stock_id"]).strip(), t["action"].upper(), int(t["shares"]))


def write_trades_csv(csv_path: str, trades_to_write: list[dict],
                     account: str, dry_run: bool = False):
    """寫入 trades CSV（覆寫，保留 header 註解）。"""
    if dry_run:
        print(f"  [DRY-RUN] 不寫檔。")
        return

    header_comment = (
        "# ══════════════════════════════════════════════\n"
        "# 交易流水帳  格式說明：\n"
        "#   action: BUY 買股 / SELL 賣股 / DEPOSIT 現金存入 / WITHDRAW 現金提出\n"
        "#   DEPOSIT/WITHDRAW → stock_id=CASH, price=1, shares=NT$金額\n"
        "#   BUY/SELL → price=股價（已含手續費/稅）, shares=股數\n"
        f"# 帳戶：{account}\n"
        f"# 來源：投資款.xlsx「交易紀錄」sheet (自動同步)\n"
        f"# 最後同步：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "# ══════════════════════════════════════════════\n"
        "\n"
    )

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(header_comment)
        writer = csv.DictWriter(f, fieldnames=["date", "stock_id", "action", "price", "shares", "note"])
        writer.writeheader()
        for t in trades_to_write:
            writer.writerow({
                "date": t["date"],
                "stock_id": t["stock_id"],
                "action": t["action"],
                "price": t["price"],
                "shares": t["shares"],
                "note": t["note"],
            })
    print(f"  寫入 {csv_path}: {len(trades_to_write)} 筆")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--excel", default=DEFAULT_EXCEL,
                   help=f"Excel 路徑（預設 {DEFAULT_EXCEL}）")
    p.add_argument("--account", default=DEFAULT_ACCOUNT,
                   help=f"帳戶名稱（預設 {DEFAULT_ACCOUNT}），寫到 data/trades_<account>.csv")
    p.add_argument("--dry-run", action="store_true",
                   help="只輸出統計，不寫檔")
    p.add_argument("--include-cash", action="store_true",
                   help="（保留）將來支援讀取現金存入/提出")
    args = p.parse_args()

    print(f"\n=== Sync 持倉 from Excel ===")
    print(f"  Excel: {args.excel}")
    print(f"  Account: {args.account}")

    if not os.path.exists(args.excel):
        print(f"[ERR] Excel 檔不存在: {args.excel}")
        sys.exit(2)

    # 1. 讀 Excel
    excel_trades = parse_excel(args.excel)
    excel_trades.sort(key=lambda t: (t["date"], t["stock_id"]))

    # 2. 讀現有 trades CSV
    csv_path = os.path.join(BASE_DIR, "data", f"trades_{args.account}.csv")
    existing = load_existing_trades(csv_path)
    print(f"  既有 CSV：{len(existing)} 筆")

    # 3. dedup: 保留現有的 DEPOSIT/WITHDRAW + 新的 BUY/SELL（覆寫舊的 BUY/SELL）
    # 簡單策略：刪掉 BUY/SELL 行，append Excel 全部 BUY/SELL
    cash_rows = [r for r in existing if r.get("action", "").upper() in ("DEPOSIT", "WITHDRAW")]

    # 合併：先 cash 後股票，按日期排序
    merged = cash_rows + excel_trades
    merged.sort(key=lambda t: (t["date"], 0 if t.get("action","").upper() in ("DEPOSIT","WITHDRAW") else 1))

    # Excel vs existing diff
    old_keys = {_trade_key(r) for r in existing if r.get("action","").upper() in ("BUY", "SELL")}
    new_keys = {_trade_key(t) for t in excel_trades}
    added = new_keys - old_keys
    removed = old_keys - new_keys
    print(f"\n  Diff: +{len(added)} 新增, -{len(removed)} Excel 沒有的舊筆")
    if added:
        for k in sorted(added)[:10]:
            print(f"    + {k}")
        if len(added) > 10:
            print(f"    + ... ({len(added)-10} more)")
    if removed:
        for k in sorted(removed)[:10]:
            print(f"    - {k}")

    # 4. 寫回
    print()
    write_trades_csv(csv_path, merged, args.account, dry_run=args.dry_run)

    # 5. 計算 open positions
    if not args.dry_run:
        try:
            from src.ledger import load_trades, compute_open_positions
            trades_df = load_trades(args.account)
            open_pos = compute_open_positions(trades_df)
            print(f"\n  目前持倉：{len(open_pos)} 檔")
            for p in open_pos[:20]:
                avg_cost = p.get("open_price", 0) * 1.0  # may need adjustment for splits/divs
                print(f"    {p['stock_id']:<8} {p['shares']:>5} 股 @ ~{avg_cost:.2f}")
            if len(open_pos) > 20:
                print(f"    ... ({len(open_pos)-20} more)")
        except Exception as e:
            print(f"  [WARN] 無法計算 open positions: {e}")


if __name__ == "__main__":
    main()
