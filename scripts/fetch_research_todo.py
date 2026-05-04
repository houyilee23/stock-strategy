"""逐檔抓 watchlists.yaml 中 research_todo 的股票，成功後移至 universe

機制：
  1. 讀 research_todo 清單
  2. 對每檔呼叫 `python main.py update <sid>`（fetcher 自帶 IPO skip + rate limit）
  3. 抓完檢查 data/adjusted/{sid}.csv 是否存在且 ≥ 50 筆
  4. 通過 → 從 research_todo 移到 universe（保留尾隨註解）
  5. 失敗 → 留在 research_todo，記錄到 failed list

⚠️ 不要在 auto_iterate retrain 跑中時執行此腳本。fetcher 會寫入 adjusted/，可能與
   retrain 讀檔產生 race condition。

⚠️ 為避免 TWSE 過密請求，此腳本永遠 sequential（一次 1 檔），無 --parallel 選項。

用法：
  python scripts/fetch_research_todo.py            # 跑全部 research_todo
  python scripts/fetch_research_todo.py --dry-run  # 只列要做什麼，不實際抓
  python scripts/fetch_research_todo.py --limit 5  # 只跑前 5 檔（測試用）
"""
import os
import re
import sys
import subprocess
import argparse
import yaml
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHLISTS_PATH = os.path.join(BASE_DIR, "config", "watchlists.yaml")
ADJUSTED_DIR = os.path.join(BASE_DIR, "data", "adjusted")
MIN_ROWS_OK = 50


def read_watchlists_text() -> str:
    with open(WATCHLISTS_PATH, encoding="utf-8") as f:
        return f.read()


def write_watchlists_text(text: str):
    with open(WATCHLISTS_PATH, "w", encoding="utf-8") as f:
        f.write(text)


def parse_research_todo(text: str) -> list[tuple[str, str]]:
    """從 watchlists.yaml 文字中讀 research_todo 的所有 stock_id 與其原始整行
    回傳 [(sid, original_line), ...]，順序保留原檔順序"""
    in_section = False
    items = []
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*$", line)
        if m:
            in_section = (m.group(1) == "research_todo")
            continue
        if not in_section:
            continue
        # match: "  - "1101"   # 台泥"
        m = re.match(r'^\s*-\s*"([^"]+)"', line)
        if m:
            items.append((m.group(1), line))
    return items


def adjusted_ok(stock_id: str) -> bool:
    path = os.path.join(ADJUSTED_DIR, f"{stock_id}.csv")
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            n = sum(1 for _ in f)
        return n >= MIN_ROWS_OK
    except OSError:
        return False


def move_lines_in_text(text: str, lines_to_move: list[str]) -> str:
    """把 lines_to_move 從 research_todo: 區塊移到 universe: 區塊尾"""
    if not lines_to_move:
        return text

    src_lines = text.splitlines(keepends=True)

    # 1) 找 universe: 與 research_todo: 行 index
    idx_universe = None
    idx_research_todo = None
    for i, line in enumerate(src_lines):
        if re.match(r"^universe:\s*$", line):
            idx_universe = i
        elif re.match(r"^research_todo:\s*$", line):
            idx_research_todo = i

    if idx_universe is None or idx_research_todo is None:
        raise ValueError("找不到 universe: 或 research_todo: 區塊")

    # 2) 找 universe 區塊結尾（下一個 ^[A-Za-z_]+:）
    end_universe = idx_research_todo  # universe 區塊結到 research_todo 之前
    for i in range(idx_universe + 1, idx_research_todo):
        if re.match(r"^[A-Za-z_]+:\s*$", src_lines[i]):
            end_universe = i
            break

    # 3) 找 research_todo 區塊範圍（從 idx_research_todo 到下一個 ^[A-Za-z_]+:）
    end_todo = len(src_lines)
    for i in range(idx_research_todo + 1, len(src_lines)):
        if re.match(r"^[A-Za-z_]+:\s*$", src_lines[i]):
            end_todo = i
            break

    # 4) 從 research_todo 區塊中移除 lines_to_move
    targets = set(line.rstrip("\n") for line in lines_to_move)
    new_src = []
    in_todo_range = False
    for i, line in enumerate(src_lines):
        if i == idx_research_todo:
            in_todo_range = True
            new_src.append(line)
            continue
        if in_todo_range and i >= end_todo:
            in_todo_range = False
        if in_todo_range and line.rstrip("\n") in targets:
            continue  # 跳過要被移走的行
        new_src.append(line)

    # 5) 在 universe 區塊尾插入新行（end_universe 位置之前）
    insertion = [line if line.endswith("\n") else line + "\n" for line in lines_to_move]
    final = new_src[:end_universe] + insertion + new_src[end_universe:]
    return "".join(final)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="不實際抓，只列計畫")
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 檔（測試）")
    args = ap.parse_args()

    text = read_watchlists_text()
    todo = parse_research_todo(text)
    if not todo:
        print("research_todo 空，無事可做。")
        return

    if args.limit:
        todo = todo[:args.limit]

    print(f"research_todo 待處理：{len(todo)} 檔")
    if args.dry_run:
        for sid, line in todo:
            print(f"  {sid}  ({'已有 adjusted' if adjusted_ok(sid) else '需抓'})")
        return

    success_lines = []
    failed = []
    skipped = []  # 已 OK 直接跳過

    for i, (sid, original_line) in enumerate(todo, 1):
        if adjusted_ok(sid):
            print(f"[{i}/{len(todo)}] {sid}: 已 OK，直接 promote")
            success_lines.append(original_line)
            continue

        print(f"[{i}/{len(todo)}] {sid}: 開始抓...", flush=True)
        t0 = datetime.now()
        try:
            r = subprocess.run(
                ["python", "main.py", "update", sid],
                cwd=BASE_DIR, capture_output=True, text=True,
                encoding="utf-8", timeout=1800,  # 30 min per stock max
            )
            elapsed = (datetime.now() - t0).total_seconds()
            if r.returncode != 0:
                print(f"  ✗ {sid}: subprocess returncode={r.returncode}, elapsed={elapsed:.0f}s")
                failed.append(sid)
                continue
        except subprocess.TimeoutExpired:
            print(f"  ✗ {sid}: timeout 30 min")
            failed.append(sid)
            continue

        if adjusted_ok(sid):
            print(f"  ✓ {sid}: OK ({elapsed:.0f}s)")
            success_lines.append(original_line)
        else:
            print(f"  ✗ {sid}: 抓完但 adjusted 仍 < {MIN_ROWS_OK} 列")
            failed.append(sid)

    # 更新 watchlists.yaml
    if success_lines:
        new_text = move_lines_in_text(text, success_lines)
        write_watchlists_text(new_text)
        print(f"\nwatchlists.yaml 已更新：{len(success_lines)} 檔從 research_todo → universe")

    print(f"\n總結：成功 {len(success_lines)} / 失敗 {len(failed)} / 已跳過 {len(skipped)}")
    if failed:
        print(f"失敗清單：{failed}")


if __name__ == "__main__":
    main()
