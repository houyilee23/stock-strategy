"""24 hr heavy retrain controller — Phase A + B + C 自動串接。

Phase A (~12 hr): 大批量重訓
  Train 2010-2020 / Test 2021-2026
  全 universe (data/adjusted/ 所有股) × 全 65 templates × 100 trials

Phase B (~6 hr): Walk-forward 3 folds
  Fold 1: Train 2010-2014 / Test 2015-2017 (含 2015 中港股災)
  Fold 2: Train 2010-2017 / Test 2018-2020 (含 2018-19 貿易戰)
  Fold 3: Train 2010-2020 / Test 2021-2023 (含 COVID 高峰)
  每 fold: top 100 stocks (from Phase A) × 30 best templates × 100 trials

Phase C (~6 hr): Multi-strategy 耦合實驗
  Top 50 by Phase B 穩定度 × 5 種 ensemble 策略 × 100 trials
  寫 docs/training_log/ensembles_<date>.md

各階段完成都會：
  - 更新 output/auto_iterate/INDEX.csv
  - 寫 docs/training_log/<date>_phase_X_report.md
  - 不直接套用 recommendations.yaml（等使用者驗證再 apply）

用法：
  python scripts/heavy_retrain_24hr.py             # 全程跑
  python scripts/heavy_retrain_24hr.py --phase A   # 只跑 Phase A
  python scripts/heavy_retrain_24hr.py --wait-pilot output/auto_iterate/20260519_210501
"""
from __future__ import annotations
import argparse, os, sys, subprocess, time
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)


def wait_pilot(pilot_run_id: str, timeout_min: int = 120):
    """等待指定 pilot run 完成（出現 summary.md）。"""
    summary = os.path.join(BASE_DIR, "output", "auto_iterate",
                           pilot_run_id.split("/")[-1], "summary.md")
    log(f"等待 pilot 完成：{summary}")
    start = time.time()
    while not os.path.exists(summary):
        if (time.time() - start) > timeout_min * 60:
            log(f"等 {timeout_min} 分鐘還沒完成，強制繼續")
            break
        time.sleep(60)
    log(f"pilot 完成或 timeout → 開始 Phase A")


def phase_a():
    log("\n" + "="*64)
    log("  PHASE A : 大批量重訓（Train 2010-2020 / Test 2021-2026）")
    log("="*64)
    started = datetime.now()
    cmd = [
        sys.executable, "main.py", "auto_iterate",
        "--trials-per-pair", "100",
        "--timeout-per-pair", "300",
        "--train-start", "2010-01-01",
        "--train-end",   "2020-12-31",
        "--test-start",  "2021-01-01",
        "--test-end",    "2026-04-22",
        "--universe",    "all",
        "--wide-search",
    ]
    log(f"指令：{' '.join(cmd)}")
    rc = subprocess.call(cmd, cwd=BASE_DIR)
    elapsed = (datetime.now() - started).total_seconds() / 3600
    log(f"Phase A 完成（rc={rc}，{elapsed:.1f} hr）")

    # 更新 INDEX + 寫 report
    subprocess.call([sys.executable, "scripts/build_run_index.py"], cwd=BASE_DIR)
    _write_phase_report("A", started, datetime.now(), rc)
    return rc


def phase_b():
    """3 folds 跑 walk-forward。每 fold 用 top 100 by Phase A pass。"""
    log("\n" + "="*64)
    log("  PHASE B : Walk-forward 3 folds")
    log("="*64)

    folds = [
        ("fold1", "2010-01-01", "2014-12-31", "2015-01-01", "2017-12-31"),
        ("fold2", "2010-01-01", "2017-12-31", "2018-01-01", "2020-12-31"),
        ("fold3", "2010-01-01", "2020-12-31", "2021-01-01", "2023-12-31"),
    ]

    # 從 Phase A 結果取 top 100 stocks（PASS template 數 ≥ 2 的）
    top100 = _pick_top_stocks_from_phase_a(n=100)
    log(f"從 Phase A 挑出 {len(top100)} 檔做 walk-forward 驗證")

    for name, ts, te, vs, ve in folds:
        started = datetime.now()
        log(f"\n--- {name}: Train {ts} ~ {te}, Test {vs} ~ {ve} ---")
        cmd = [
            sys.executable, "main.py", "auto_iterate",
            "--trials-per-pair", "100",
            "--timeout-per-pair", "300",
            "--train-start", ts, "--train-end", te,
            "--test-start",  vs, "--test-end",  ve,
            "--universe",    ",".join(top100),
        ]
        rc = subprocess.call(cmd, cwd=BASE_DIR)
        elapsed = (datetime.now() - started).total_seconds() / 3600
        log(f"  {name} 完成（rc={rc}，{elapsed:.1f} hr）")

    subprocess.call([sys.executable, "scripts/build_run_index.py"], cwd=BASE_DIR)

    # 寫 walk-forward 跨 fold 對比報告
    _write_walk_forward_report()


