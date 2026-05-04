"""補齊 config/stock_ipo.yaml — 為 watchlists 中尚未登錄的股票查 IPO 日期

機制：
  對每個尚未在 stock_ipo.yaml 中的股票，做 1 次 FinMind TaiwanStockPrice 呼叫
  （start=2000-01-01, end=today），取 response 第一筆 date 作為 IPO 月份。

成本：
  ~1 call/stock，FinMind 免費版 300 req/hr。watchlists ~30 檔未登錄 → 30 calls，OK。

用法：
  python scripts/fetch_stock_ipo.py            # 補齊所有 watchlists 缺失的
  python scripts/fetch_stock_ipo.py --force    # 全部重抓（即使已有）
  python scripts/fetch_stock_ipo.py --stocks 5871 1101  # 指定
"""
import os
import sys
import time
import argparse
import yaml
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

WATCHLISTS_PATH = os.path.join(BASE_DIR, "config", "watchlists.yaml")
IPO_PATH = os.path.join(BASE_DIR, "config", "stock_ipo.yaml")
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
SLEEP_SEC = 1.5  # 兩 call 間
SYSTEM_FLOOR = "2010-01"  # 系統最早抓的月份；早於此一律寫 2010-01


def load_watchlists() -> set[str]:
    """收集 watchlists 中所有股票（不含 exception）"""
    with open(WATCHLISTS_PATH, encoding="utf-8") as f:
        wl = yaml.safe_load(f) or {}
    ids = set()
    for key, lst in wl.items():
        if key == "exception":
            continue
        for sid in (lst or []):
            ids.add(str(sid))
    return ids


def load_ipo_yaml() -> dict[str, str]:
    if not os.path.exists(IPO_PATH):
        return {}
    with open(IPO_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in data.items()}


def save_ipo_yaml(data: dict[str, str]):
    """保留原 header"""
    header = (
        "# ============================================================\n"
        "# 個股最早可下載資料的月份\n"
        "# 格式：股票代號: \"YYYY-MM\"\n"
        "#\n"
        "# 此檔案由程式自動維護（首次成功下載時寫入），也可手動修改。\n"
        "# 作用：fetch 時自動跳過上市前的月份，避免無效請求。\n"
        "# ============================================================\n\n"
    )
    lines = "".join(f'"{k}": "{v}"\n' for k, v in sorted(data.items()))
    with open(IPO_PATH, "w", encoding="utf-8") as f:
        f.write(header + lines)


def query_ipo_via_finmind(stock_id: str) -> str | None:
    """回傳 IPO 月份 'YYYY-MM'，找不到回 None。"""
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": "2000-01-01",
        "end_date": time.strftime("%Y-%m-%d"),
    }
    try:
        r = requests.get(FINMIND_URL, params=params, timeout=60)
        r.raise_for_status()
        j = r.json()
        if j.get("status") != 200:
            return None
        data = j.get("data", [])
        if not data:
            return None
        first_date = data[0].get("date")  # 'YYYY-MM-DD'
        if not first_date or len(first_date) < 7:
            return None
        return first_date[:7]  # 'YYYY-MM'
    except (requests.RequestException, ValueError):
        return None


def normalize_to_floor(ipo_ym: str) -> str:
    """晚於 SYSTEM_FLOOR 用實際 IPO，否則用 floor（系統最早抓 2010-01）"""
    if ipo_ym < SYSTEM_FLOOR:
        return SYSTEM_FLOOR
    return ipo_ym


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="即使已存在也重抓")
    ap.add_argument("--stocks", nargs="*", default=None, help="指定股票")
    args = ap.parse_args()

    ipo_data = load_ipo_yaml()
    print(f"目前 stock_ipo.yaml: {len(ipo_data)} 檔")

    if args.stocks:
        target = set(args.stocks)
    else:
        wl = load_watchlists()
        if args.force:
            target = wl
        else:
            target = wl - set(ipo_data.keys())

    target = sorted(target)
    print(f"待查詢：{len(target)} 檔")
    if not target:
        print("無需補齊。")
        return

    added, updated, failed = [], [], []
    for i, sid in enumerate(target, 1):
        actual = query_ipo_via_finmind(sid)
        if actual is None:
            failed.append(sid)
            print(f"  [{i:>2}/{len(target)}] {sid}: ✗ FinMind 無資料")
        else:
            normalized = normalize_to_floor(actual)
            existing = ipo_data.get(sid)
            ipo_data[sid] = normalized
            if existing is None:
                added.append((sid, actual, normalized))
                print(f"  [{i:>2}/{len(target)}] {sid}: + IPO={actual}, 寫入 {normalized}")
            elif existing != normalized:
                updated.append((sid, existing, normalized))
                print(f"  [{i:>2}/{len(target)}] {sid}: ~ {existing} → {normalized} (FinMind: {actual})")
            else:
                print(f"  [{i:>2}/{len(target)}] {sid}: = {normalized}（已正確）")
        time.sleep(SLEEP_SEC)

    save_ipo_yaml(ipo_data)
    print(f"\n完成：新增 {len(added)} / 更新 {len(updated)} / 失敗 {len(failed)}")
    if failed:
        print(f"失敗清單：{failed}")
    print(f"寫入：{IPO_PATH}（共 {len(ipo_data)} 檔）")


if __name__ == "__main__":
    main()
