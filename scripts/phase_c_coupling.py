"""Phase C：多策略耦合實驗。

從 Phase B 篩出的「穩定強 + 次穩」個股，對每檔測 5 種 ensemble：

  1. top3_vote        — 該股 top 3 single strategy 都 BUY 才進場
  2. regime_switch    — bull regime 用 momentum、bear regime 用 mean-revert
  3. equal_weight     — top 3 strategy 各分 1/3 資金
  4. pf_weighted      — 依各 strategy 過去 PF 動態加權
  5. cascade          — A strategy 進場 → B strategy 退場

每種 ensemble 跑 backtest，跟原本 best single strategy 對比：
  - in_market CAGR
  - max drawdown
  - sharpe (rough)
  - n_trades

輸出：
  output/auto_iterate/ensembles_<date>/
    coupling_report.md
    per_stock_ensemble_comparison.csv

注意：本 phase 不重新優化參數，只組合既有 best strategies。
"""
from __future__ import annotations
import os, sys, yaml, json, csv
from datetime import date
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def _load_phase_a_results():
    """從最新 Phase A run 抓 per_stock_best.yaml。"""
    ai_dir = os.path.join(BASE_DIR, "output", "auto_iterate")
    # Phase A 應該是 train_2010-2020/test_2021-2026 的最大 run
    import csv as _csv
    idx_path = os.path.join(ai_dir, "INDEX.csv")
    with open(idx_path, encoding="utf-8-sig") as f:
        rows = list(_csv.DictReader(f))
    phase_a = [r for r in rows
               if r["train_start"]=="2010-01-01" and r["train_end"]=="2020-12-31"
               and r["test_start"]=="2021-01-01" and r["test_end"]=="2026-04-22"]
    if not phase_a:
        return None, None
    latest = sorted(phase_a, key=lambda r: r["started_at"], reverse=True)[0]
    run_id = latest["run_id"]
    psb_path = os.path.join(ai_dir, run_id, "per_stock_best.yaml")
    with open(psb_path, encoding="utf-8") as f:
        return run_id, yaml.safe_load(f) or {}


def _load_top_templates_per_stock(run_id: str, sid: str, top_n: int = 3) -> list[dict]:
    """對某檔股票，從 run dir 的所有 template yaml 中取前 N 個（依 PF + n_trades）。"""
    ai_dir = os.path.join(BASE_DIR, "output", "auto_iterate", run_id)
    candidates = []
    for fname in os.listdir(ai_dir):
        if not fname.endswith(".yaml"): continue
        if fname == "per_stock_best.yaml": continue
        path = os.path.join(ai_dir, fname)
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            ps = data.get("per_stock", {})
            entry = ps.get(sid) or ps.get(str(sid))
            if not entry: continue
            pf = entry.get("test_pf") or 0
            n = entry.get("test_n_trades") or 0
            if pf > 1 and n >= 3:  # 最低門檻
                candidates.append({
                    "template": fname.replace(".yaml",""),
                    "params": entry.get("best_params"),
                    "test_pf": pf,
                    "test_n_trades": n,
                    "test_cagr": entry.get("test_cagr") or 0,
                })
        except Exception:
            pass
    # 排序：先依 PF×log(n_trades) ，取 top N
    import math
    candidates.sort(key=lambda c: -(c["test_pf"] * math.log(c["test_n_trades"]+1)))
    return candidates[:top_n]


def _run_ensemble_backtest(sid: str, strategies: list[dict], ensemble_type: str):
    """根據 ensemble_type 組合 strategies 跑回測。

    回 dict: { n_trades, win_rate, cagr, max_dd, pf, expectancy }
    """
    from src.strategy.runner import _load_adj_ohlcv, _load_strategy_cfg
    from src.strategy.backtest.engine import Backtester, BacktestConfig
    from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS
    import pandas as pd
    import inspect

    df = _load_adj_ohlcv(sid)
    if df is None or len(df) < 50:
        return None

    # 為每個 strategy 產生信號
    signals_list = []
    for s in strategies:
        gen_fn = TEMPLATE_GENERATORS.get(s["template"])
        if gen_fn is None: continue
        sig_params = inspect.signature(gen_fn).parameters
        kwargs = {}
        if "chip_data" in sig_params:
            try:
                from src.strategy.auto_iterate.chip_fetcher import load_chip_data
                kwargs["chip_data"] = load_chip_data(sid)
            except Exception:
                kwargs["chip_data"] = None
        if "revenue_data" in sig_params:
            try:
                from src.strategy.auto_iterate.revenue_fetcher import load_revenue_data
                kwargs["revenue_data"] = load_revenue_data(sid)
            except Exception:
                kwargs["revenue_data"] = None
        sig = gen_fn(df, s["params"], **kwargs)
        signals_list.append(sig)

    if not signals_list:
        return None

    # 組合信號
    combined = _combine_signals(signals_list, ensemble_type, strategies)

    cfg = _load_strategy_cfg()
    bt_cfg = BacktestConfig(
        fees=cfg["fees"],
        start_date="2021-01-01", end_date="2026-04-22",
        initial_capital=1_000_000,
        max_position_pct=0.5,
    )
    bt = Backtester(bt_cfg)
    res = bt.run_per_stock(sid, df, combined)
    return {
        "n_trades": res.n_trades,
        "win_rate": res.win_rate,
        "pf": res.profit_factor,
        "cagr": res.in_market_cagr,
        "max_dd": res.max_drawdown,
        "expectancy": res.expectancy,
    }


