"""Signal journal reporter — 績效摘要。

讀多月份 journal CSV，計算掛單命中率與當下浮動報酬（exit tracking 在 Phase 2
完整接上之前，先用「最新收盤 vs fill_price」當代理值）。

輸出 Markdown 報表 + console 簡表。
"""
from __future__ import annotations
import os
from datetime import datetime
import pandas as pd

from src.journal import storage
from src.journal.schema import (
    STATUS_FILLED, STATUS_NOT_FILLED, STATUS_EXPIRED, STATUS_NO_DATA,
    STATUS_PENDING, STATUS_SKIPPED,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT_DIR = os.path.join(BASE_DIR, "output", "signal_journal", "reports")


def _latest_close(sid: str) -> float | None:
    """取最新收盤（adjusted 優先）。"""
    for sub in ("adjusted", "raw"):
        path = os.path.join(BASE_DIR, "data", sub, f"{sid}.csv")
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, dtype={"date": str})
            if df.empty:
                continue
            if sub == "adjusted" and "close_adj" in df.columns:
                return float(df["close_adj"].iloc[-1])
            return float(df["close"].iloc[-1])
        except Exception:
            continue
    return None


def _compute_pnl(row: pd.Series) -> float | None:
    """目前的代理 P&L：BUY 用 (latest_close / fill_price) - 1；SELL 不算。

    Phase 2 接上完整 exit tracking 後改讀 realized_return。
    """
    if row["status"] != STATUS_FILLED:
        return None
    if str(row["action"]).upper() != "BUY":
        return None
    fp = row["fill_price"]
    if pd.isna(fp) or fp <= 0:
        return None
    latest = _latest_close(str(row["sid"]))
    if latest is None:
        return None
    return (latest / float(fp)) - 1.0


def build_summary(df: pd.DataFrame) -> dict:
    """整體摘要：依 status 統計 + 命中率 + 浮動報酬。"""
    if df.empty:
        return {"total": 0}

    status_counts = df["status"].value_counts().to_dict()
    total = len(df)
    filled = status_counts.get(STATUS_FILLED, 0)
    not_filled = status_counts.get(STATUS_NOT_FILLED, 0)
    expired = status_counts.get(STATUS_EXPIRED, 0)
    pending = status_counts.get(STATUS_PENDING, 0)
    no_data = status_counts.get(STATUS_NO_DATA, 0)

    decided = filled + not_filled + expired  # 已驗結束的（無論 fill 與否）
    hit_rate = (filled / decided) if decided > 0 else float("nan")

    # 浮動 P&L（只有 filled BUY）
    pnls = df.apply(_compute_pnl, axis=1).dropna()
    avg_pnl = float(pnls.mean()) if len(pnls) > 0 else float("nan")
    win_rate = float((pnls > 0).mean()) if len(pnls) > 0 else float("nan")

    return {
        "total":       total,
        "filled":      filled,
        "not_filled":  not_filled,
        "expired":     expired,
        "pending":     pending,
        "no_data":     no_data,
        "hit_rate":    hit_rate,
        "open_pnl_n":  len(pnls),
        "open_pnl_mean": avg_pnl,
        "open_pnl_winrate": win_rate,
    }


def group_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """依 account / template / tier 等欄位 group 統計。"""
    if df.empty or by not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["_pnl"] = df.apply(_compute_pnl, axis=1)

    def _agg(g: pd.DataFrame) -> pd.Series:
        decided_mask = g["status"].isin([STATUS_FILLED, STATUS_NOT_FILLED,
                                          STATUS_EXPIRED])
        decided = int(decided_mask.sum())
        filled = int((g["status"] == STATUS_FILLED).sum())
        hit_rate = filled / decided if decided > 0 else float("nan")
        pnls = g["_pnl"].dropna()
        return pd.Series({
            "n":         int(len(g)),
            "filled":    filled,
            "not_filled": int((g["status"] == STATUS_NOT_FILLED).sum()),
            "expired":   int((g["status"] == STATUS_EXPIRED).sum()),
            "pending":   int((g["status"] == STATUS_PENDING).sum()),
            "hit_rate":  hit_rate,
            "open_n":    int(len(pnls)),
            "open_avg":  float(pnls.mean()) if len(pnls) > 0 else float("nan"),
            "open_win":  float((pnls > 0).mean()) if len(pnls) > 0 else float("nan"),
        })

    return df.groupby(by, dropna=False).apply(_agg).reset_index()


def _fmt_pct(v) -> str:
    if v is None or pd.isna(v):
        return "  -  "
    return f"{v*100:+.1f}%" if abs(v) < 10 else f"{v:.2f}"


