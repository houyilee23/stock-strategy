"""optimize 子命令入口：解析 CLI args → 跑 walk-forward → 儲存所有輸出。"""
import os
import time
import numpy as np
import yaml
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


def _load_base_cfg() -> dict:
    path = os.path.join(BASE_DIR, "config", "strategy.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _resolve_universe(universe_arg: str) -> list:
    """解析 --universe 參數。
    all      → 掃 data/adjusted/ 全部
    research → Takeshi watchlist
    <sids>   → 逗號分隔的股票代號
    """
    adj_dir = os.path.join(BASE_DIR, "data", "adjusted")
    if universe_arg in (None, "all"):
        ids = sorted(f[:-4] for f in os.listdir(adj_dir) if f.endswith(".csv"))
        print(f"  --universe all：{len(ids)} 檔")
        return ids
    if universe_arg == "research":
        import yaml as _yaml
        wl_path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
        with open(wl_path, encoding="utf-8") as f:
            wl = _yaml.safe_load(f) or {}
        ids = [str(s) for s in wl.get("Takeshi", [])]
        print(f"  --universe research（Takeshi）：{len(ids)} 檔")
        return ids
    # 逗號分隔
    ids = [s.strip() for s in universe_arg.split(",") if s.strip()]
    print(f"  --universe 指定：{ids}")
    return ids


def run_optimize(
    style: str = "style1_pullback",
    n_trials: int = 300,
    train_end: str = "2022-12-31",
    test_start: str = "2023-01-01",
    train_start: str = "2017-01-01",
    test_end: str = "2026-04-22",
    universe_arg: str = "all",
    resume_run_id: str = None,
) -> None:
    from src.strategy.optimize.walk_forward import run_walk_forward

    if style != "style1_pullback":
        print(f"[錯誤] 目前只支援 style1_pullback，收到：{style}")
        return

    if resume_run_id:
        run_id = resume_run_id
        out_dir = os.path.join(BASE_DIR, "output", "optimize", run_id)
        db_check = os.path.join(out_dir, "study.db")
        if not os.path.exists(db_check):
            print(f"[錯誤] 找不到 {db_check}，無法 resume")
            return
        print(f"  → RESUME 模式 from run_id={run_id}")
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(BASE_DIR, "output", "optimize", run_id)

    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  Optimize Run  {run_id}")
    print(f"  Style:  {style}")
    print(f"  Trials: {n_trials}")
    print(f"  Train:  {train_start} ~ {train_end}")
    print(f"  Test:   {test_start} ~ {test_end}")
    print(f"  Output: {out_dir}")
    print(f"{'='*70}\n")

    universe_ids = _resolve_universe(universe_arg)
    if not universe_ids:
        print("[錯誤] universe 為空，中止。")
        return

    base_cfg = _load_base_cfg()

    t0 = time.time()
    result = run_walk_forward(
        universe_ids=universe_ids,
        n_trials=n_trials,
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
        base_cfg=base_cfg,
        out_dir=out_dir,
    )
    elapsed = time.time() - t0

    # ── 產 Opus 報告 ────────────────────────────────────────────
    _write_opus_report(result, run_id, n_trials, elapsed, out_dir)

    print(f"\n{'='*70}")
    print(f"  優化完成！耗時 {elapsed/60:.1f} 分鐘")
    print(f"  run_id = {run_id}")
    print(f"  輸出目錄：{out_dir}")
    print(f"{'='*70}")


def _write_opus_report(result: dict, run_id: str, n_trials: int,
                        elapsed: float, out_dir: str):
    tr = result["wf_stats"]
    best = result["best_params"]
    cur = result["current_params"]
    top5 = result["top5"]
    best_score = result["best_score"]

    # 計算 test score（直接用 score_results）
    from src.strategy.optimize.objective import score_results
    test_score = score_results(result["test_df"], len(result["test_df"]))

    overfit_flag = False
    if (not np.isnan(tr["train_median_pf"]) and not np.isnan(tr["test_median_pf"])
            and tr["train_median_pf"] > 0):
        if tr["test_median_pf"] < tr["train_median_pf"] * 0.5:
            overfit_flag = True

    top5_scores = top5["score"].tolist() if len(top5) >= 2 else []
    sensitive_flag = (len(top5_scores) >= 2 and
                      (top5_scores[0] - top5_scores[-1]) / abs(top5_scores[0] + 1e-9) > 0.30)

    # 建議套用？
    params_changed = sum(1 for k in best if str(best.get(k)) != str(cur.get(k, "")))
    recommend = (not overfit_flag and not np.isnan(tr["test_median_pf"])
                 and tr["test_median_pf"] > 1.0 and tr["test_n_active"] >= 3)

    lines = [
        "# Optimize Round 1 報告\n",
        "## TL;DR",
        f"- 跑了 {n_trials} trials，耗時 {elapsed/60:.1f} 分鐘",
        f"- 最佳 in-sample score = {best_score:.4f}，out-of-sample score = {test_score:.4f}",
        f"- overfit 警訊：{'有' if overfit_flag else '無'}",
        f"- 建議套用 best_params：{'是' if recommend else '否'}（理由見下方）",
        "",
        "## 最佳參數 diff",
        "",
        "| 參數 | 目前 | 最佳 | 變化 |",
        "|---|---|---|---|",
    ]
    for k in sorted(set(list(best.keys()) + list(cur.keys()))):
        c = cur.get(k, "—")
        b = best.get(k, "—")
        changed = "✓" if str(c) != str(b) else ""
        lines.append(f"| {k} | {c} | {b} | {changed} |")
    lines.append("")

    lines += [
        "## In-Sample vs Out-of-Sample",
        "",
        f"| 指標 | Train (2017-2022) | Test (2023-2026) | 衰減 |",
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

    lines += ["## Top-5 Trial 對照", ""]
    if not top5.empty:
        param_cols = [c for c in top5.columns if c not in ("trial", "score")]
        header = "| trial | score | " + " | ".join(param_cols) + " |"
        sep = "|---|---|" + "|".join(["---"] * len(param_cols)) + "|"
        lines += [header, sep]
        for _, row in top5.iterrows():
            vals = " | ".join(str(row.get(c, "—")) for c in param_cols)
            lines.append(f"| {int(row['trial'])} | {row['score']:.4f} | {vals} |")
    lines.append("")

    lines += [
        "## 我的判斷",
        "",
        f"- overfit 警訊：{'**有（test < train × 0.5）**' if overfit_flag else '無'}",
        f"- top-5 敏感性：{'**高（差距 >30%）**' if sensitive_flag else '低（穩定）'}",
        f"- 參數差異：共 {params_changed} 個參數與目前 strategy.yaml 不同",
        "",
    ]

    if recommend:
        lines += [
            "- 建議：**套用 best_params 到 strategy.yaml**",
            "  - out-of-sample 績效穩健（median PF > 1.0，n_active 充足）",
            "  - 無明顯 overfit 警訊",
            f"  - 詳細參數見 {out_dir}/best_params.yaml",
        ]
    else:
        reasons = []
        if overfit_flag:
            reasons.append("out-of-sample 績效衰減超過 50%，有 overfit 風險")
        if np.isnan(tr["test_median_pf"]) or tr["test_median_pf"] <= 1.0:
            reasons.append(f"out-of-sample median PF = {tr['test_median_pf']:.3f} ≤ 1.0，策略無正期望")
        if tr["test_n_active"] < 3:
            reasons.append(f"test 段只有 {tr['test_n_active']} 檔有效交易，樣本不足")
        reasons_str = "；".join(reasons) if reasons else "謹慎觀察"
        lines += [
            "- 不建議：**暫不套用 best_params**",
            f"  - 原因：{reasons_str}",
            "  - 建議：繼續收集資料，下次優化加入更多歷史或調整 search_space",
        ]

    lines += [
        "",
        "## 下一步",
        "- 人工 review best_params.yaml，決定是否手動套入 config/strategy.yaml",
        "- 若套用後跑 `python main.py backtest --all` 驗證全 universe 效果",
        f"- 本次 run_id：`{run_id}`",
    ]

    # 寫到 docs/
    docs_path = os.path.join(BASE_DIR, "docs", "OPTIMIZE_REPORT_TO_OPUS.md")
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  OPTIMIZE_REPORT_TO_OPUS.md 已寫入：{docs_path}")
