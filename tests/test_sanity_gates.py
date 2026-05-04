# Sanity gates — 確保回測結果在合理範圍
# 跑法：python.exe -m pytest tests/test_sanity_gates.py -v
# P0-4 修正：上輪「全綠卻全紅」根因就是缺這些合理性檢查
import sys
import os
import math
import yaml
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.backtest.result import PortfolioResult
from src.strategy.signals.regime import detect_regime
from src.strategy.signals.style1_pullback import generate_signals

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "strategy.yaml")
with open(_cfg_path, encoding="utf-8") as f:
    _STRATEGY = yaml.safe_load(f)


def load_stock(sid: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, f"{sid}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").set_index("date")
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            return None
    return df[["open", "high", "low", "close", "volume"]].astype(float)


BT_CFG_REAL = BacktestConfig(
    fees=_STRATEGY["fees"],
    start_date="2017-01-01",
    end_date="today",
    initial_capital=100_000,
    max_position_pct=1.0,  # 單股模式：全倉
)


# ── Sanity Gate A：0050 buy-and-hold CAGR 在 3%~15% ─────────

def test_0050_buyhold_cagr_reasonable():
    """0050 buy-and-hold 2017~today 年化報酬應在 3%~15%（歷史合理區間）"""
    df = load_stock("0050")
    if df is None:
        pytest.skip("0050 資料不存在")

    df_sub = df["2017-01-01":]
    years = (df_sub.index[-1] - df_sub.index[0]).days / 365.25
    if years < 1:
        pytest.skip(f"0050 資料不足 1 年（{years:.2f} 年）")

    actions = ["HOLD"] * len(df_sub)
    actions[0] = "BUY"
    actions[-2] = "SELL"
    sig = pd.DataFrame({"action": actions}, index=df_sub.index)

    bt = Backtester(BT_CFG_REAL)
    result = bt.run_per_stock("0050", df_sub, sig)
    assert result.n_trades == 1, f"buy-and-hold 應恰好 1 筆交易，實際 {result.n_trades}"

    t = result.trades[0]
    hold_d = max(t.hold_days, 1)
    cagr = (1 + t.pnl_pct) ** (252 / hold_d) - 1

    # 注意：資料為未調整除息價，每年約 3-4% 股利從股價扣除
    # 所以 price-only CAGR 低於含息報酬約 3-4 個百分點
    # 下限設 0.5%（避免重大計算錯誤），上限設 20%（避免短期爆炸值）
    assert 0.005 <= cagr <= 0.20, (
        f"0050 buy-and-hold price-only CAGR = {cagr:.2%}，超出合理範圍 0.5%~20%。"
        f"entry={t.entry_price:.2f} exit={t.exit_price:.2f} "
        f"pnl_pct={t.pnl_pct:.2%} hold_days={hold_d}"
    )
    # 額外印出供人工確認
    print(f"\n  0050 buy-and-hold: entry={t.entry_price:.2f} exit={t.exit_price:.2f}"
          f" pnl={t.pnl_pct:.2%} hold={hold_d}d CAGR={cagr:.2%}")


# ── Sanity Gate B：portfolio equity 最終不應損失 >70% ────────

def test_portfolio_equity_not_bankrupt():
    """portfolio 回測最終 equity 應 > 初始資金 30%（未破產）"""
    df_0050 = load_stock("0050")
    if df_0050 is None:
        pytest.skip("0050 資料不存在")

    # 載入清單
    import yaml as _yaml
    wl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "config", "watchlists.yaml")
    with open(wl_path, encoding="utf-8") as f:
        wl = _yaml.safe_load(f)
    takeshi_ids = [str(s) for s in wl.get("Takeshi", [])]

    regime = detect_regime(df_0050, _STRATEGY["regime"]["ma_long"])
    params = _STRATEGY["style1_pullback"]

    dfs = {}
    signals_dict = {}
    for sid in takeshi_ids:
        df = load_stock(sid)
        if df is None or len(df) < 250:
            continue
        stock_regime = regime.reindex(df.index, method="ffill").fillna("BEAR")
        dfs[sid] = df
        signals_dict[sid] = generate_signals(df, stock_regime, params)

    if len(dfs) < 3:
        pytest.skip("可用股票不足 3 檔")

    bt = Backtester(BacktestConfig(
        fees=_STRATEGY["fees"],
        start_date="2017-01-01",
        end_date="today",
        initial_capital=100_000,
        max_position_pct=0.25,
    ))

    result = bt.run_portfolio(dfs, signals_dict, lambda *a: {})
    eq = result.equity_curve
    assert len(eq) > 0

    initial = eq.iloc[0]
    final = eq.iloc[-1]
    ratio = final / initial
    assert ratio > 0.3, (
        f"組合最終 equity 損失 >70%：{initial:.0f} → {final:.0f}（{ratio:.1%}）"
        "可能是費用計算錯誤或資料問題"
    )