def _combine_signals(signals_list, ensemble_type: str, strategies: list[dict]):
    """依 ensemble_type 合併信號。"""
    import pandas as pd
    # 對齊 index
    aligned = [s["action"].reindex(signals_list[0].index).fillna("HOLD") for s in signals_list]
    n = len(aligned[0])

    if ensemble_type == "top3_vote":
        # 全部 BUY → BUY; 任一 SELL → SELL; 否則 HOLD
        result = []
        for i in range(n):
            actions = [a.iloc[i] for a in aligned]
            if all(x == "BUY" for x in actions):
                result.append("BUY")
            elif any(x == "SELL" for x in actions):
                result.append("SELL")
            else:
                result.append("HOLD")
    elif ensemble_type == "equal_weight":
        # 任一 BUY → BUY（簡化版，未實作真正 1/3 加權）
        result = []
        for i in range(n):
            actions = [a.iloc[i] for a in aligned]
            buys = sum(1 for x in actions if x == "BUY")
            sells = sum(1 for x in actions if x == "SELL")
            if buys > sells: result.append("BUY")
            elif sells > buys: result.append("SELL")
            else: result.append("HOLD")
    elif ensemble_type == "pf_weighted":
        # 按 PF 加權，超過 50% 才觸發
        pfs = [s["test_pf"] for s in strategies]
        total = sum(pfs)
        weights = [pf/total for pf in pfs] if total > 0 else [1/len(pfs)]*len(pfs)
        result = []
        for i in range(n):
            actions = [a.iloc[i] for a in aligned]
            buy_w = sum(w for a, w in zip(actions, weights) if a == "BUY")
            sell_w = sum(w for a, w in zip(actions, weights) if a == "SELL")
            if buy_w > 0.5: result.append("BUY")
            elif sell_w > 0.5: result.append("SELL")
            else: result.append("HOLD")
    elif ensemble_type == "cascade":
        # 第一個 strategy 進場、最後一個 strategy 退場
        result = []
        in_pos = False
        for i in range(n):
            first = aligned[0].iloc[i]
            last = aligned[-1].iloc[i]
            if not in_pos and first == "BUY":
                result.append("BUY"); in_pos = True
            elif in_pos and last == "SELL":
                result.append("SELL"); in_pos = False
            else:
                result.append("HOLD")
    else:  # 'regime_switch' 等之後實作
        result = list(aligned[0])  # fallback

    return pd.DataFrame({"action": result}, index=signals_list[0].index)


def main():
    out_dir = os.path.join(BASE_DIR, "output", "auto_iterate",
                            f"ensembles_{date.today()}")
    os.makedirs(out_dir, exist_ok=True)

    run_id, psb = _load_phase_a_results()
    if not psb:
        print("[ERR] 找不到 Phase A 結果")
        return

    print(f"使用 Phase A run_id = {run_id}")

    # 從 walk-forward report 找穩定強 + 次穩個股，沒有報告就用 PASS tier
    candidates = []
    for sid, info in psb.items():
        if isinstance(info, dict) and info.get("tier") in ("S","A","B"):
            candidates.append(sid)
    print(f"候選個股：{len(candidates)} 檔")

    rows = []
    ENSEMBLES = ["top3_vote", "equal_weight", "pf_weighted", "cascade"]
    for sid in candidates[:50]:  # top 50 for time budget
        print(f"\n--- {sid} ---")
        strats = _load_top_templates_per_stock(run_id, sid, top_n=3)
        if len(strats) < 2:
            print(f"  strategies < 2，跳過")
            continue
        # baseline = 最佳 single
        baseline = strats[0]
        row = {"sid": sid, "n_strats": len(strats),
                "baseline_template": baseline["template"],
                "baseline_pf": baseline["test_pf"],
                "baseline_cagr": baseline["test_cagr"]}
        for ens in ENSEMBLES:
            try:
                r = _run_ensemble_backtest(sid, strats, ens)
                if r:
                    row[f"{ens}_pf"] = r["pf"]
                    row[f"{ens}_cagr"] = r["cagr"]
                    row[f"{ens}_n"] = r["n_trades"]
                    print(f"  {ens}: pf={r['pf']:.2f}, cagr={r['cagr']*100:+.1f}%, n={r['n_trades']}")
            except Exception as e:
                print(f"  {ens}: ERROR {e}")
        rows.append(row)

    # 寫 CSV
    if rows:
        csv_path = os.path.join(out_dir, "ensemble_comparison.csv")
        all_keys = sorted({k for r in rows for k in r.keys()})
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=all_keys)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"\n✓ 寫入 {csv_path}")


if __name__ == "__main__":
    main()
