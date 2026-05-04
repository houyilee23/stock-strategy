"""
0050 還原股價驗證實驗
- 從 FinMind 免費 API 抓除權息 + 拆分事件
- 用我們現有 data/raw/0050.csv 的 raw close 自己算 adj close
- 印出對照：拆分日、各次除息日、CAGR

執行：'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' scripts/test_0050_adjustment.py
"""
import os, sys, requests, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

FINMIND = "https://api.finmindtrade.com/api/v4/data"
SID = "0050"
START = "2010-01-01"
END   = "2026-04-22"


def fmind(dataset, sid, start, end):
    r = requests.get(FINMIND, params={
        "dataset": dataset, "data_id": sid,
        "start_date": start, "end_date": end,
    }, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        raise RuntimeError(f"{dataset}: {j}")
    return pd.DataFrame(j.get("data", []))


def load_raw(sid):
    df = pd.read_csv(os.path.join(BASE, "data", "raw", f"{sid}.csv"), dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.sort_values("date").set_index("date")


def calc_adj_close(raw_close: pd.Series, dividends: pd.DataFrame, splits: pd.DataFrame) -> pd.Series:
    """
    向後復權 (backward adjustment):
    從最近事件往過去走，每個事件把「事件日(含)之前」的歷史價格乘上 factor。
    現在的價格不動，歷史被往下/往上拉，使序列「連續可比」。
    """
    adj = raw_close.copy().astype(float)

    # 收集所有事件: (event_date, factor)  — factor < 1 表股價往下調
    events = []

    # 除息: factor = (P_prev - cash_div) / P_prev
    for _, row in dividends.iterrows():
        ex_date_str = row.get("CashExDividendTradingDate") or ""
        cash_div = float(row.get("CashEarningsDistribution") or 0) + float(row.get("CashStatutorySurplus") or 0)
        if not ex_date_str or cash_div <= 0:
            continue
        ex_date = pd.to_datetime(ex_date_str)
        # 找除息日前一個交易日的 raw close
        prev_idx = adj.index[adj.index < ex_date]
        if len(prev_idx) == 0:
            continue
        p_prev = adj.loc[prev_idx[-1]]
        if p_prev <= 0 or cash_div >= p_prev:
            continue
        factor = (p_prev - cash_div) / p_prev
        events.append(("除息", ex_date, factor, f"cash_div={cash_div:.3f}, P_prev={p_prev:.2f}"))

        # 股票股利（如果有）
        stock_div = float(row.get("StockEarningsDistribution") or 0) + float(row.get("StockStatutorySurplus") or 0)
        if stock_div > 0:
            stock_ex = row.get("StockExDividendTradingDate") or ex_date_str
            stock_ex_dt = pd.to_datetime(stock_ex) if stock_ex else ex_date
            factor_s = 1 / (1 + stock_div / 10)
            events.append(("除權", stock_ex_dt, factor_s, f"stock_div={stock_div:.3f}"))

    # 拆分: factor = after_price / before_price
    for _, row in splits.iterrows():
        sp_date = pd.to_datetime(row["date"])
        before = float(row["before_price"])
        after  = float(row["after_price"])
        if before <= 0:
            continue
        factor = after / before
        events.append((f"拆分({row.get('type','')})", sp_date, factor,
                       f"before={before:.2f} after={after:.2f}"))

    # 排序：事件日由舊到新
    events.sort(key=lambda x: x[1])

    print(f"\n  共 {len(events)} 個事件:")
    for et, ed, f, note in events:
        print(f"    {ed.strftime('%Y-%m-%d')}  {et:<10} factor={f:.6f}  ({note})")

    # 套用：每個事件，把事件日「之前」(不含當日)的所有價格乘以 factor
    for et, ed, factor, _ in events:
        mask = adj.index < ed
        adj.loc[mask] = adj.loc[mask] * factor

    return adj


def main():
    print("="*70)
    print(f"  0050 還原股價驗證 ({START} ~ {END})")
    print("="*70)

    print("\n[1] 抓 FinMind 事件資料 (免費)")
    div = fmind("TaiwanStockDividend", SID, START, END)
    spl = fmind("TaiwanStockSplitPrice", SID, START, END)
    print(f"  TaiwanStockDividend     : {len(div)} 筆")
    print(f"  TaiwanStockSplitPrice   : {len(spl)} 筆")

    print("\n[2] 載入 raw close (data/raw/0050.csv)")
    raw = load_raw(SID)
    print(f"  資料範圍: {raw.index[0].date()} ~ {raw.index[-1].date()}, 共 {len(raw)} 列")
    print(f"  起點 close: {raw['close'].iloc[0]:.2f}")
    print(f"  終點 close: {raw['close'].iloc[-1]:.2f}")

    print("\n[3] 計算還原股價 (backward adjustment)")
    adj = calc_adj_close(raw["close"], div, spl)

    print("\n[4] 對照: 拆分日前後 (2025-06-10 ~ 2025-06-18)")
    print("  date         raw_close   adj_close")
    for d in pd.date_range("2025-06-09", "2025-06-23"):
        if d in raw.index:
            print(f"  {d.date()}   {raw.loc[d, 'close']:>9.2f}   {adj.loc[d]:>9.2f}")

    print("\n[5] 對照: 一次除息日 (隨選 2024-01-17)")
    target = pd.Timestamp("2024-01-17")
    nearby = raw.index[(raw.index >= target - pd.Timedelta(days=3)) &
                       (raw.index <= target + pd.Timedelta(days=3))]
    print("  date         raw_close   adj_close")
    for d in nearby:
        print(f"  {d.date()}   {raw.loc[d, 'close']:>9.2f}   {adj.loc[d]:>9.2f}")

    print("\n[6] CAGR 對照")
    raw_start, raw_end = raw["close"].iloc[0], raw["close"].iloc[-1]
    adj_start, adj_end = adj.iloc[0], adj.iloc[-1]
    years = (raw.index[-1] - raw.index[0]).days / 365.25
    raw_cagr = (raw_end / raw_start) ** (1/years) - 1
    adj_cagr = (adj_end / adj_start) ** (1/years) - 1
    print(f"  raw_close   起點={raw_start:>8.2f}  終點={raw_end:>8.2f}  CAGR={raw_cagr:>+6.2%}")
    print(f"  adj_close   起點={adj_start:>8.2f}  終點={adj_end:>8.2f}  CAGR={adj_cagr:>+6.2%}")

    print("\n[7] 截取 2017-01-01 起 (跟回測同區間)")
    start_2017 = pd.Timestamp("2017-01-03")
    sub_raw = raw["close"][raw.index >= start_2017]
    sub_adj = adj[adj.index >= start_2017]
    yrs = (sub_raw.index[-1] - sub_raw.index[0]).days / 365.25
    raw_c = (sub_raw.iloc[-1] / sub_raw.iloc[0]) ** (1/yrs) - 1
    adj_c = (sub_adj.iloc[-1] / sub_adj.iloc[0]) ** (1/yrs) - 1
    print(f"  raw  CAGR (2017~now): {raw_c:+.2%}")
    print(f"  adj  CAGR (2017~now): {adj_c:+.2%}")

    # 寫到 output/ 避免汙染 data/adjusted/（被 backtest --all 誤掃）
    out_dir = os.path.join(BASE, "output", "verify")
    os.makedirs(out_dir, exist_ok=True)
    out = raw.copy()
    out["close_adj"] = adj
    out.to_csv(os.path.join(out_dir, f"{SID}_adj_check.csv"), encoding="utf-8-sig")
    print(f"\n[8] 寫出 output/verify/{SID}_adj_check.csv (含 close_adj 欄位)")


if __name__ == "__main__":
    main()