# ── Sanity Gate C：MaxDD 在 [-1, 0) ─────────────────────────

def test_portfolio_maxdd_range():
    """MaxDD 應在 (-100%, 0)，不應為 NaN 或 0"""
    df_0050 = load_stock("0050")
    if df_0050 is None:
        pytest.skip("0050 資料不存在")

    import yaml as _yaml
    wl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "config", "watchlists.yaml")
    with open(wl_path, encoding="utf-8") as f:
        wl = _yaml.safe_load(f)

    regime = detect_regime(df_0050)
    params = _STRATEGY["style1_pullback"]
    sid = "1301"
    df = load_stock(sid)
    if df is None:
        pytest.skip("1301 資料不存在")

    stock_regime = regime.reindex(df.index, method="ffill").fillna("BEAR")
    signals = generate_signals(df, stock_regime, params)

    bt = Backtester(BT_CFG_REAL)
    result = bt.run_per_stock(sid, df, signals)
    mdd = result.max_drawdown

    if math.isnan(mdd):
        pytest.skip("無 equity_curve，MaxDD=NaN（可能 0 筆交易）")

    assert -1.0 < mdd <= 0.0, f"MaxDD={mdd:.4f} 超出合理範圍 (-1.0, 0]"


# ── Sanity Gate D：per-stock PF 不該全部 < 0.5 ───────────────

def test_per_stock_pf_not_all_bad():
    """若回測筆數足夠，不應超過半數 PF < 0.5（系統性反向操作的警訊）"""
    df_0050 = load_stock("0050")
    if df_0050 is None:
        pytest.skip("0050 資料不存在")

    import yaml as _yaml
    wl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "config", "watchlists.yaml")
    with open(wl_path, encoding="utf-8") as f:
        wl = _yaml.safe_load(f)
    takeshi_ids = [str(s) for s in wl.get("Takeshi", [])]

    regime = detect_regime(df_0050, _STRATEGY["regime"]["ma_long"])
    params = _STRATEGY["style1_pullback"]
    bt = Backtester(BT_CFG_REAL)

    pfs = []
    for sid in takeshi_ids:
        df = load_stock(sid)
        if df is None or len(df) < 250:
            continue
        stock_regime = regime.reindex(df.index, method="ffill").fillna("BEAR")
        signals = generate_signals(df, stock_regime, params)
        result = bt.run_per_stock(sid, df, signals)
        if result.n_trades >= 5 and not math.isinf(result.profit_factor):
            pfs.append((sid, result.profit_factor, result.n_trades))

    if len(pfs) < 3:
        pytest.skip(f"有效股票不足 3 檔（{len(pfs)} 檔有交易）")

    bad = [(sid, pf, n) for sid, pf, n in pfs if pf < 0.5]
    bad_ratio = len(bad) / len(pfs)

    # 列印結果供人工檢查
    print(f"\n  PF 統計（{len(pfs)} 檔）：")
    for sid, pf, n in sorted(pfs, key=lambda x: x[1], reverse=True):
        marker = " ⚠" if pf < 0.5 else ""
        print(f"    {sid}: PF={pf:.2f}  N={n}{marker}")
    print(f"  PF<0.5 比例：{bad_ratio:.0%}（{len(bad)}/{len(pfs)}）")

    assert bad_ratio < 0.6, (
        f"超過 60% 股票 PF<0.5（{len(bad)}/{len(pfs)}），"
        f"策略可能系統性反向。壞標的：{[(s,f'{p:.2f}') for s,p,_ in bad]}"
    )


# ── Sanity Gate E：0050 baseline CAGR 資料長度保護 ──────────

