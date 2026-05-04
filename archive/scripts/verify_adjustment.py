"""
P0-14：除權息 / 拆分事件驗證
掃 data/raw/ 找所有單日 |chg| > 10% 的事件，對照 data/dividends/ 和 data/splits/，
列出「raw 跳動但事件表沒對應紀錄」的殘留事件。

用法：python scripts/verify_adjustment.py
"""
import os
import sys
import pandas as pd
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "raw")
DIV_DIR = os.path.join(BASE, "data", "dividends")
SPL_DIR = os.path.join(BASE, "data", "splits")
ADJ_DIR = os.path.join(BASE, "data", "adjusted")

JUMP_THRESHOLD = 0.10   # |日漲跌| > 10% → 可疑事件
MATCH_WINDOW_DAYS = 3   # 事件日前後 ±3 個日曆日視為匹配


def load_raw(sid: str) -> pd.DataFrame | None:
    path = os.path.join(RAW_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.sort_values("date").set_index("date")


def get_dividend_dates(sid: str) -> set:
    """取得 dividends CSV 的除息 / 除權日期集合（±WINDOW）"""
    path = os.path.join(DIV_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return set()
    try:
        df = pd.read_csv(path)
    except Exception:
        return set()
    dates = set()
    for col in ("CashExDividendTradingDate", "StockExDividendTradingDate"):
        if col in df.columns:
            for v in df[col].dropna():
                try:
                    d = pd.Timestamp(v)
                    for delta in range(-MATCH_WINDOW_DAYS, MATCH_WINDOW_DAYS + 1):
                        dates.add(d + timedelta(days=delta))
                except Exception:
                    pass
    return dates


def get_split_dates(sid: str) -> set:
    """取得 splits CSV 的拆分 / 減資日期集合（±WINDOW）"""
    path = os.path.join(SPL_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return set()
    try:
        df = pd.read_csv(path)
    except Exception:
        return set()
    dates = set()
    if df.empty:
        return set()
    if "date" in df.columns:
        for v in df["date"].dropna():
            try:
                d = pd.Timestamp(v)
                for delta in range(-MATCH_WINDOW_DAYS, MATCH_WINDOW_DAYS + 1):
                    dates.add(d + timedelta(days=delta))
            except Exception:
                pass
    return dates


def check_adj_reduces_jump(sid: str, jump_date: pd.Timestamp, raw_chg: float) -> float | None:
    """驗證 adjusted 是否真的平滑掉這個跳動。
    回傳 adjusted 在同日的 pct_change，若無資料回傳 None。
    """
    path = os.path.join(ADJ_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype={"date": str})
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df = df.sort_values("date").set_index("date")
        if "close_adj" not in df.columns:
            return None
        adj_chg = df["close_adj"].pct_change()
        if jump_date in adj_chg.index:
            return float(adj_chg.loc[jump_date])
    except Exception:
        pass
    return None


def main():
    sids = sorted([f[:-4] for f in os.listdir(RAW_DIR) if f.endswith(".csv")])
    print(f"\n{'='*72}")
    print(f"  P0-14 除權息事件驗證  |日漲跌| > {JUMP_THRESHOLD:.0%}")
    print(f"  掃描 {len(sids)} 檔（data/raw/）")
    print(f"{'='*72}\n")

    all_events = []     # (sid, date, raw_chg)
    explained = []
    unexplained = []

    for sid in sids:
        raw = load_raw(sid)
        if raw is None or "close" not in raw.columns or len(raw) < 2:
            continue

        chg = raw["close"].pct_change()
        jumps = chg[chg.abs() > JUMP_THRESHOLD]

        if jumps.empty:
            continue

        div_dates = get_dividend_dates(sid)
        spl_dates = get_split_dates(sid)
        event_dates = div_dates | spl_dates

        for jdate, jchg in jumps.items():
            all_events.append((sid, jdate, jchg))
            matched = jdate in event_dates
            entry = {
                "sid": sid,
                "date": jdate.strftime("%Y-%m-%d"),
                "raw_chg": f"{jchg:+.1%}",
                "direction": "漲" if jchg > 0 else "跌",
                "div_match": jdate in div_dates,
                "spl_match": jdate in spl_dates,
            }
            # 也記錄 adjusted 是否平滑
            adj_chg = check_adj_reduces_jump(sid, jdate, jchg)
            if adj_chg is not None:
                entry["adj_chg"] = f"{adj_chg:+.1%}"
                entry["adj_ok"] = abs(adj_chg) < JUMP_THRESHOLD
            else:
                entry["adj_chg"] = "N/A"
                entry["adj_ok"] = None

            if matched:
                explained.append(entry)
            else:
                unexplained.append(entry)

    total = len(all_events)
    print(f"  偵測到 {total} 筆單日 |漲跌| > {JUMP_THRESHOLD:.0%} 事件")
    print(f"  [OK] FinMind 事件表能解釋：{len(explained)} 筆 ({len(explained)/max(total,1):.0%})")
    print(f"  [!!] 無法解釋（待查）：{len(unexplained)} 筆 ({len(unexplained)/max(total,1):.0%})\n")

    if explained:
        print(f"  {'─'*70}")
        print(f"  【已解釋事件】（dividend / split 表有對應記錄）")
        print(f"  {'─'*70}")
        print(f"  {'股票':<7} {'日期':<12} {'raw 漲跌':>8} {'adj 漲跌':>9}  {'adj 修正':^8}  {'來源'}")
        print(f"  {'─'*70}")
        for e in explained:
            source = ("div" if e["div_match"] else "") + ("+" if e["div_match"] and e["spl_match"] else "") + ("split" if e["spl_match"] else "")
            adj_ok_str = "[OK]  " if e["adj_ok"] is True else ("[!!]  " if e["adj_ok"] is False else "  -  ")
            print(f"  {e['sid']:<7} {e['date']:<12} {e['raw_chg']:>8} {e['adj_chg']:>9}  {adj_ok_str:^8}  {source}")

    if unexplained:
        print(f"\n  {'─'*70}")
        print(f"  【無法解釋事件】← 需要確認是否為減資 / M&A / 資料錯誤")
        print(f"  {'─'*70}")
        print(f"  {'股票':<7} {'日期':<12} {'raw 漲跌':>8} {'adj 漲跌':>9}  {'adj 修正':^8}")
        print(f"  {'─'*70}")
        for e in unexplained:
            adj_ok_str = "[OK]  " if e["adj_ok"] is True else ("[!!]  " if e["adj_ok"] is False else "  -  ")
            print(f"  {e['sid']:<7} {e['date']:<12} {e['raw_chg']:>8} {e['adj_chg']:>9}  {adj_ok_str:^8}")

        print(f"\n  提示：無法解釋的事件若 adj 已平滑 (✓)，代表 split/減資事件已被 TaiwanStockSplitPrice 覆蓋；")
        print(f"        若 adj 仍大 (✗)，需人工確認資料源頭。")
    else:
        print("  所有 jump 事件均已被 FinMind 事件表解釋。")

    print(f"\n{'='*72}")
    print("  驗證完畢")
    print(f"{'='*72}\n")

    # 回傳摘要供自動化測試
    return {
        "total": total,
        "explained": len(explained),
        "unexplained": len(unexplained),
        "unexplained_list": unexplained,
    }


if __name__ == "__main__":
    main()
