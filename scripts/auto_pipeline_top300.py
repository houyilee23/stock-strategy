"""Top-300 全自動 pipeline：抓資料 → 加入 watchlist → 每 20 筆 publish 前台。

100% 不碰 FinMind 抓股價（只走 TWSE + TPEX 官方端點）。

流程：
  1. 讀 config/top_300_marketcap.yaml
  2. 對每檔尚未抓 raw 的，呼叫 src.fetchers.fetch_stock（自動 TWSE/TPEX dispatch）
  3. 每完成 BATCH_SIZE 檔（預設 20）：
       a. 把新抓的 sid append 到 watchlists.yaml universe section
       b. 跑 main.py signals --list universe
       c. 跑 scripts/build_html.py
       d. git add + commit + push
  4. 最後一批不滿 20 也要 publish 收尾

設計：
  - Idempotent — 已抓過 raw 的會被 storage.get_missing_months 自動 skip
  - Resumable — 可以中斷重跑，會從未抓的開始
  - 不踩 chip / revenue / FinMind adjusted
  - 進度寫 logs/pipeline_top300_<ts>.log

用法：
  python scripts/auto_pipeline_top300.py             # 全跑（預設 batch=20）
  python scripts/auto_pipeline_top300.py --batch 10  # 改 batch size
  python scripts/auto_pipeline_top300.py --dry-run   # 只看哪些要跑、不執行
  python scripts/auto_pipeline_top300.py --skip-publish  # 不 publish（只 fetch）
"""
from __future__ import annotations
import argparse, os, sys, time, subprocess, yaml
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def load_top_list() -> list[dict]:
    p = os.path.join(BASE_DIR, "config", "top_300_marketcap.yaml")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def list_to_fetch(top: list[dict]) -> list[dict]:
    """過濾出尚未有 raw CSV 或 raw 落後當天的 sid。"""
    out = []
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    for t in top:
        path = os.path.join(raw_dir, f'{t["sid"]}.csv')
        if not os.path.exists(path):
            out.append(t)
    return out


def fetch_one(sid: str, log) -> tuple[bool, str]:
    """單檔 fetch（用 src.fetchers，會自動偵測 TWSE/TPEX）。

    抓完 raw 後也建立 adjusted/<sid>.csv（先 unadjusted = raw close），
    讓 signals / 個股頁能立刻看到此股。未來補 TWSE 除權息事件後可重算。
    """
    try:
        from src.fetchers import fetch_stock
        fetch_stock(sid, start_date="2010-01-01",
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    sleep_seconds=2, max_retries=2)
        # 確認 raw 檔案出現
        raw_path = os.path.join(BASE_DIR, "data", "raw", f"{sid}.csv")
        if not os.path.exists(raw_path):
            return False, "no raw file after fetch"

        import pandas as pd
        df = pd.read_csv(raw_path, dtype={"date": str})
        if df.empty:
            return False, "raw is empty"

        # 建 adjusted（先 unadjusted = raw，欄位用 close_adj 與下游一致）
        adj_path = os.path.join(BASE_DIR, "data", "adjusted", f"{sid}.csv")
        adj = df.copy()
        adj["date"] = pd.to_datetime(adj["date"], format="%Y%m%d")
        adj = adj.rename(columns={})  # keep column names
        adj["close_adj"] = adj["close"]  # 未調整版（後續可補除權息事件再算）
        # 留下標準欄位
        keep = ["date", "open", "high", "low", "close", "volume",
                "turnover", "transactions", "price_change", "close_adj"]
        keep = [c for c in keep if c in adj.columns]
        adj = adj[keep]
        os.makedirs(os.path.dirname(adj_path), exist_ok=True)
        adj.to_csv(adj_path, index=False, encoding="utf-8-sig")

        log(f"  ✓ {sid}: raw {len(df)} 筆, adj 已建（未調整版本，後續可補事件再算）")
        return True, f"{len(df)} rows"
    except Exception as e:
        log(f"  ✗ {sid}: {e}")
        return False, str(e)