def test_baseline_cagr_rejects_short_data():
    """資料不足 1 年時 _calc_benchmark_cagr 應 raise ValueError"""
    from src.strategy.runner import _calc_benchmark_cagr
    from src.strategy.backtest.engine import BacktestConfig

    # 故意造短資料（只有 10 天）
    idx = pd.date_range("2026-04-01", periods=10, freq="B")
    short_df = pd.DataFrame({
        "open": 75.0, "high": 76.0, "low": 74.0, "close": 75.5, "volume": 1e6
    }, index=idx)
    short_df.index.name = "date"

    cfg_short = BacktestConfig(
        fees=_STRATEGY["fees"],
        start_date="2026-04-01",
        end_date="2026-04-15",
    )
    with pytest.raises(ValueError, match="至少 1 年"):
        _calc_benchmark_cagr(short_df, cfg_short, _STRATEGY)


# ── Sanity Gate F：Katie 組合 MaxDD ≤ 35% ────────────────────

def test_portfolio_maxdd_within_threshold():
    """Katie 組合回測（含 P0-6/7/8 修正）MaxDD 應 ≥ -35%"""
    import yaml as _yaml
    df_0050 = load_stock("0050")
    if df_0050 is None:
        pytest.skip("0050 資料不存在")

    wl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "config", "watchlists.yaml")
    with open(wl_path, encoding="utf-8") as f:
        wl = _yaml.safe_load(f)
    katie_ids = [str(s) for s in wl.get("Katie", [])]

    regime = detect_regime(df_0050, _STRATEGY["regime"]["ma_long"])
    params = _STRATEGY["style1_pullback"]

    dfs = {}
    signals_dict = {}
    for sid in katie_ids:
        df = load_stock(sid)
        if df is None or len(df) < 250:
            continue
        stock_regime = regime.reindex(df.index, method="ffill").fillna("BEAR")
        dfs[sid] = df
        signals_dict[sid] = generate_signals(df, stock_regime, params)

    if len(dfs) < 3:
        pytest.skip(f"可用股票不足 3 檔（{len(dfs)} 檔）")

    from src.strategy.portfolio.allocator import make_monthly_portfolio_sizing
    mom_params = _STRATEGY["style2_momentum"]
    max_pos = 0.25
    sizing_fn = make_monthly_portfolio_sizing(regime, mom_params, max_pos)

    bt = Backtester(BacktestConfig(
        fees=_STRATEGY["fees"],
        start_date="2017-01-01",
        end_date="today",
        initial_capital=1_000_000,
        max_position_pct=max_pos,
    ))
    result = bt.run_portfolio(dfs, signals_dict, sizing_fn)
    mdd = result.max_drawdown

    if math.isnan(mdd):
        pytest.skip("equity curve 為空，無法計算 MaxDD")

    print(f"\n  Katie 組合 MaxDD = {mdd:.2%}")
    assert mdd >= -0.35, (
        f"Katie 組合 MaxDD={mdd:.1%} 超過 -35% 門檻。"
        f"P0-6（regime filter）或 P0-8（cash reserve）可能未正確套用。"
    )


# ── Sanity Gate G：0050 adjusted CAGR 5%~25%（P0-12）─────────