def phase_c():
    """Multi-strategy 耦合：對每檔 Phase B 篩出的穩定 stock 設計 ensemble。"""
    log("\n" + "="*64)
    log("  PHASE C : Multi-strategy 耦合實驗")
    log("="*64)
    started = datetime.now()

    # Phase C 主要是 design + backtest，沒有 Optuna 搜索
    # 用獨立 script 跑
    cmd = [sys.executable, "scripts/phase_c_coupling.py"]
    rc = subprocess.call(cmd, cwd=BASE_DIR)
    elapsed = (datetime.now() - started).total_seconds() / 3600
    log(f"Phase C 完成（rc={rc}，{elapsed:.1f} hr）")
    _write_phase_report("C", started, datetime.now(), rc)


def _pick_top_stocks_from_phase_a(n: int) -> list[str]:
    """從最新 Phase A run dir 抓 PASS/PASS-rate 高的 top n stock_id。"""
    import yaml
    ai_dir = os.path.join(BASE_DIR, "output", "auto_iterate")
    candidates = sorted([d for d in os.listdir(ai_dir)
                         if d.startswith("2026") and not d.startswith("merged_")],
                        reverse=True)
    if not candidates:
        return []
    latest = candidates[0]
    psb_path = os.path.join(ai_dir, latest, "per_stock_best.yaml")
    if not os.path.exists(psb_path):
        log(f"  Phase A 結果未找到 per_stock_best.yaml，fallback 用 watchlist")
        # Fallback: 用 data/adjusted/ 全部
        adj_dir = os.path.join(BASE_DIR, "data", "adjusted")
        return sorted([f[:-4] for f in os.listdir(adj_dir) if f.endswith(".csv")])[:n]

    with open(psb_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # 排序：tier S/A/B 優先，再 test_cagr 高
    tier_order = {"S":0,"A":1,"B":2,"C":3,"D":4,"F":9,"?":9}
    items = [(sid, info) for sid, info in data.items() if isinstance(info, dict)]
    items.sort(key=lambda x: (tier_order.get(x[1].get("tier","?"), 9),
                                -((x[1].get("test_cagr") or 0))))
    return [sid for sid, _ in items[:n]]


def _write_phase_report(phase: str, start: datetime, end: datetime, rc: int):
    log_dir = os.path.join(BASE_DIR, "docs", "training_log")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"{start.strftime('%Y-%m-%d')}_heavy_retrain.md")
    elapsed_min = (end - start).total_seconds() / 60
    section = []
    section.append(f"\n## Phase {phase} ({start.strftime('%H:%M')} → {end.strftime('%H:%M')})")
    section.append(f"  - 耗時：{elapsed_min:.0f} 分鐘")
    section.append(f"  - 結束碼：rc={rc}")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# 24-hr Heavy Retrain — {start.strftime('%Y-%m-%d')}\n")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(section) + "\n")


def _write_walk_forward_report():
    """跨 3 fold 的 robustness 對比。"""
    log("寫 walk-forward 跨 fold 對比報告 → docs/training_log/")
    # 細節之後在 scripts/walk_forward_analysis.py 寫
    rc = subprocess.call([sys.executable, "scripts/walk_forward_analysis.py"],
                         cwd=BASE_DIR)
    if rc != 0:
        log(f"  ⚠ walk_forward_analysis.py 不存在或失敗（rc={rc}），跳過")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=["all","A","B","C"])
    ap.add_argument("--wait-pilot", default=None,
                    help="先等指定 pilot run 完成再啟動 Phase A")
    args = ap.parse_args()

    overall_start = datetime.now()
    log(f"==================================")
    log(f" 24-hr heavy retrain controller")
    log(f"==================================")
    log(f"開始時間：{overall_start.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.wait_pilot:
        wait_pilot(args.wait_pilot)

    if args.phase in ("all", "A"):
        phase_a()
    if args.phase in ("all", "B"):
        phase_b()
    if args.phase in ("all", "C"):
        phase_c()

    elapsed = (datetime.now() - overall_start).total_seconds() / 3600
    log(f"\n==================================")
    log(f" 全程結束：{elapsed:.1f} hr")
    log(f"==================================")


if __name__ == "__main__":
    main()
