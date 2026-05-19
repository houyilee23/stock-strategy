"""掃描 output/auto_iterate/ 全部 run dir，產出 INDEX.csv + INDEX.md。

目的：日後想分析「哪次訓練用什麼區間 / 結果怎樣 / 哪些個股 PASS」時，
有一份結構化清單可直接讀。原本只能從 summary.md 一個個翻。

INDEX.csv 欄位：
  run_id, started_at, train_start, train_end, test_start, test_end,
  n_pairs, n_templates, n_pass, n_fail, n_dd_breach, n_insufficient,
  benchmark_0050_test_cagr, elapsed_min, kind, notes

INDEX.md：分區段（依 train 區間 group），方便瀏覽。

用法：
  python scripts/build_run_index.py            # 全掃，產 INDEX.csv + INDEX.md
"""
from __future__ import annotations
import os
import re
import csv
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_DIR    = os.path.join(BASE_DIR, "output", "auto_iterate")
CSV_PATH  = os.path.join(AI_DIR, "INDEX.csv")
MD_PATH   = os.path.join(AI_DIR, "INDEX.md")


# ── summary.md 解析 ────────────────────────────────────────

RE_RUN_ID   = re.compile(r"\*\*run_id\*\*:\s*(\S+)")
RE_TRAIN    = re.compile(r"\*\*Train\*\*:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})")
RE_TEST     = re.compile(r"\*\*Test\*\*\s*:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})")
RE_PAIRS    = re.compile(r"跑了\*\*:\s*(\d+)")
RE_UNIVERSE = re.compile(r"Universe\*\*:\s*(\d+)\s*檔\s*x\s*(\d+)\s*模板")
RE_ELAPSED  = re.compile(r"耗時\*\*:\s*([\d.]+)\s*分鐘")
RE_BENCH    = re.compile(r"benchmark.*test CAGR=([+\-]?[\d.]+)%")

VERDICT_PAT = re.compile(r"\|\s*(PASS|FAIL|DD_BREACH|INSUFFICIENT|WEAK|SUSPICIOUS_PERFECT)\s*\|\s*(\d+)")


