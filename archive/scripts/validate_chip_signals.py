"""
scripts/validate_chip_signals.py
Style 3 籌碼策略 — 階段 1.5 PnL 驗證

進場條件（4 條件全滿足，叢集首日）：
  1. 個股 close > MA60
  2. 外資+投信 5日累計淨買超 > 0，且今日淨買超 > 0（T-1 shift，防穿越）
  3. close > 過去 20 日最高 × 0.98（近高突破）
  4. 大盤 0050 close > MA60
出場條件（任一觸發）：
  X1. 5日累計淨買超轉負
  X2. close < MA60
  X3. 持倉 >= 60 個交易日（強制出場）
成交：T 日訊號 → T+1 開盤成交
用法：python scripts/validate_chip_signals.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time, requests
import pandas as pd
import numpy as np
import yaml

SIDS        = ["2330", "3017", "6669", "2454", "2317"]
START       = "2013-01-01"
END         = "2026-04-22"
BASE        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

# 費用（讀 strategy.yaml）
with open(os.path.join(BASE, "config", "strategy.yaml"), encoding="utf-8") as _f:
    _fees = yaml.safe_load(_f)["fees"]
BUY_COMM  = _fees["buy_commission_rate"]
SELL_COMM = _fees["sell_commission_rate"]
SELL_TAX  = _fees["sell_tax_rate"]
SLIP      = _fees["slippage_rate"]


# ── 資料載入 ────────────────────────────────────────────────────

def fetch_chips(sid: str) -> pd.DataFrame:
    r = requests.get(FINMIND_URL, params={
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
        "data_id": sid, "start_date": START, "end_date": END}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        raise RuntimeError(f"{sid} API status={j.get('status')}: {j.get('msg','')}")
    raw = pd.DataFrame(j.get("data", []))
    if raw.empty:
        raise RuntimeError(f"{sid} 籌碼資料為空")
    raw["date"] = pd.to_datetime(raw["date"])
    raw[["buy","sell"]] = raw[["buy","sell"]].apply(pd.to_numeric, errors="coerce").fillna(0)
    raw["net"] = raw["buy"] - raw["sell"]
    pivot = raw[raw["name"].isin(["Foreign_Investor","Investment_Trust"])].copy()
    wide = pivot.pivot_table(index="date", columns="name", values="net", aggfunc="sum").fillna(0)
    wide.columns.name = None
    wide = wide.rename(columns={"Foreign_Investor":"foreign_net","Investment_Trust":"trust_net"})
    for c in ("foreign_net","trust_net"):
        if c not in wide.columns: wide[c] = 0.0
    return wide.sort_index()


def load_ohlcv(sid: str) -> pd.DataFrame:
    path = os.path.join(BASE, "data", "adjusted", f"{sid}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到 {path}")
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").set_index("date")
    close_col = "close_adj" if "close_adj" in df.columns else "close"
    return pd.DataFrame({
        "open":  df["open"].astype(float),
        "close": df[close_col].astype(float),
    }, index=df.index)


# ── 策略模擬 ────────────────────────────────────────────────────

def simulate(sid: str, ohlcv: pd.DataFrame, chips: pd.DataFrame,
             mkt_close: pd.Series, mkt_ma60: pd.Series) -> dict:
    df = ohlcv.copy()
    df = df.join(chips[["foreign_net","trust_net"]], how="left").fillna(0.0)

    # T-1 shift（防穿越）
    df["f_s"] = df["foreign_net"].shift(1)
    df["t_s"] = df["trust_net"].shift(1)
    df["combo_s"] = df["f_s"] + df["t_s"]
    df["roll5"]   = df["combo_s"].rolling(5, min_periods=5).sum()

    df["ma60"]   = df["close"].rolling(60, min_periods=60).mean()
    df["high20"] = df["close"].rolling(20, min_periods=20).max().shift(1)
    df["mkt_c"]  = mkt_close.reindex(df.index)
    df["mkt_m"]  = mkt_ma60.reindex(df.index)

    # 4 個進場條件
    c1 = df["close"] > df["ma60"]
    c2 = (df["roll5"] > 0) & (df["combo_s"] > 0)
    c3 = df["close"] > df["high20"] * 0.98
    c4 = df["mkt_c"] > df["mkt_m"]
    sig = c1 & c2 & c3 & c4

    # 叢集首日（cluster collapsing）
    entry_sig = sig & ~sig.shift(1).fillna(False)

    # 出場條件（T 日判斷，T+1 成交）
    exit_sig = (df["roll5"] < 0) | (df["close"] < df["ma60"])

    # ── 逐日模擬 ──
    trades = []
    in_pos = False
    entry_open = entry_date = None
    hold_days = 0

    idx = df.index.tolist()
    for i, today in enumerate(idx):
        if i == 0:
            continue
        yesterday = idx[i - 1]

        if not in_pos:
            if entry_sig.get(yesterday, False):
                entry_open = df.at[today, "open"] * (1 + SLIP) * (1 + BUY_COMM)
                entry_date = today
                hold_days  = 0
                in_pos     = True
        else:
            hold_days += 1
            forced = hold_days >= 60
            if exit_sig.get(yesterday, False) or forced:
                exit_open  = df.at[today, "open"]
                sell_eff   = exit_open * (1 - SLIP) * (1 - SELL_COMM - SELL_TAX)
                ret        = sell_eff / entry_open - 1
                reason     = ("強制60日" if forced else
                              "chip轉負"  if df.at[yesterday,"roll5"] < 0 else "破MA60")
                trades.append({
                    "entry_date": entry_date, "exit_date": today,
                    "entry_open": df.at[entry_date,"open"],
                    "exit_open":  exit_open,
                    "hold_days":  hold_days,
                    "ret":        ret,
                    "chip5d":     df.at[yesterday,"roll5"] / 1000,
                    "exit_reason": reason,
                })
                in_pos = False

    if not trades:
        return {"trades": [], "n": 0}

    tr = pd.DataFrame(trades)
    wins = tr[tr["ret"] > 0]
    losses = tr[tr["ret"] <= 0]

    win_rate   = len(wins) / len(tr)
    avg_win    = wins["ret"].mean() if len(wins) > 0 else 0.0
    avg_loss   = losses["ret"].mean() if len(losses) > 0 else 0.0
    pf         = (wins["ret"].sum() / -losses["ret"].sum()
                  if len(losses) > 0 and losses["ret"].sum() != 0 else np.inf)
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss

    # 累計報酬 & CAGR（閉倉曲線）
    equity = (1 + tr["ret"]).cumprod()
    cum_ret = equity.iloc[-1] - 1
    first_e = tr["entry_date"].min()
    last_x  = tr["exit_date"].max()
    years   = max((last_x - first_e).days / 365.25, 0.5)
    cagr    = (equity.iloc[-1]) ** (1 / years) - 1

    # MaxDD（閉倉曲線）
    roll_max = equity.cummax()
    mdd_strat = ((equity - roll_max) / roll_max).min()

    # B&H（第一筆進場日 ~ 最後一筆出場日，用 adjusted close）
    bah_ser  = df["close"].reindex(pd.date_range(first_e, last_x, freq="B")).ffill().dropna()
    bah_eq   = bah_ser / bah_ser.iloc[0]
    bah_cum  = bah_eq.iloc[-1] - 1
    bah_cagr = bah_eq.iloc[-1] ** (1 / years) - 1
    bah_rm   = bah_eq.cummax()
    bah_mdd  = ((bah_eq - bah_rm) / bah_rm).min()

    return {
        "trades": tr, "n": len(tr),
        "win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss,
        "pf": pf, "expectancy": expectancy,
        "cum_ret": cum_ret, "cagr": cagr, "mdd": mdd_strat,
        "bah_cum": bah_cum, "bah_cagr": bah_cagr, "bah_mdd": bah_mdd,
        "years": years, "avg_hold": tr["hold_days"].mean(),
    }


# ── 列印每檔 ────────────────────────────────────────────────────

def print_stock(sid: str, res: dict):
    if res["n"] == 0:
        print(f"\n  [{sid}] 無交易")
        return
    tr = res["trades"]
    print(f"\n{'='*72}")
    print(f"  {sid}  績效統計（{START} ~ {END}，{res['years']:.1f} 年）")
    print(f"{'='*72}")
    print(f"  進場次數         : {res['n']}")
    print(f"  年化進場次數     : {res['n']/res['years']:.1f}")
    print(f"  平均持倉天數     : {res['avg_hold']:.1f} 個交易日")
    print()
    wr = res["win_rate"]
    print(f"  Win rate         : {wr:.1%}")
    print(f"  平均贏 / 平均輸  : {res['avg_win']:+.2%} / {res['avg_loss']:+.2%}")
    pf_s = f"{res['pf']:.2f}" if not np.isinf(res['pf']) else "∞"
    print(f"  Profit factor    : {pf_s}")
    print(f"  Expectancy       : {res['expectancy']:+.2%}")
    print()
    print(f"  累計報酬         : {res['cum_ret']:+.1%}")
    print(f"  年化報酬 (CAGR)  : {res['cagr']:+.1%}")
    print(f"  最大回撤         : {res['mdd']:+.1%}")
    print()
    print(f"  Buy-and-hold 對照：")
    print(f"    累計報酬       : {res['bah_cum']:+.1%}")
    print(f"    年化報酬       : {res['bah_cagr']:+.1%}")
    print(f"    最大回撤       : {res['bah_mdd']:+.1%}")
    alpha = res["cagr"] - res["bah_cagr"]
    print(f"  超額年化報酬     : {alpha:+.1%}   （策略 - B&H）")

    # 前 5 + 後 5 筆 trades
    sample = pd.concat([tr.head(5), tr.tail(5)]).drop_duplicates()
    print(f"\n  {'日期':^11}  {'動作':^4}  {'成交價':>8}  {'chip5d(張)':>10}  {'出場原因':^8}  {'持倉':>4}  {'PnL%':>7}")
    print(f"  {'-'*66}")
    for _, row in sample.iterrows():
        print(f"  {row['entry_date'].strftime('%Y-%m-%d')}  BUY   {row['entry_open']:>8.1f}  "
              f"  {'—':>10}   {'—':^8}   {'—':>4}   {'—':>7}")
        print(f"  {row['exit_date'].strftime('%Y-%m-%d')}  SELL  {row['exit_open']:>8.1f}  "
              f"  {row['chip5d']:>+10.0f}   {row['exit_reason']:^8}   {row['hold_days']:>4}   "
              f"  {row['ret']:>+6.1%}")


# ── 主程式 ──────────────────────────────────────────────────────

print(f"\n  載入 0050 大盤資料...")
mkt_ohlcv = load_ohlcv("0050")
mkt_close = mkt_ohlcv["close"]
mkt_ma60  = mkt_close.rolling(60, min_periods=60).mean()

all_results = {}

for sid in SIDS:
    print(f"  [{sid}] 抓籌碼資料中...", end=" ", flush=True)
    try:
        chips = fetch_chips(sid)
        time.sleep(1.2)
        print("OK")
    except Exception as e:
        print(f"\n  [ERROR] {sid} 籌碼失敗：{e}")
        continue
    try:
        ohlcv = load_ohlcv(sid)
    except FileNotFoundError as e:
        print(f"  [ERROR] {e}")
        continue
    res = simulate(sid, ohlcv, chips, mkt_close, mkt_ma60)
    all_results[sid] = res
    print_stock(sid, res)

# ── 總結表 ──────────────────────────────────────────────────────
print(f"\n\n{'='*72}")
print(f"  總結（5 檔對照）")
print(f"{'='*72}")
print(f"  {'Stock':<6} {'Trades':>6} {'WinRate':>8} {'PF':>5} {'E(R)':>7} "
      f"{'Strategy':>9} {'B&H':>7} {'Alpha':>7} {'MaxDD':>7}")
print(f"  {'-'*68}")

strat_cagrs, bah_cagrs, pfs, win_rates, alphas = [], [], [], [], []
for sid in SIDS:
    res = all_results.get(sid)
    if not res or res["n"] == 0:
        print(f"  {sid:<6} {'—':>6}")
        continue
    alpha = res["cagr"] - res["bah_cagr"]
    pf_s  = f"{res['pf']:.2f}" if not np.isinf(res['pf']) else "∞"
    print(f"  {sid:<6} {res['n']:>6} {res['win_rate']:>8.1%} {pf_s:>5} "
          f"{res['expectancy']:>+7.2%} {res['cagr']:>+9.1%} "
          f"{res['bah_cagr']:>+7.1%} {alpha:>+7.1%} {res['mdd']:>+7.1%}")
    strat_cagrs.append(res["cagr"]); bah_cagrs.append(res["bah_cagr"])
    pfs.append(res["pf"] if not np.isinf(res["pf"]) else np.nan)
    win_rates.append(res["win_rate"]); alphas.append(alpha)

if strat_cagrs:
    print(f"  {'-'*68}")
    print(f"  {'median':<6} {'':>6} {np.median(win_rates):>8.1%} "
          f"{np.nanmedian(pfs):>5.2f} {'':>7} "
          f"{np.median(strat_cagrs):>+9.1%} {np.median(bah_cagrs):>+7.1%} "
          f"{np.median(alphas):>+7.1%}")

print(f"""
{'='*72}
  下一步
{'='*72}
  請看上方總結表，判斷：

  A. 策略 CAGR 中位數 > B&H + 5%  → 概念成立，進階段 2
  B. 策略 CAGR 中位數 ~= B&H +/-5%  → 改規則重跑（例如加 RSI 過濾）
  C. 策略 CAGR 中位數 < B&H - 5%  → 概念不對，重新討論方向

  另外注意：
  - 5 檔 PF 分散度（標準差大 → 策略 universality 待確認）
  - MaxDD 是否 < 30%
  - 年化進場次數是否在 1~5 次/年/股 的合理區間
{'='*72}
""")