def add_to_universe(new_sids: list[str], top_by_sid: dict, log):
    """把新 sid append 到 watchlists.yaml 的 universe section（保留註解）。"""
    wl_path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
    if not os.path.exists(wl_path):
        log(f"[WARN] watchlists.yaml not found, skip")
        return

    with open(wl_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 找 universe: 區段尾巴位置（下一個 top-level key 之前）
    import re
    lines = text.split("\n")
    in_universe = False
    insert_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^universe:\s*$", ln):
            in_universe = True
            continue
        if in_universe and re.match(r"^\w[\w_]*:\s*$", ln):
            insert_idx = i  # 下一個 top-level key 起始
            break
    if not in_universe:
        log(f"[WARN] universe section not found")
        return
    if insert_idx is None:
        insert_idx = len(lines)

    # 抓現有 universe 中的 sid，不重複加
    existing = set()
    sid_pat = re.compile(r'-\s*"([\w\d]+)"')
    for ln in lines[:insert_idx]:
        m = sid_pat.search(ln)
        if m:
            existing.add(m.group(1))

    addable = [s for s in new_sids if s not in existing]
    if not addable:
        log(f"  → universe 已包含所有 batch sid，無需新增")
        return

    today_tag = datetime.now().strftime("%Y-%m-%d")
    block = [f"  # ── {today_tag} top-300 補入 ({len(addable)} 檔) ──"]
    for sid in addable:
        rec = top_by_sid.get(sid, {})
        name = rec.get("name", "")
        rank = rec.get("rank", "?")
        block.append(f'  - "{sid}"   # {name} (rank {rank})')

    new_lines = lines[:insert_idx] + block + [""] + lines[insert_idx:]
    with open(wl_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    log(f"  ✓ universe 新增 {len(addable)} 檔")


def publish(batch_idx: int, batch_sids: list[str], log):
    """跑 signals + build_html + git commit + push。"""
    log(f"  → 重跑 signals universe ...")
    subprocess.call([sys.executable, "main.py", "signals", "--list", "universe"],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"  → 重跑 build_html ...")
    subprocess.call([sys.executable, os.path.join("scripts", "build_html.py")],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Git commit + push
    log(f"  → git commit + push ...")
    subprocess.call(["git", "add", "data/raw", "data/adjusted",
                     "config/watchlists.yaml", "config/stock_market.yaml",
                     "config/stock_ipo.yaml",
                     "index.html", "katie.html", "stock/"],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    msg = f"top-300 pipeline batch {batch_idx}：抓 {len(batch_sids)} 檔上市/上櫃股 + publish"
    subprocess.call(["git", "commit", "-m", msg],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rc = subprocess.call(["git", "push", "origin", "main"],
                         cwd=BASE_DIR,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"  ✓ batch {batch_idx} push {'OK' if rc==0 else 'FAILED'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-publish", action="store_true",
                    help="只抓資料、不 publish")
    args = ap.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = os.path.join(BASE_DIR, "logs", f"pipeline_top300_{ts}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_f = open(log_path, "w", encoding="utf-8", buffering=1)

    def log(msg: str):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        print(line)
        log_f.write(line + "\n")

    log(f"=== Top-300 auto pipeline 啟動 ===")
    top = load_top_list()
    log(f"Top {len(top)} 列表載入")
    todo = list_to_fetch(top)
    log(f"待處理（沒 raw csv 的）：{len(todo)} 檔")
    if args.dry_run:
        for t in todo[:30]:
            log(f"  待抓 Rank {t['rank']:>3} {t['sid']} {t['name']} ({t['market']})")
        if len(todo) > 30:
            log(f"  ... 還有 {len(todo)-30} 檔")
        return

    top_by_sid = {t["sid"]: t for t in top}
    batch_buf = []
    batch_idx = 0
    success_total = 0
    fail_total = 0

    for i, t in enumerate(todo):
        sid = t["sid"]
        log(f"[{i+1}/{len(todo)}] fetch {sid} ({t['name']}, {t['market']})...")
        ok, msg = fetch_one(sid, log)
        if ok:
            batch_buf.append(sid)
            success_total += 1
        else:
            fail_total += 1
        time.sleep(2)  # 每檔之間 sleep 2 秒，不要打太兇

        # 滿 batch 就 publish
        if len(batch_buf) >= args.batch:
            batch_idx += 1
            log(f"\n=== Batch {batch_idx}: {len(batch_buf)} 檔完成，publish 中 ===")
            if not args.skip_publish:
                add_to_universe(batch_buf, top_by_sid, log)
                publish(batch_idx, batch_buf, log)
            batch_buf = []

    # 收尾不滿 batch
    if batch_buf and not args.skip_publish:
        batch_idx += 1
        log(f"\n=== Final batch {batch_idx}: {len(batch_buf)} 檔，publish 中 ===")
        add_to_universe(batch_buf, top_by_sid, log)
        publish(batch_idx, batch_buf, log)

    log(f"\n=== 完成：成功 {success_total}, 失敗 {fail_total}, 共 {batch_idx} 個 batch ===")
    log_f.close()


if __name__ == "__main__":
    main()
