"""Walk-forward 分析：in-sample 優化 → out-of-sample 驗證。"""
import os
import yaml
import numpy as np
import pandas as pd

from src.strategy.optimize.objective import (
    make_objective, run_backtests_for_params, score_results, _make_bt_cfg,
)
from src.strategy.optimize.search_space import SEARCH_SPACE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


def _load_universe(universe_ids: list) -> dict:
    """載入全 universe 的 adj OHLCV（預熱用，保留全期資料）。"""
    from src.strategy.runner import _load_adj_ohlcv
    from src.utils import log_error
    data = {}
    for sid in universe_ids:
        df = _load_adj_ohlcv(sid)
        if df is None or len(df) < 250:
            log_error("optimize", sid, "資料不足 250 日，跳過")
            continue
        data[sid] = df
    return data


def _load_regime(cfg: dict) -> pd.Series:
    """用全期大盤資料計算 regime。"""
    from src.strategy.runner import _load_adj_ohlcv
    from src.strategy.signals.regime import detect_regime
    proxy = cfg.get("regime", {}).get("market_proxy", "0050")
    market_df = _load_adj_ohlcv(proxy)
    if market_df is None:
        return pd.Series(dtype=str)
    return detect_regime(market_df, cfg["regime"]["ma_long"])


def _get_current_params(cfg: dict) -> dict:
    """從 strategy.yaml 取目前的 style1_pullback 參數。"""
    return dict(cfg["style1_pullback"])