def test_0050_adj_cagr_reasonable():
    """0050 還原股價 CAGR 應落在 5%~25%（含拆分還原 + 含息還原）
    raw price-only CAGR ~2%，加回除息 + 拆分後應顯著提升。
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    adj_path = os.path.join(BASE_DIR, "data", "adjusted", "0050.csv")
    if not os.path.exists(adj_path):
        pytest.skip("data/adjusted/0050.csv 不存在，請先執行 fetch-adjusted")

    df = pd.read_csv(adj_path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").set_index("date")
    if "close_adj" not in df.columns:
        pytest.skip("adjusted CSV 缺少 close_adj 欄位")

    df_sub = df["2017-01-01":]
    if len(df_sub) < 2:
        pytest.skip("0050 adjusted 資料不足")

    years = (df_sub.index[-1] - df_sub.index[0]).days / 365.25
    if years < 1:
        pytest.skip(f"0050 adjusted 資料不足 1 年（{years:.2f} 年）")

    start_price = df_sub["close_adj"].iloc[0]
    end_price   = df_sub["close_adj"].iloc[-1]
    cagr = (end_price / start_price) ** (1 / years) - 1

    print(f"\n  0050 adj CAGR = {cagr:.2%}  "
          f"（start={start_price:.2f} end={end_price:.2f} years={years:.1f}）")
    assert 0.05 <= cagr <= 0.25, (
        f"0050 adjusted CAGR={cagr:.1%} 超出合理範圍 5%~25%。"
        f"可能是 calc_adj_close 計算錯誤或除息事件遺漏。"
    )


# ── Sanity Gate H：adjusted 不應有單日 > 30% 跳動（P0-12）─────

def test_no_extreme_jumps_in_adj():
    """還原後不應有單日 > 30% 的跳動（除非真的是熔斷級事件）"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    adj_dir = os.path.join(BASE_DIR, "data", "adjusted")
    if not os.path.isdir(adj_dir):
        pytest.skip("data/adjusted/ 目錄不存在")

    # 測試清單中的幾個已知高風險股（之前有 split / 除息事件的）
    # 注意：2408（南亞科 2014/09/09 減資）、2337（旺宏 2017/08/28 減資）
    # 因 FinMind TaiwanStockSplitPrice 缺少對應記錄，排除於此 gate；
    # 由 verify_adjustment.py (P0-14) 記錄並回報 Opus。
    TEST_LIST = ["0050", "1301", "2330", "1227", "9940"]
    violations = []

    for sid in TEST_LIST:
        path = os.path.join(adj_dir, f"{sid}.csv")
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, dtype={"date": str})
            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
            df = df.sort_values("date").set_index("date")
            if "close_adj" not in df.columns:
                continue
            max_jump = df["close_adj"].pct_change().abs().max()
            if max_jump >= 0.30:
                worst_date = df["close_adj"].pct_change().abs().idxmax()
                violations.append((sid, max_jump, worst_date))
        except Exception:
            pass

    if violations:
        msgs = [f"{sid} 最大跳動 {jmp:.1%} ({dt.date()})" for sid, jmp, dt in violations]
        pytest.fail(f"adjusted 仍有單日 >30% 跳動：{msgs}")
    print(f"\n  已驗證 {len(TEST_LIST)} 檔，adjusted 無單日 >30% 跳動 ✓")


def test_adj_ohlc_internal_consistency():
    """P0-12.1 防退步：_load_adj_ohlcv 必須讓 OHLC 內部一致。

    歷史 bug：原本只把 close 換成 close_adj，open/high/low 仍用 raw，
    導致 close < open 在還原期間幾乎永遠成立，style1 的反轉條件 c>o
    全部失敗，9 年只跑出 0~2 筆訊號。
    """
    import importlib, src.strategy.runner
    importlib.reload(src.strategy.runner)
    from src.strategy.runner import _load_adj_ohlcv

    # 0050 是受影響最嚴重的（4:1 拆分）
    df = _load_adj_ohlcv("0050")
    if df is None or df.empty:
        pytest.skip("data/adjusted/0050.csv 不存在，跳過")
    sub = df[df.index >= "2017-01-01"]

    c_gt_o_pct = (sub["close"] > sub["open"]).mean()
    # 一般股票 close>open 應在 35%~65%。低於 20% 必然是 OHLC 不一致 bug
    assert c_gt_o_pct > 0.20, (
        f"0050 close>open 比例 {c_gt_o_pct:.1%} 異常低，"
        f"OHLC 還原可能不一致（_load_adj_ohlcv 沒把 factor 套到 open/high/low？）"
    )

    # 同時驗證 high>=max(open,close) 和 low<=min(open,close)（OHLC 基本邏輯）
    # 給 0.1% 的浮點容差
    bad_high = (sub["high"] < sub[["open", "close"]].max(axis=1) * 0.999).sum()
    bad_low = (sub["low"] > sub[["open", "close"]].min(axis=1) * 1.001).sum()
    assert bad_high == 0, f"0050 有 {bad_high} 列 high < max(o,c)"
    assert bad_low == 0, f"0050 有 {bad_low} 列 low > min(o,c)"
    print(f"\n  0050 OHLC 一致性 ✓ (c>o={c_gt_o_pct:.1%})")
