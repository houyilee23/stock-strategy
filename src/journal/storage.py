"""Signal journal 的 CSV 讀寫。月切檔案：output/signal_journal/{YYYY-MM}.csv。

跟「資料是怎麼來的」「驗證怎麼跑」完全解耦。
"""
from __future__ import annotations
import os
from typing import Iterable
import pandas as pd

from src.journal.schema import ALL_FIELDS, partition_for

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL_DIR = os.path.join(BASE_DIR, "output", "signal_journal")


def journal_path(partition: str) -> str:
    """partition='2026-05' → output/signal_journal/2026-05.csv"""
    return os.path.join(JOURNAL_DIR, f"{partition}.csv")


def ensure_dir() -> None:
    os.makedirs(JOURNAL_DIR, exist_ok=True)


def load_partition(partition: str) -> pd.DataFrame:
    """讀單月 CSV。檔案不存在 → 回空 DataFrame（含完整欄位）。"""
    path = journal_path(partition)
    if not os.path.exists(path):
        return pd.DataFrame(columns=ALL_FIELDS)
    df = pd.read_csv(path, dtype={"sid": str, "signal_date": str,
                                   "fill_date": str, "exit_date": str})
    # 補齊缺欄位（schema 演進時舊檔仍可讀）
    for col in ALL_FIELDS:
        if col not in df.columns:
            df[col] = None
    return df[ALL_FIELDS]


def save_partition(partition: str, df: pd.DataFrame) -> str:
    """寫回單月 CSV（覆寫）。回傳檔案路徑。"""
    ensure_dir()
    path = journal_path(partition)
    # 強制欄位順序一致
    df = df.reindex(columns=ALL_FIELDS)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def upsert_rows(rows: Iterable[dict]) -> dict:
    """把多筆 row 落帳到對應月份檔案。

    依 journal_id 去重：已存在則 skip（不覆寫，避免 validator 寫過的欄位被洗掉）。
    多月份的 row 會分發到各自的檔案。
    回傳 {"inserted": N, "skipped": M, "files": [...]}
    """
    rows = list(rows)
    if not rows:
        return {"inserted": 0, "skipped": 0, "files": []}

    # group by partition
    by_partition: dict[str, list[dict]] = {}
    for r in rows:
        p = partition_for(r["signal_date"])
        by_partition.setdefault(p, []).append(r)

    inserted = 0
    skipped = 0
    files = []
    for partition, new_rows in by_partition.items():
        existing = load_partition(partition)
        existing_ids = set(existing["journal_id"].dropna().astype(str).tolist())
        to_add = []
        for r in new_rows:
            if r["journal_id"] in existing_ids:
                skipped += 1
                continue
            to_add.append(r)
            existing_ids.add(r["journal_id"])
        if to_add:
            new_df = pd.DataFrame(to_add)
            combined = pd.concat([existing, new_df], ignore_index=True)
            path = save_partition(partition, combined)
            files.append(path)
            inserted += len(to_add)
    return {"inserted": inserted, "skipped": skipped, "files": files}


def load_range(start_partition: str | None = None,
                end_partition: str | None = None) -> pd.DataFrame:
    """讀多月份 CSV 並 concat。partition 字串比較即可（YYYY-MM 自然排序）。"""
    ensure_dir()
    parts = sorted(f[:-4] for f in os.listdir(JOURNAL_DIR)
                   if f.endswith(".csv") and len(f) == 11)  # YYYY-MM.csv = 11
    if start_partition:
        parts = [p for p in parts if p >= start_partition]
    if end_partition:
        parts = [p for p in parts if p <= end_partition]
    if not parts:
        return pd.DataFrame(columns=ALL_FIELDS)
    return pd.concat([load_partition(p) for p in parts], ignore_index=True)


def list_partitions() -> list[str]:
    ensure_dir()
    return sorted(f[:-4] for f in os.listdir(JOURNAL_DIR)
                  if f.endswith(".csv") and len(f) == 11)
