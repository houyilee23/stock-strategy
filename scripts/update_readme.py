"""每日 update 結束後產生 README.md（手機 GitHub App 主入口）。

內容：
- 最新更新日期
- 各帳戶今日訊號摘要表（連結到完整報告 + per_stock 個股報告）
- 連結到歷史月份歸檔
- 系統說明簡述

用法：
  python scripts/update_readme.py
"""
import os
import sys
import yaml
import pandas as pd
from datetime import date

# 強制 stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.runner import _load_recommendations


def load_watchlists() -> dict:
    path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_latest_signals(account: str) -> str:
    """讀取 latest/ 中該帳戶的訊號 markdown 內容。"""
    p = os.path.join(BASE_DIR, "output", "reports", "latest", f"signals_{account}.md")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def parse_signals_md_table(md: str) -> list[dict]:
    """從 latest signals markdown 解析訊號表（GitHub flavored markdown table）。"""
    rows = []
    in_table = False
    headers = []
    for line in md.split("\n"):
        line = line.strip()
        if line.startswith("| 股票 |"):
            headers = [c.strip() for c in line.strip("|").split("|")]
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
    return rows


def build_account_section(account: str) -> list[str]:
    """為單一帳戶產生 README 段落（連結到 latest 報告 + per_stock 個股報告）。"""
    md = load_latest_signals(account)
    if not md:
        return []

    rows = parse_signals_md_table(md)
    if not rows:
        return []

    L = []
    L.append(f"### {account}")
    L.append("")
    L.append(f"📄 完整報告：[最新訊號](output/reports/latest/signals_{account}.md)")
    L.append("")

    # 簡化表格：只顯示動作/Tier/收盤/RSI/個股趨勢/Regime + 連結個股
    L.append("| 股票 | 名稱 | 收盤 | 動作 | Tier | 倉位 | RSI | 趨勢 | Regime |")
    L.append("|------|------|------|------|------|------|-----|------|--------|")

    for r in rows:
        sid = r.get("股票", "")
        name = r.get("名稱", "")
        close = r.get("收盤", "—")
        action = r.get("動作", "—")
        tier = r.get("Tier", "—")
        pos = r.get("倉位上限", "—")
        rsi = r.get("RSI", "—")
        trend = r.get("個股趨勢", "—")
        regime = r.get("市場Regime", "—")

        # 動作高亮
        if action == "BUY":
            action_disp = f"🟢 **BUY**"
        elif action == "SELL":
            action_disp = f"🔴 **SELL**"
        else:
            action_disp = action

        # 個股代號連結到 per_stock 報告
        sid_link = f"[{sid}](output/reports/per_stock/{sid}.md)" if sid else ""
        L.append(f"| {sid_link} | {name} | {close} | {action_disp} | {tier} | "
                  f"{pos} | {rsi} | {trend} | {regime} |")

    L.append("")
    return L


def build_archive_links() -> list[str]:
    """列出 output/reports/{YYYY}/{MM}/ 結構，供翻閱歷史。"""
    L = []
    reports_dir = os.path.join(BASE_DIR, "output", "reports")
    if not os.path.isdir(reports_dir):
        return L

    years = sorted([d for d in os.listdir(reports_dir)
                    if d.isdigit() and len(d) == 4 and
                    os.path.isdir(os.path.join(reports_dir, d))],
                   reverse=True)
    if not years:
        return L

    L.append("## 歷史報告")
    L.append("")
    for yr in years:
        ymo_dir = os.path.join(reports_dir, yr)
        months = sorted([d for d in os.listdir(ymo_dir)
                          if os.path.isdir(os.path.join(ymo_dir, d))],
                         reverse=True)
        for mo in months:
            n_files = len([f for f in os.listdir(os.path.join(ymo_dir, mo))
                            if f.endswith(".md")])
            L.append(f"- [{yr}/{mo}](output/reports/{yr}/{mo}/) — {n_files} 份")
    L.append("")
    return L


def main():
    today_str = date.today().strftime("%Y-%m-%d")
    wl = load_watchlists()
    accounts = [k for k in wl.keys() if k not in ("exception",)]

    L = []
    L.append("# 台股個股策略系統")
    L.append("")
    L.append(f"_最後更新：**{today_str}**_")
    L.append("")
    L.append("📱 在手機 GitHub App 上開啟此頁，可直接查看當日訊號 + 點任一檔股票看歷史回測。")
    L.append("")

    # 各帳戶區塊
    L.append("## 今日訊號")
    L.append("")
    for acc in accounts:
        sec = build_account_section(acc)
        if sec:
            L.extend(sec)

    # 歷史報告連結
    L.extend(build_archive_links())

    # 系統說明
    L.append("---")
    L.append("")
    L.append("## 系統概念")
    L.append("")
    L.append("- **訊號模式**：每天對 watchlist 內每檔輸出 BUY/HOLD/SELL 建議")
    L.append("- **Tier**：S > A > B > C > D > F；F-tier 表示策略無利可圖，建議不持有")
    L.append("- **BS/BA/BB**：tier=F 但 BNH 長持期 CAGR 漂亮 → 改用「買進長持」替代")
    L.append("- **每檔 Template 不同**：每股獨立優化，由 `auto_iterate` 找出最佳策略 + 參數")
    L.append("")
    L.append("詳見 [docs/](docs/) 與 [CLAUDE.md](CLAUDE.md)。")
    L.append("")

    out_path = os.path.join(BASE_DIR, "README.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"✓ 寫入 {out_path}")


if __name__ == "__main__":
    main()