def _fmt_rate(v) -> str:
    if v is None or pd.isna(v):
        return "  -  "
    return f"{v*100:.1f}%"


def write_markdown(start: str | None = None, end: str | None = None,
                    account: str | None = None) -> str:
    """產出 Markdown 報表到 output/signal_journal/reports/。

    Args:
      start / end: partition 字串 'YYYY-MM'。None = 全部歷史。
      account: 只看單一帳戶。None = 全部。
    """
    os.makedirs(REPORT_DIR, exist_ok=True)
    df = storage.load_range(start, end)
    if account:
        df = df[df["account"] == account]

    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    range_tag = f"{start or 'all'}_{end or 'latest'}"
    acc_tag = account or "all"
    out_path = os.path.join(REPORT_DIR,
                             f"signal_perf_{acc_tag}_{range_tag}_{ts}.md")

    summary = build_summary(df)
    g_account  = group_summary(df, "account")
    g_template = group_summary(df, "template")
    g_tier     = group_summary(df, "tier")
    g_action   = group_summary(df, "action")

    lines: list[str] = []
    lines.append(f"# 訊號績效報表 — account={acc_tag} period={range_tag}")
    lines.append("")
    lines.append(f"生成時間：{datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## 整體摘要")
    lines.append("")
    if summary.get("total", 0) == 0:
        lines.append("（無資料）")
    else:
        lines.append(f"- 訊號總數：{summary['total']}")
        lines.append(f"- 已驗證（filled + not_filled + expired）："
                     f"{summary['filled'] + summary['not_filled'] + summary['expired']}")
        lines.append(f"- 掛單成交：{summary['filled']}")
        lines.append(f"- 掛單未成交（next bars 不觸及）：{summary['not_filled']}")
        lines.append(f"- 過期（{summary.get('expired', 0)} 筆 >10 交易日未觸發）")
        lines.append(f"- 待驗證 pending：{summary['pending']}")
        lines.append(f"- 命中率（filled / 已驗證）：{_fmt_rate(summary['hit_rate'])}")
        lines.append("")
        lines.append("### 已成交 BUY 訊號的當下浮動 P&L（最新收盤 vs fill_price）")
        lines.append(f"- 樣本數：{summary['open_pnl_n']}")
        lines.append(f"- 平均浮動報酬：{_fmt_pct(summary['open_pnl_mean'])}")
        lines.append(f"- 浮動勝率：{_fmt_rate(summary['open_pnl_winrate'])}")
    lines.append("")

    def _table(title: str, g: pd.DataFrame, key: str) -> None:
        lines.append(f"## 依 {title} 拆解")
        lines.append("")
        if g.empty:
            lines.append("（無資料）")
            lines.append("")
            return
        lines.append(f"| {title} | 訊號數 | 成交 | 未成交 | 過期 | 命中率 | "
                     f"浮動樣本 | 浮動平均 | 浮動勝率 |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        g_sorted = g.sort_values("n", ascending=False)
        for _, r in g_sorted.iterrows():
            lines.append(f"| {r[key]} | {int(r['n'])} | {int(r['filled'])} | "
                         f"{int(r['not_filled'])} | {int(r['expired'])} | "
                         f"{_fmt_rate(r['hit_rate'])} | {int(r['open_n'])} | "
                         f"{_fmt_pct(r['open_avg'])} | {_fmt_rate(r['open_win'])} |")
        lines.append("")

    _table("Account",  g_account,  "account")
    _table("Action",   g_action,   "action")
    _table("Tier",     g_tier,     "tier")
    _table("Template", g_template, "template")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def print_console_summary(start: str | None = None, end: str | None = None,
                           account: str | None = None) -> None:
    """終端機簡表（不寫檔），供快速查看。"""
    df = storage.load_range(start, end)
    if account:
        df = df[df["account"] == account]
    s = build_summary(df)
    print(f"\n  訊號績效 — account={account or 'all'} "
          f"period={start or 'all'}~{end or 'latest'}")
    print(f"  {'-'*60}")
    if s.get("total", 0) == 0:
        print("  （無資料）")
        return
    print(f"  訊號總數：{s['total']}  |  pending：{s['pending']}  "
          f"|  no_data：{s['no_data']}")
    print(f"  成交：{s['filled']}  未成交：{s['not_filled']}  "
          f"過期：{s['expired']}  →  命中率 {_fmt_rate(s['hit_rate'])}")
    print(f"  已成交 BUY 浮動報酬：n={s['open_pnl_n']}  "
          f"平均 {_fmt_pct(s['open_pnl_mean'])}  勝率 {_fmt_rate(s['open_pnl_winrate'])}")
    print()
