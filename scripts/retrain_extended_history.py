"""啟動「擴大歷史區間」的 auto_iterate retrain。

目的：把 2010-2016 也納入訓練/回測。
原訓練視窗 2017-01-01 ~ 2023-12-31 完全錯過 2011 歐債、2015 中港股災、
2018-2019 小空頭，是 docs/TODO_RETRAIN.md 早就標記的「過度樂觀近期 fit」問題。

新視窗：
  Train 2010-01-01 ~ 2020-12-31  (11 年，含 2011/2015/2018-19 三段壓力)
  Test  2021-01-01 ~ 2026-04-22  (5.3 年 OOS)

跑完後會：
  1. 自動跑 scripts/build_run_index.py 更新 INDEX.csv/md
  2. 寫入 docs/training_log/<date>.md 紀錄這次跑了什麼、結果分佈
  3. (option) 用 scripts/compare_recommendations.py 比較跟舊 recommendations
     的差異

用法（背景跑數小時，建議用 daily_update.bat 排程方式 chaining）：

  python scripts/retrain_extended_history.py                       # 全 universe × 全 templates
  python scripts/retrain_extended_history.py --pilot               # 只跑 Takeshi list 取代驗證可行
  python scripts/retrain_extended_history.py --trials 100          # 改 trials per pair
  python scripts/retrain_extended_history.py --templates T1,T4     # 只跑特定 templates
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-start", default="2010-01-01")
    ap.add_argument("--train-end",   default="2020-12-31")
    ap.add_argument("--test-start",  default="2021-01-01")
    ap.add_argument("--test-end",    default="2026-04-22")
    ap.add_argument("--trials",      default="100",
                    help="trials per (stock, template) pair（預設 100，原 80 → 100 為了擴大 search space）")
    ap.add_argument("--timeout",     default="300",
                    help="每對 timeout 秒數")
    ap.add_argument("--pilot",       action="store_true",
                    help="只跑 Takeshi list 26 檔（快速驗證）")
    ap.add_argument("--universe",    default="all",
                    help='universe 指定：all / 逗號分隔 sid / "all" 預設')
    ap.add_argument("--templates",   default=None,
                    help="逗號分隔 template 名稱或 T1/T4 等簡稱；省略=全部")
    ap.add_argument("--wide-search", action="store_true",
                    help="啟用 wide-search（搜尋空間擴大版）")
    ap.add_argument("--resume",      default=None,
                    help="續跑指定 run_id")
    ap.add_argument("--no-update-index", action="store_true",
                    help="跑完不要自動更新 INDEX.csv")
    args = ap.parse_args()

    # 決定 universe
    if args.pilot:
        universe = "Takeshi"  # main.py auto_iterate 不支援 list name？要查
        # 改成讀 watchlist 後傳逗號分隔
        import yaml
        with open(os.path.join(BASE_DIR, "config", "watchlists.yaml"),
                  encoding="utf-8") as f:
            wl = yaml.safe_load(f) or {}
        universe = ",".join(str(s) for s in (wl.get("Takeshi") or []))
        print(f"[pilot] universe = Takeshi ({len(wl.get('Takeshi') or [])} 檔)")
    else:
        universe = args.universe

    # 組 main.py auto_iterate command
    cmd = [
        sys.executable, "main.py", "auto_iterate",
        "--trials-per-pair", args.trials,
        "--timeout-per-pair", args.timeout,
        "--train-start", args.train_start,
        "--train-end",   args.train_end,
        "--test-start",  args.test_start,
        "--test-end",    args.test_end,
        "--universe",    universe,
    ]
    if args.templates:
        cmd += ["--templates", args.templates]
    if args.wide_search:
        cmd += ["--wide-search"]
    if args.resume:
        cmd += ["--resume", args.resume]

    print(f"\n{'='*64}")
    print(f"  擴大歷史區間 retrain")
    print(f"  Train: {args.train_start} ~ {args.train_end}")
    print(f"  Test : {args.test_start} ~ {args.test_end}")
    print(f"  Trials per pair: {args.trials}")
    if args.pilot:
        print(f"  [PILOT MODE] 只跑 Takeshi list")
    print(f"{'='*64}\n")
    print(f"指令: {' '.join(cmd)}\n")

    started_at = datetime.now()
    rc = subprocess.call(cmd, cwd=BASE_DIR)
    ended_at = datetime.now()
    elapsed = (ended_at - started_at).total_seconds() / 60.0

    print(f"\n{'='*64}")
    print(f"  完成（rc={rc}，耗時 {elapsed:.1f} 分鐘）")
    print(f"{'='*64}\n")

    # 自動更新 INDEX
    if not args.no_update_index:
        print("更新 INDEX.csv / INDEX.md ...")
        subprocess.call([sys.executable, os.path.join("scripts", "build_run_index.py")],
                        cwd=BASE_DIR)

    # 寫 training log
    _write_training_log(args, rc, started_at, ended_at, elapsed)


def _write_training_log(args, rc: int, start, end, elapsed_min: float):
    """寫一筆 training log 到 docs/training_log/YYYY-MM-DD.md（append）。"""
    log_dir = os.path.join(BASE_DIR, "docs", "training_log")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{start.strftime('%Y-%m-%d')}.md")

    section = []
    section.append(f"## {start.strftime('%H:%M:%S')} — Extended-history retrain")
    section.append("")
    section.append(f"- 結束時間：{end.strftime('%H:%M:%S')}（耗時 {elapsed_min:.1f} 分）")
    section.append(f"- 結束碼：rc={rc}")
    section.append(f"- Train：{args.train_start} ~ {args.train_end}")
    section.append(f"- Test：{args.test_start} ~ {args.test_end}")
    section.append(f"- Trials/pair：{args.trials}, Timeout：{args.timeout} 秒")
    section.append(f"- 模式：{'PILOT (Takeshi list)' if args.pilot else 'FULL universe'}")
    if args.templates:
        section.append(f"- Templates：{args.templates}")
    if args.wide_search:
        section.append(f"- Wide-search：YES")
    if args.resume:
        section.append(f"- Resume：{args.resume}")
    section.append("")

    # Append (建立 header if 新檔)
    if not os.path.exists(log_path):
        header = f"# Training Log — {start.strftime('%Y-%m-%d')}\n\n"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(header)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(section) + "\n")
    print(f"✓ 寫入 {log_path}")


if __name__ == "__main__":
    main()