def run_walk_forward(
    universe_ids: list,
    n_trials: int,
    train_start: str,
    train_end: str,
    test_start: str,
    test_end: str,
    base_cfg: dict,
    out_dir: str,
) -> dict:
    """執行 walk-forward 優化。回傳結果 dict。"""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    os.makedirs(out_dir, exist_ok=True)

    print(f"  載入 universe 資料（{len(universe_ids)} 檔）...")
    universe_data = _load_universe(universe_ids)
    if not universe_data:
        raise RuntimeError("universe 無可用資料，終止優化。")
    print(f"  可用股票：{len(universe_data)} 檔")

    print(f"  計算大盤 regime...")
    regime = _load_regime(base_cfg)

    fees = base_cfg["fees"]
    train_cfg = _make_bt_cfg(fees, train_start, train_end)
    test_cfg  = _make_bt_cfg(fees, test_start, test_end)

    # ── In-sample 優化 ──────────────────────────────────────────
    print(f"  開始優化（{n_trials} trials，train: {train_start}~{train_end}）...")
    objective_fn = make_objective(universe_data, regime, train_cfg)

    # SQLite checkpointing：落盤、可中斷續跑
    db_path = os.path.join(out_dir, "study.db")
    storage_url = "sqlite:///" + db_path.replace(os.sep, "/")
    study_name = f"style1_{os.path.basename(out_dir)}"

    study = optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(
            n_startup_trials=min(50, n_trials // 3),
            seed=42,
        ),
        load_if_exists=True,
    )
    print(f"  storage: {storage_url}")
    print(f"  即時監看：optuna-dashboard {storage_url}")

    # 只在全新 study（沒任何 trial）時 enqueue current strategy.yaml 參數
    current_params = _get_current_params(base_cfg)
    if len(study.trials) == 0:
        try:
            enqueue_params = {k: current_params[k] for k in SEARCH_SPACE if k in current_params}
            study.enqueue_trial(enqueue_params)
        except Exception:
            pass
    else:
        print(f"  resume 模式：已有 {len(study.trials)} trials，從第 {len(study.trials)+1} 個續跑")

    def _callback(study, trial):
        total = len(study.trials)
        if total % 20 == 0 or trial.number < 5:
            print(f"    trial {trial.number+1:>3}（累計 {total}）  "
                  f"score={trial.value:.4f}  best={study.best_value:.4f}")

    print(f"  本次將執行 {n_trials} trials（study 累計將達 {len(study.trials)+n_trials}）")
    study.optimize(objective_fn, n_trials=n_trials, callbacks=[_callback])

    best_params = dict(study.best_params)
    best_score  = study.best_value

    print(f"\n  最佳 in-sample score = {best_score:.4f}")
    print(f"  最佳參數：{best_params}")

    # ── 儲存 trial log ──────────────────────────────────────────
    trial_rows = []
    for t in study.trials:
        if t.value is not None:
            row = {"trial": t.number, "score": t.value}
            row.update(t.params)
            trial_rows.append(row)
    trial_df = pd.DataFrame(trial_rows)
    trial_log_path = os.path.join(out_dir, "trial_log.csv")
    trial_df.to_csv(trial_log_path, index=False, encoding="utf-8-sig")
    print(f"  trial_log.csv 已儲存（{len(trial_rows)} 筆）")

    # ── 儲存 best_params.yaml ───────────────────────────────────
    best_yaml_path = os.path.join(out_dir, "best_params.yaml")
    with open(best_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump({"style1_pullback": best_params}, f, allow_unicode=True,
                  default_flow_style=False, sort_keys=False)
    print(f"  best_params.yaml 已儲存")

    # ── Per-stock（train） ──────────────────────────────────────
    print(f"  計算 train 段每檔績效...")
    train_df = run_backtests_for_params(best_params, universe_data, regime, train_cfg)
    train_path = os.path.join(out_dir, "per_stock_train.csv")
    train_df.to_csv(train_path, index=False, encoding="utf-8-sig")

    # ── Per-stock（test） ───────────────────────────────────────
    print(f"  計算 test 段每檔績效（out-of-sample）...")
    test_df = run_backtests_for_params(best_params, universe_data, regime, test_cfg)
    test_path = os.path.join(out_dir, "per_stock_test.csv")
    test_df.to_csv(test_path, index=False, encoding="utf-8-sig")

    # ── Walk-forward 對照 ───────────────────────────────────────
    wf_stats = _calc_wf_stats(train_df, test_df)
    wf_path = os.path.join(out_dir, "walk_forward.md")
    _write_walk_forward_md(wf_stats, train_start, train_end, test_start, test_end, wf_path)
    print(f"  walk_forward.md 已儲存")

    # ── Top-5 trials ────────────────────────────────────────────
    top5 = (trial_df.nlargest(5, "score")
            .reset_index(drop=True)
            if len(trial_df) >= 5
            else trial_df.sort_values("score", ascending=False).reset_index(drop=True))

    # ── Summary ─────────────────────────────────────────────────
    summary_path = os.path.join(out_dir, "summary.md")
    _write_summary_md(
        best_params, current_params, wf_stats, top5, study,
        train_start, train_end, test_start, test_end,
        n_trials, summary_path,
    )
    print(f"  summary.md 已儲存")

    return {
        "best_params":   best_params,
        "best_score":    best_score,
        "current_params": current_params,
        "train_df":      train_df,
        "test_df":       test_df,
        "wf_stats":      wf_stats,
        "top5":          top5,
        "study":         study,
        "out_dir":       out_dir,
    }


def _calc_wf_stats(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    def _safe_median_pf(df):
        mask = df["n_trades"] >= 3
        pf = df.loc[mask, "profit_factor"].replace([np.inf, -np.inf], np.nan).dropna()
        return float(pf.median()) if len(pf) > 0 else np.nan

    def _safe_median_dd(df):
        return float(df["max_drawdown"].abs().median())

    def _n_active(df):
        return int((df["n_trades"] >= 3).sum())

    return {
        "train_median_pf":  _safe_median_pf(train_df),
        "train_median_dd":  _safe_median_dd(train_df),
        "train_n_active":   _n_active(train_df),
        "test_median_pf":   _safe_median_pf(test_df),
        "test_median_dd":   _safe_median_dd(test_df),
        "test_n_active":    _n_active(test_df),
    }


def _write_walk_forward_md(stats: dict, train_start, train_end,
                            test_start, test_end, path: str):
    tr = stats
    lines = [
        "# Walk-Forward 對照\n",
        f"| 指標 | Train ({train_start}~{train_end}) | Test ({test_start}~{test_end}) | 衰減 |",
        "|---|---|---|---|",
    ]

    def decay(a, b):
        if np.isnan(a) or np.isnan(b) or a == 0:
            return "N/A"
        return f"{(b/a - 1):.1%}"

    lines.append(f"| median PF    | {tr['train_median_pf']:.3f} | {tr['test_median_pf']:.3f} | {decay(tr['train_median_pf'], tr['test_median_pf'])} |")
    lines.append(f"| median MaxDD | {tr['train_median_dd']:.1%} | {tr['test_median_dd']:.1%} | {decay(tr['train_median_dd'], tr['test_median_dd'])} |")
    lines.append(f"| n_active     | {tr['train_n_active']} | {tr['test_n_active']} | — |")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _write_summary_md(
    best_params, current_params, wf_stats, top5,
    study, train_start, train_end, test_start, test_end,
    n_trials, path,
):
    tr = wf_stats
    lines = ["# 優化結果 Summary\n"]

    # 最佳 vs 目前參數對照
    lines += [
        "## 最佳參數 vs 目前 strategy.yaml 對照",
        "",
        "| 參數 | 目前值 | 最佳值 | 變化 |",
        "|---|---|---|---|",
    ]
    for k in sorted(set(list(best_params.keys()) + list(current_params.keys()))):
        cur = current_params.get(k, "—")
        best = best_params.get(k, "—")
        changed = "✓ 變化" if str(cur) != str(best) else "—"
        lines.append(f"| {k} | {cur} | {best} | {changed} |")
    lines.append("")

    # In-sample vs Out-of-sample
    lines += [
        "## In-Sample vs Out-of-Sample",
        "",
        f"| 指標 | Train ({train_start}~{train_end}) | Test ({test_start}~{test_end}) | 衰減 |",
        "|---|---|---|---|",
    ]

    def decay(a, b):
        if np.isnan(a) or np.isnan(b) or a == 0:
            return "N/A"
        return f"{(b/a - 1):.1%}"

    lines.append(f"| median PF    | {tr['train_median_pf']:.3f} | {tr['test_median_pf']:.3f} | {decay(tr['train_median_pf'], tr['test_median_pf'])} |")
    lines.append(f"| median MaxDD | {tr['train_median_dd']:.1%} | {tr['test_median_dd']:.1%} | {decay(tr['train_median_dd'], tr['test_median_dd'])} |")
    lines.append(f"| n_active     | {tr['train_n_active']} | {tr['test_n_active']} | — |")
    lines.append("")

    # Overfit 警訊
    overfit_flag = False
    if not np.isnan(tr["train_median_pf"]) and not np.isnan(tr["test_median_pf"]) and tr["train_median_pf"] > 0:
        if tr["test_median_pf"] < tr["train_median_pf"] * 0.5:
            overfit_flag = True

    # Top-5 穩定性
    top5_scores = top5["score"].tolist() if len(top5) >= 2 else []
    sensitive_flag = False
    if len(top5_scores) >= 2:
        if (top5_scores[0] - top5_scores[-1]) / abs(top5_scores[0]) > 0.30:
            sensitive_flag = True

    lines += [
        "## Overfit 警訊",
        "",
        f"- out-of-sample < in-sample × 0.5：{'**是，可能 overfit**' if overfit_flag else '否'}",
        f"- top-5 score 差距 > 30%：{'**是，敏感性高，挑次優更穩**' if sensitive_flag else '否'}",
        "",
    ]

    # Top-5 對照
    lines += ["## 前 5 名 Trial 對照（穩定性）", ""]
    if not top5.empty:
        param_cols = [c for c in top5.columns if c not in ("trial", "score")]
        header = "| trial | score | " + " | ".join(param_cols) + " |"
        sep = "|---|---|" + "|".join(["---"] * len(param_cols)) + "|"
        lines += [header, sep]
        for _, row in top5.iterrows():
            vals = " | ".join(str(row.get(c, "—")) for c in param_cols)
            lines.append(f"| {int(row['trial'])} | {row['score']:.4f} | {vals} |")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