def parse_summary(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except Exception:
        return None

    m_run   = RE_RUN_ID.search(txt)
    m_train = RE_TRAIN.search(txt)
    m_test  = RE_TEST.search(txt)
    if not (m_run and m_train and m_test):
        return None

    out = {
        "run_id":      m_run.group(1),
        "train_start": m_train.group(1),
        "train_end":   m_train.group(2),
        "test_start":  m_test.group(1),
        "test_end":    m_test.group(2),
    }

    m_pairs = RE_PAIRS.search(txt)
    out["n_pairs"] = int(m_pairs.group(1)) if m_pairs else 0
    m_uni = RE_UNIVERSE.search(txt)
    out["n_stocks"]    = int(m_uni.group(1)) if m_uni else 0
    out["n_templates"] = int(m_uni.group(2)) if m_uni else 0

    m_el = RE_ELAPSED.search(txt)
    out["elapsed_min"] = float(m_el.group(1)) if m_el else None

    m_bn = RE_BENCH.search(txt)
    out["benchmark_0050_test_cagr"] = (
        float(m_bn.group(1)) / 100.0 if m_bn else None
    )

    # verdict counts
    verdicts = {k: 0 for k in ("PASS","FAIL","DD_BREACH","INSUFFICIENT","WEAK","SUSPICIOUS_PERFECT")}
    for k, n in VERDICT_PAT.findall(txt):
        verdicts[k] = int(n)
    for k, v in verdicts.items():
        out[f"n_{k.lower()}"] = v
    return out


def detect_kind(run_id: str, info: dict) -> str:
    """從 run_id / 規模 推斷類型：merged / phase / 全 retrain / 個別 retest / ?"""
    if run_id.startswith("merged_"):
        return "merged"
    n_pairs = info.get("n_pairs", 0)
    if n_pairs >= 1000:
        return "full_retrain"
    if n_pairs >= 100:
        return "batch_retrain"
    if n_pairs >= 10:
        return "phase"
    if n_pairs > 0:
        return "small_test"
    return "?"


def main():
    if not os.path.isdir(AI_DIR):
        print(f"[ERR] 找不到 {AI_DIR}")
        return

    rows = []
    for name in sorted(os.listdir(AI_DIR)):
        full = os.path.join(AI_DIR, name)
        if not os.path.isdir(full):
            continue
        info = parse_summary(os.path.join(full, "summary.md"))
        if not info:
            continue
        info["kind"] = detect_kind(name, info)
        # 開始時間從 run_id 推（格式 YYYYMMDD_HHMMSS）
        m = re.match(r"(\d{8})_(\d{6})", name)
        if m:
            try:
                dt = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
                info["started_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                info["started_at"] = ""
        else:
            info["started_at"] = ""
        rows.append(info)

    # 排序：依 started_at（空字串排最後）
    rows.sort(key=lambda r: r.get("started_at") or "ZZZ")

    # 寫 CSV
    cols = ["run_id", "started_at", "kind",
            "train_start", "train_end", "test_start", "test_end",
            "n_stocks", "n_templates", "n_pairs", "elapsed_min",
            "n_pass", "n_fail", "n_dd_breach", "n_insufficient",
            "n_weak", "n_suspicious_perfect",
            "benchmark_0050_test_cagr"]
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    # 寫 Markdown：依 (train_start, train_end) group
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        key = (r["train_start"], r["train_end"], r["test_start"], r["test_end"])
        groups[key].append(r)

    lines = []
    lines.append("# Auto-iterate 訓練紀錄索引")
    lines.append("")
    lines.append(f"_自動產出 {datetime.now().strftime('%Y-%m-%d %H:%M')}_  · "
                 f"共 **{len(rows)}** 個 run，"
                 f"分屬 **{len(groups)}** 組訓練區間")
    lines.append("")
    lines.append("> 結構化資料：`INDEX.csv`（同目錄）")
    lines.append("")

    for (ts, te, vs, ve), grp in sorted(groups.items()):
        n_runs = len(grp)
        total_pairs = sum(g["n_pairs"] for g in grp)
        total_pass  = sum(g.get("n_pass",0) for g in grp)
        total_fail  = sum(g.get("n_fail",0) for g in grp)
        total_dd    = sum(g.get("n_dd_breach",0) for g in grp)
        total_ins   = sum(g.get("n_insufficient",0) for g in grp)
        train_yrs = _years_between(ts, te)
        test_yrs  = _years_between(vs, ve)
        lines.append(f"## Train {ts} ~ {te} ({train_yrs:.1f} yr)  /  "
                     f"Test {vs} ~ {ve} ({test_yrs:.1f} yr)")
        lines.append("")
        lines.append(f"- Run 數：**{n_runs}**")
        lines.append(f"- 累計 (stock, template) pairs：**{total_pairs:,}**")
        lines.append(f"- Verdict 合計：PASS={total_pass}  FAIL={total_fail}  "
                     f"DD_BREACH={total_dd}  INSUFFICIENT={total_ins}")
        if grp[0].get("benchmark_0050_test_cagr") is not None:
            lines.append(f"- 0050 test CAGR (benchmark)："
                         f"**{grp[0]['benchmark_0050_test_cagr']*100:+.1f}%**")
        lines.append("")
        lines.append("| run_id | 開始時間 | kind | pairs | PASS | FAIL | DD | INSUF | 耗時(分) |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
        for r in grp:
            elapsed = f"{r['elapsed_min']:.1f}" if r.get("elapsed_min") else "—"
            lines.append(
                f"| `{r['run_id']}` | {r.get('started_at','—')} | {r.get('kind','?')} "
                f"| {r['n_pairs']:,} | {r.get('n_pass',0)} | {r.get('n_fail',0)} "
                f"| {r.get('n_dd_breach',0)} | {r.get('n_insufficient',0)} | {elapsed} |"
            )
        lines.append("")

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✓ 寫入 {CSV_PATH}  ({len(rows)} 個 run)")
    print(f"✓ 寫入 {MD_PATH}")
    print(f"  訓練區間組合數：{len(groups)}")
    for (ts, te, vs, ve), grp in sorted(groups.items()):
        print(f"    Train {ts}~{te}  Test {vs}~{ve}: {len(grp)} 個 run")


def _years_between(start: str, end: str) -> float:
    try:
        a = datetime.strptime(start, "%Y-%m-%d")
        b = datetime.strptime(end,   "%Y-%m-%d")
        return (b - a).days / 365.25
    except Exception:
        return 0


if __name__ == "__main__":
    main()
