"""產生手機友善的 web UI。

輸入：
- output/reports/latest/signals_{account}.md  ← 各帳戶今日訊號
- config/per_stock_recommendations.yaml       ← tier、template、推薦
- data/adjusted/{sid}.csv                     ← 還原股價（多時段績效用）
- data/raw/{sid}.csv                          ← raw（回測引擎用）
- output/auto_iterate/merged_*/{template}.yaml ← 各檔 best_params

輸出：
- /index.html                             ← 首頁（3 帳戶 tab + 訊號表）
- /stock/{sid}.html                       ← 個股頁
- docs/_data.json                             ← 嵌入資料（debug 用，主要寫進 HTML）

設計：
- Pico.css（semantic CSS，27KB）
- Alpine.js（15KB，做 tab/搜尋/排序）
- 全部資料 inline 進 HTML，不需網路就能看（除了 CDN 那兩個 lib）
- 路徑相對，可在本機 file:// 與 GitHub Pages 同樣運作

用法：
  python scripts/build_html.py
"""
import os
import sys
import json
import math
import yaml
import argparse
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

# 強制 stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.runner import (
    _load_strategy_cfg, _load_adj_ohlcv, _load_ohlcv,
    _load_recommendations,
)
from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS

# Web UI 寫到 repo 根目錄（GitHub Pages source = /）
# docs/ 保留給 markdown 文件（給人或 Claude 看）
WEB_DIR = BASE_DIR
WEB_STOCK_DIR = os.path.join(WEB_DIR, "stock")
# 舊變數名相容（避免 build 過程中其他地方仍然引用）
DOCS_DIR = WEB_DIR
DOCS_STOCK_DIR = WEB_STOCK_DIR
TODAY = date.today().strftime("%Y-%m-%d")


# ===== 1. 資料收集 ============================================================

def load_watchlists() -> dict:
    path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_signals_md(path: str) -> list[dict]:
    """從 latest signals markdown 解析訊號表。"""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        md = f.read()

    rows, in_table, headers = [], False, []
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


def load_per_stock_params(stock_id: str, template: str) -> dict | None:
    merged_dir = os.path.join(BASE_DIR, "output", "auto_iterate", "merged_20260426_120034")
    yaml_path = os.path.join(merged_dir, f"{template}.yaml")
    if not os.path.exists(yaml_path):
        return None
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    per_stock = data.get("per_stock", {}) if isinstance(data, dict) else {}
    rec = per_stock.get(stock_id)
    if not isinstance(rec, dict):
        return None
    return rec.get("best_params")


# ===== 2. 多時段績效 ==========================================================

def cagr(start_val: float, end_val: float, days: int) -> float:
    """計算 CAGR；days < 30 回 nan（樣本太少）"""
    if days < 30 or start_val <= 0 or end_val <= 0:
        return float("nan")
    years = days / 365.0
    return (end_val / start_val) ** (1.0 / years) - 1.0


def trailing_returns_strategy(equity: pd.Series) -> dict:
    """從 equity_curve 切出多時段績效。
    回傳 {6m, 1y, 2y, 3y, 5y, 10y, all}: CAGR
    """
    if equity.empty or len(equity) < 30:
        return {}
    end_dt = equity.index[-1]
    end_val = equity.iloc[-1]
    out = {}
    period_map = [
        ("6m", 180), ("1y", 365), ("2y", 730), ("3y", 1095),
        ("5y", 1825), ("10y", 3650),
    ]
    for label, days in period_map:
        cutoff = end_dt - pd.Timedelta(days=days)
        if cutoff < equity.index[0]:
            continue
        sliced = equity[equity.index >= cutoff]
        if len(sliced) < 5:
            continue
        start_val = sliced.iloc[0]
        actual_days = (end_dt - sliced.index[0]).days
        out[label] = cagr(start_val, end_val, actual_days)
    # all-time
    out["all"] = cagr(equity.iloc[0], end_val, (end_dt - equity.index[0]).days)
    return out


def trailing_returns_close(close_series: pd.Series) -> dict:
    """從 close 序列計算 BNH 多時段績效（買進長持）。"""
    if close_series.empty or len(close_series) < 30:
        return {}
    end_dt = close_series.index[-1]
    end_val = close_series.iloc[-1]
    out = {}
    for label, days in [("6m", 180), ("1y", 365), ("2y", 730),
                          ("3y", 1095), ("5y", 1825), ("10y", 3650)]:
        cutoff = end_dt - pd.Timedelta(days=days)
        if cutoff < close_series.index[0]:
            continue
        sliced = close_series[close_series.index >= cutoff]
        if len(sliced) < 5:
            continue
        actual_days = (end_dt - sliced.index[0]).days
        out[label] = cagr(sliced.iloc[0], end_val, actual_days)
    out["all"] = cagr(close_series.iloc[0], end_val,
                       (end_dt - close_series.index[0]).days)
    return out


# ===== 3. 個股回測 ============================================================

_BENCHMARK_CACHE = {}


def benchmark_0050_returns() -> dict:
    """0050 多時段 BNH（cache）"""
    if "data" in _BENCHMARK_CACHE:
        return _BENCHMARK_CACHE["data"]
    df = _load_adj_ohlcv("0050")
    if df is None or df.empty:
        _BENCHMARK_CACHE["data"] = {}
        return {}
    out = trailing_returns_close(df["close"])
    _BENCHMARK_CACHE["data"] = out
    return out


def run_full_backtest(stock_id: str, template: str, params: dict,
                      start_date: str, end_date: str,
                      max_position_pct: float):
    """執行完整回測，回傳 result + bnh_close。

    一律用 adj_close 跑（含限價單機制下的 OCO 比較）：
      - 與 BNH / 0050 同期 CAGR 比較公平（都含複利）
      - 限價單 target 算出來與 adj 的 high/low 直接可比
    """
    df_adj = _load_adj_ohlcv(stock_id)
    if df_adj is None or len(df_adj) < 50:
        return None, None

    gen_fn = TEMPLATE_GENERATORS.get(template)
    if gen_fn is None:
        return None, df_adj["close"]
    sig_df = gen_fn(df_adj, params)

    cfg = _load_strategy_cfg()
    bt_cfg = BacktestConfig(
        fees=cfg["fees"],
        start_date=start_date,
        end_date=end_date,
        initial_capital=1_000_000,
        max_position_pct=max_position_pct,
    )
    bt = Backtester(bt_cfg)
    res = bt.run_per_stock(stock_id, df_adj, sig_df)
    return res, df_adj["close"]


# ===== 4. HTML 模板 ===========================================================

PICO_CDN = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"
ALPINE_CDN = "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"


def html_head(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-Hant" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="{PICO_CDN}">
<style>
:root {{ --pico-spacing: 0.8rem; --pico-font-size: 95%; }}
body {{ padding: 0.5rem 0.7rem; }}
main {{ padding-top: 0; }}
header h1 {{ margin-bottom: 0.2rem; font-size: 1.4rem; }}
.subtitle {{ color: var(--pico-muted-color); margin-bottom: 1rem; font-size: 0.85rem; }}
.banner {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;
           padding: 0.7rem; border-radius: 8px; background: var(--pico-card-background-color);
           border: 1px solid var(--pico-card-border-color); margin-bottom: 1rem; }}
.banner div {{ text-align: center; font-size: 0.85rem; }}
.banner div strong {{ display: block; font-size: 1.3rem; }}
.tabs {{ display: flex; gap: 0.3rem; margin-bottom: 0.8rem; flex-wrap: wrap; }}
.tabs button {{ padding: 0.4rem 0.9rem; font-size: 0.9rem; }}
.tabs button[aria-pressed=true] {{ background: var(--pico-primary); color: white; }}
input[type=search] {{ margin-bottom: 0.6rem; }}
table {{ font-size: 0.85rem; }}
table th {{ cursor: pointer; user-select: none; white-space: nowrap; padding: 0.4rem 0.3rem !important; }}
table th:hover {{ background: var(--pico-secondary-background); }}
table td {{ padding: 0.4rem 0.3rem !important; vertical-align: middle; }}
/* 台股配色：紅漲綠跌（與美股相反）；Tier 抽離成藍/靛/橘以免混淆 */
.action-buy {{ color: #d62828; font-weight: bold; white-space: nowrap; }}     /* BUY = 看多 = 紅 */
.action-sell {{ color: #2a9d3f; font-weight: bold; white-space: nowrap; }}    /* SELL = 看空 = 綠 */
.tier-S, .tier-A {{ color: #1a73e8; font-weight: bold; }}                      /* 高信心 = 藍 */
.tier-B {{ color: #6f4ab8; font-weight: bold; }}                                /* 靛 */
.tier-C {{ color: #ff8c00; }}                                                    /* 橘 */
.tier-F {{ color: #999; }}                                                       /* 灰 */
.rsi-hot {{ color: #ff8c00; font-weight: bold; }}                              /* 過熱 = 警告橘（不用紅，避免與「漲」混淆）*/
.rsi-cool {{ color: #1a73e8; }}                                                  /* 過冷 = 藍（中性）*/
.trend-bull {{ color: #d62828; font-weight: bold; white-space: nowrap; }}     /* 多 = 紅 */
.trend-bear {{ color: #2a9d3f; font-weight: bold; white-space: nowrap; }}     /* 空 = 綠 */
.order-cell {{ font-size: 0.78rem; white-space: nowrap; }}
.order-buy {{ color: #d62828; font-weight: bold; }}
.order-hold {{ color: #555; }}
.in-pos {{ font-size: 0.9rem; }}
details.legend {{ margin-top: 1.5rem; padding: 0.7rem 1rem;
                   background: var(--pico-card-background-color);
                   border: 1px solid var(--pico-card-border-color);
                   border-radius: 8px; }}
details.legend summary {{ cursor: pointer; font-weight: 600;
                           color: var(--pico-primary); list-style: none; }}
details.legend summary::-webkit-details-marker {{ display: none; }}
details.legend summary::before {{ content: "▶ "; transition: transform 0.2s; display: inline-block; }}
details.legend[open] summary::before {{ transform: rotate(90deg); }}
.legend-body {{ font-size: 0.85rem; margin-top: 0.5rem; }}
.legend-body p {{ margin-bottom: 0.3rem; margin-top: 0.7rem; }}
.legend-body ul {{ margin: 0; padding-left: 1.2rem; }}
.legend-body li {{ margin-bottom: 0.3rem; line-height: 1.6; }}
a.stock-link {{ color: var(--pico-primary); text-decoration: none; font-weight: 600; }}
a.stock-link:hover {{ text-decoration: underline; }}
.stock-card {{ padding: 1rem; border-radius: 8px;
                background: var(--pico-card-background-color);
                border: 1px solid var(--pico-card-border-color);
                margin-bottom: 1rem; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                 gap: 0.5rem; }}
.metric {{ padding: 0.6rem; background: rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.08); border-radius: 6px; }}
.metric strong {{ display: block; font-size: 1.15rem; color: var(--pico-primary);
                   font-weight: 700; margin-bottom: 0.2rem; }}
.metric small {{ color: #555; font-size: 0.78rem; }}
@media (prefers-color-scheme: dark) {{
  .metric {{ background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.12); }}
  .metric small {{ color: #aaa; }}
}}
.back-link {{ font-size: 0.9rem; margin-bottom: 0.7rem; display: inline-block; }}
.pos-cagr {{ color: #d62828; }}    /* 正報酬 = 紅（台股配色）*/
.neg-cagr {{ color: #2a9d3f; }}    /* 負報酬 = 綠 */
@media (max-width: 600px) {{
  .banner {{ grid-template-columns: 1fr; }}
  table {{ font-size: 0.75rem; }}
  .metric-grid {{ grid-template-columns: 1fr 1fr; }}
}}
</style>
</head>
<body>
<main class="container">
"""


def html_tail() -> str:
    return f"""</main>
<script defer src="{ALPINE_CDN}"></script>
</body>
</html>
"""


# ===== 5. 首頁渲染 ============================================================

def cell_action(action: str) -> str:
    if action == "BUY":
        return f'<span class="action-buy">🟢 BUY</span>'
    if action == "SELL":
        return f'<span class="action-sell">🔴 SELL</span>'
    return action


def cell_tier(tier: str) -> str:
    return f'<span class="tier-{tier}">{tier}</span>'


def cell_rsi(rsi_str: str) -> str:
    try:
        v = int(rsi_str)
        if v >= 75:
            return f'<span class="rsi-hot">{v} 🔥</span>'
        if v <= 30:
            return f'<span class="rsi-cool">{v} ❄️</span>'
        return str(v)
    except (ValueError, TypeError):
        return rsi_str


def render_index_html(accounts_data: dict) -> str:
    """產 /index.html

    accounts_data = {
       "Takeshi":  [{"sid":"1301", "name":"台塑", "close":"51.5", "action":"HOLD",
                    "tier":"F", "pos":"—", "rsi":"56", "trend":"[多頭]", "regime":"BULL"}, ...],
       "Katie":    [...],
       "universe": [...]
    }
    """
    # 各帳戶摘要：BUY/SELL 數、過熱數
    summaries = {}
    for acc, rows in accounts_data.items():
        buy = sum(1 for r in rows if r["action"] == "BUY")
        sell = sum(1 for r in rows if r["action"] == "SELL")
        hot = sum(1 for r in rows
                   if (r["rsi"].isdigit() and int(r["rsi"]) >= 75))
        summaries[acc] = {"buy": buy, "sell": sell, "hot": hot, "n": len(rows)}

    # 第一個帳戶的摘要顯示在 banner（總和也可以）
    total_buy = sum(s["buy"] for s in summaries.values())
    total_sell = sum(s["sell"] for s in summaries.values())
    total_hot = sum(s["hot"] for s in summaries.values())

    # 把 accounts_data 轉成 JSON 給 Alpine
    accounts_json = json.dumps(accounts_data, ensure_ascii=False)

    body = f"""<header>
<h1>📊 台股策略訊號</h1>
<div class="subtitle">最後更新：<strong>{TODAY}</strong> · 點任一檔股票看歷史回測</div>
</header>

<div class="banner">
  <div><small>🔴 今日 BUY</small><strong>{total_buy}</strong></div>
  <div><small>🟢 今日 SELL</small><strong>{total_sell}</strong></div>
  <div><small>🔥 RSI 過熱 (≥75)</small><strong>{total_hot}</strong></div>
</div>

<div x-data='{{
  accounts: {accounts_json},
  current: "{list(accounts_data.keys())[0]}",
  search: "",
  sortKey: "",
  sortDesc: false,
  filtered() {{
    let rows = this.accounts[this.current] || [];
    let q = this.search.trim().toLowerCase();
    if (q) {{
      rows = rows.filter(r => r.sid.includes(q) ||
                              (r.name||"").toLowerCase().includes(q));
    }}
    if (this.sortKey) {{
      const k = this.sortKey;
      rows = [...rows].sort((a,b) => {{
        let va = a[k], vb = b[k];
        const na = parseFloat(va), nb = parseFloat(vb);
        if (!isNaN(na) && !isNaN(nb)) {{ va = na; vb = nb; }}
        if (va < vb) return this.sortDesc ? 1 : -1;
        if (va > vb) return this.sortDesc ? -1 : 1;
        return 0;
      }});
    }}
    return rows;
  }},
  sort(k) {{
    if (this.sortKey === k) this.sortDesc = !this.sortDesc;
    else {{ this.sortKey = k; this.sortDesc = false; }}
  }},
  arrow(k) {{
    if (this.sortKey !== k) return "";
    return this.sortDesc ? " ↓" : " ↑";
  }}
}}'>

<div class="tabs">
"""

    for acc, summary in summaries.items():
        body += (f'  <button @click="current=\'{acc}\'; sortKey=\'\'" '
                  f':aria-pressed="current===\'{acc}\'">'
                  f'{acc} <small>({summary["n"]})</small></button>\n')

    body += """</div>

<input type="search" x-model="search" placeholder="🔍 搜尋代號或名稱（如 2330、台積電）">

<table>
<thead>
<tr>
  <th @click="sort('sid')">股票<span x-text="arrow('sid')"></span></th>
  <th @click="sort('in_pos')">在倉<span x-text="arrow('in_pos')"></span></th>
  <th @click="sort('name')">名稱<span x-text="arrow('name')"></span></th>
  <th @click="sort('close')">收盤<span x-text="arrow('close')"></span></th>
  <th @click="sort('action')">動作<span x-text="arrow('action')"></span></th>
  <th @click="sort('tier')">Tier<span x-text="arrow('tier')"></span></th>
  <th @click="sort('pos')">倉位<span x-text="arrow('pos')"></span></th>
  <th>掛單</th>
  <th @click="sort('rsi')">RSI<span x-text="arrow('rsi')"></span></th>
  <th @click="sort('trend')">趨勢<span x-text="arrow('trend')"></span></th>
</tr>
</thead>
<tbody>
<template x-for="r in filtered()" :key="r.sid + '-' + current">
<tr>
  <td><a class="stock-link" :href="`stock/${r.sid}.html`" x-text="r.sid"></a></td>
  <td x-html="cellInPos(r.in_pos)"></td>
  <td x-text="r.name"></td>
  <td x-text="r.close"></td>
  <td x-html="cellAction(r.action)"></td>
  <td x-html="cellTier(r.tier)"></td>
  <td x-text="r.pos"></td>
  <td class="order-cell" x-html="cellOrder(r.order)"></td>
  <td x-html="cellRsi(r.rsi)"></td>
  <td x-html="cellTrend(r.trend)"></td>
</tr>
</template>
</tbody>
</table>
</div>

<script>
function cellAction(a) {
  if (a === "BUY") return '<span class="action-buy">🔴 BUY</span>';
  if (a === "SELL") return '<span class="action-sell">🟢 SELL</span>';
  return a;
}
function cellTier(t) {
  return `<span class="tier-${t}">${t}</span>`;
}
function cellRsi(r) {
  const v = parseInt(r);
  if (isNaN(v)) return r;
  if (v >= 75) return `<span class="rsi-hot">${v} 🔥</span>`;
  if (v <= 30) return `<span class="rsi-cool">${v} ❄️</span>`;
  return v;
}
function cellTrend(t) {
  if (t === "多頭") return '<span class="trend-bull">▲ 多</span>';
  if (t === "空頭") return '<span class="trend-bear">▼ 空</span>';
  return t || "—";
}
function cellInPos(p) {
  if (p === "yes") return '<span class="in-pos">✅</span>';
  return '<span style="color:#bbb">·</span>';
}
function cellOrder(o) {
  if (!o || o === "—") return '<span style="color:#999">—</span>';
  // BUY 訊號："買 X"
  if (o.startsWith("買")) {
    return '<span class="order-buy">' + o + '</span>';
  }
  // 在倉中的 TP / SL 顯示
  if (o.startsWith("TP")) {
    return '<span class="order-hold">' + o + '</span>';
  }
  return o;
}
</script>

<details class="legend">
<summary>📖 符號說明</summary>
<div class="legend-body">
<p><strong>動作</strong></p>
<ul>
  <li><span class="action-buy">🔴 BUY</span> — 進場訊號（台股配色：紅 = 多/漲）</li>
  <li><span class="action-sell">🟢 SELL</span> — 出場訊號（綠 = 空/跌）</li>
  <li>HOLD — 觀望，無進出建議</li>
</ul>
<p><strong>掛單</strong>（限價單機制 v0.1，目前 low_vol_pullback / mean_reversion 才有）</p>
<ul>
  <li>買 X → 隔日預掛限價買在 X 元，盤中觸及才成交</li>
  <li>TP X / SL Y → 在倉建議：<b>TP</b>（Take Profit，停利）X 元觸及就賣；<b>SL</b>（Stop Loss，停損）Y 元跌破就賣</li>
  <li>— → 該標的無限價單訊號（其他 template 預設 T+1 開盤市價成交）</li>
</ul>
<p><strong>Tier（策略信心等級）</strong></p>
<ul>
  <li><span class="tier-S">S</span> — 最高信心（倉位上限 100%）</li>
  <li><span class="tier-A">A</span> — 高信心（倉位上限 50%）</li>
  <li><span class="tier-B">B</span> — 中等信心（倉位上限 30%）</li>
  <li><span class="tier-C">C</span> — 普通信心（倉位上限 15%）</li>
  <li><span class="tier-F">F</span> — 策略無利可圖，不建議持有</li>
  <li>BS / BA / BB → BNH_S/A/B 長持替代（tier=F 但長期買進長持有效）</li>
  <li>* → 倉位來自 BNH 評估</li>
</ul>
<p><strong>趨勢與 RSI</strong></p>
<ul>
  <li><span class="trend-bull">▲ 多</span> — 多頭排列（Close > MA200 且 MA50 > MA200）</li>
  <li><span class="trend-bear">▼ 空</span> — 空頭排列</li>
  <li><span class="rsi-hot">RSI 🔥</span> — 過熱（≥75，警告超買）</li>
  <li><span class="rsi-cool">RSI ❄️</span> — 過冷（≤30，可能反彈）</li>
</ul>
<p><strong>在倉狀態</strong></p>
<ul>
  <li><span class="in-pos">✅</span> — 真實持有（從 trades_帳戶.csv 推算）</li>
  <li>· — 未持有 / 觀察中</li>
</ul>
<p><strong>Regime（大盤環境）</strong></p>
<ul>
  <li>BULL — 大盤多頭（0050 在 MA200 之上）</li>
  <li>BEAR — 大盤空頭</li>
  <li>NEUTRAL — 中性</li>
</ul>
</div>
</details>

<footer style="margin-top:1.5rem; text-align:center; color: var(--pico-muted-color); font-size:0.8rem;">
  <p>策略由 auto_iterate 對每檔獨立優化 · Tier 越前面信心越高 · F-tier 不建議持有</p>
</footer>
"""
    return html_head("台股策略訊號") + body + html_tail()


# ===== 6. 個股頁渲染 ===========================================================

def fmt_pct(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    cls = "pos-cagr" if x >= 0 else "neg-cagr"
    return f'<span class="{cls}">{x*100:+.1f}%</span>'


def fmt_num(x, fmt=".1f", suffix=""):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"{x:{fmt}}{suffix}"


def render_stock_html(sid: str, name: str, rec: dict,
                       res, bnh_close,
                       bench_returns: dict) -> str:
    """產 /stock/{sid}.html"""
    # 多時段績效
    strat_returns = trailing_returns_strategy(res.equity_curve) if res else {}
    bnh_returns = trailing_returns_close(bnh_close) if bnh_close is not None else {}

    # 樣式分類
    tier = rec.get("tier", "—")
    template_name = rec.get("template", "—")
    pos_max = (rec.get("position_pct_max", 0) or 0) * 100

    L = []
    L.append(f'<a href="../index.html" class="back-link">← 回首頁</a>')
    L.append(f'<header><h1>{sid} {name}</h1></header>')

    # 推薦卡片
    L.append('<div class="stock-card">')
    L.append('<h3>策略推薦</h3>')
    L.append('<div class="metric-grid">')
    L.append(f'<div class="metric"><strong>{tier}</strong><small>Tier</small></div>')
    L.append(f'<div class="metric"><strong>{pos_max:.0f}%</strong><small>倉位上限</small></div>')
    L.append(f'<div class="metric"><strong>{template_name}</strong><small>Template</small></div>')
    tradeable = "✅ 可交易" if rec.get("tradeable") else "⚠️ 不建議"
    L.append(f'<div class="metric"><strong>{tradeable}</strong><small>狀態</small></div>')
    L.append('</div>')

    # BNH info
    if rec.get("bnh_tier"):
        L.append(f'<p style="margin-top:0.8rem;">📌 BNH 長持 Tier: <strong>{rec["bnh_tier"]}</strong>'
                  f' · 倉位上限 {(rec.get("bnh_position_pct_max", 0) or 0)*100:.0f}%')
        if rec.get("bnh_cagr") is not None:
            L.append(f' · CAGR {rec["bnh_cagr"]*100:+.1f}%')
        L.append('</p>')
    L.append('</div>')

    # 多時段績效
    L.append('<div class="stock-card">')
    L.append('<h3>📈 多時段績效</h3>')
    L.append('<table>')
    L.append('<thead><tr><th>期間</th><th>策略 CAGR</th><th>同期 BNH CAGR</th>'
              '<th>同期 0050</th><th>策略 vs 0050</th></tr></thead>')
    L.append('<tbody>')
    period_labels = [("6m", "近半年"), ("1y", "近 1 年"), ("2y", "近 2 年"),
                       ("3y", "近 3 年"), ("5y", "近 5 年"), ("10y", "近 10 年"),
                       ("all", "全期")]
    for code, lbl in period_labels:
        s = strat_returns.get(code)
        b = bnh_returns.get(code)
        bench = bench_returns.get(code)
        alpha = (s - bench) if (s is not None and bench is not None
                                 and not math.isnan(s) and not math.isnan(bench)) else None
        L.append(f'<tr><td>{lbl}</td>'
                  f'<td>{fmt_pct(s)}</td>'
                  f'<td>{fmt_pct(b)}</td>'
                  f'<td>{fmt_pct(bench)}</td>'
                  f'<td>{fmt_pct(alpha)}</td></tr>')
    L.append('</tbody></table>')
    L.append('<small style="color:var(--pico-muted-color)">'
              '說明：策略 CAGR 取自 equity curve 在該期間的起點到最新值；'
              'BNH 為同期間單純買進長持；0050 為元大台灣 50 同期 BNH 對照。</small>')
    L.append('</div>')

    if res is None:
        L.append('<div class="stock-card"><p>本地完整回測：資料不足或 template 未支援。</p></div>')
    else:
        # 整體指標
        L.append('<div class="stock-card">')
        L.append('<h3>📊 整體回測指標</h3>')
        L.append('<div class="metric-grid">')
        L.append(f'<div class="metric"><strong>{res.n_trades}</strong><small>交易次數</small></div>')
        if res.n_trades > 0:
            L.append(f'<div class="metric"><strong>{res.win_rate*100:.0f}%</strong><small>勝率</small></div>')
            pf_v = res.profit_factor
            pf_str = "∞" if (math.isinf(pf_v) or math.isnan(pf_v)) else f"{pf_v:.2f}"
            L.append(f'<div class="metric"><strong>{pf_str}</strong><small>Profit Factor</small></div>')
            L.append(f'<div class="metric"><strong>{res.expectancy*100:+.2f}%</strong><small>每筆 Expectancy</small></div>')
            mdd = res.max_drawdown
            if not math.isnan(mdd):
                L.append(f'<div class="metric"><strong>{mdd*100:.1f}%</strong><small>最大回撤</small></div>')
            imc = res.in_market_cagr
            if not math.isnan(imc):
                L.append(f'<div class="metric"><strong>{imc*100:.0f}%</strong><small>持倉期 CAGR</small></div>')
            L.append(f'<div class="metric"><strong>{res.avg_hold_days:.0f}d</strong><small>平均持有</small></div>')
        L.append('</div></div>')

        # 年度交易分布
        if res.trades:
            L.append('<div class="stock-card">')
            L.append('<h3>📅 年度交易分布</h3>')
            L.append('<table>')
            L.append('<thead><tr><th>年份</th><th>筆數</th><th>勝率</th><th>平均</th><th>累積</th></tr></thead>')
            L.append('<tbody>')
            df_t = pd.DataFrame([{
                "year": t.entry_date.year,
                "pnl_pct": t.pnl_pct * 100,
            } for t in res.trades])
            grp = df_t.groupby("year")
            for yr, g in grp:
                wr = (g["pnl_pct"] > 0).mean() * 100
                avg = g["pnl_pct"].mean()
                tot = g["pnl_pct"].sum()
                avg_cls = "pos-cagr" if avg >= 0 else "neg-cagr"
                tot_cls = "pos-cagr" if tot >= 0 else "neg-cagr"
                L.append(f'<tr><td>{yr}</td><td>{len(g)}</td><td>{wr:.0f}%</td>'
                          f'<td class="{avg_cls}">{avg:+.2f}%</td>'
                          f'<td class="{tot_cls}">{tot:+.1f}%</td></tr>')
            L.append('</tbody></table></div>')

        # 最近交易
        if res.trades:
            recent = res.trades[-10:]
            L.append('<div class="stock-card">')
            L.append(f'<h3>📋 最近 {len(recent)} 筆交易</h3>')
            L.append('<table>')
            L.append('<thead><tr><th>進場</th><th>進場價</th><th>出場</th><th>出場價</th>'
                      '<th>報酬</th><th>持有</th></tr></thead>')
            L.append('<tbody>')
            for t in recent:
                cls = "pos-cagr" if t.pnl_pct >= 0 else "neg-cagr"
                L.append(f'<tr><td>{t.entry_date.strftime("%Y-%m-%d")}</td>'
                          f'<td>{t.entry_price:.1f}</td>'
                          f'<td>{t.exit_date.strftime("%Y-%m-%d")}</td>'
                          f'<td>{t.exit_price:.1f}</td>'
                          f'<td class="{cls}">{t.pnl_pct*100:+.2f}%</td>'
                          f'<td>{t.hold_days}d</td></tr>')
            L.append('</tbody></table></div>')

    return html_head(f"{sid} {name}") + "\n".join(L) + html_tail()


# ===== 7. main ================================================================

def _build_stock_names_from_watchlists() -> dict:
    """從 watchlists.yaml 註解解析人讀股名（最準），過濾 name==sid 的偽值。"""
    import re
    path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
    names = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\s*-\s*"([^"]+)"\s*#\s*(.+?)(?:\s*\(|\s*$)', line)
                if m:
                    sid, name = m.group(1), m.group(2).strip()
                    if name and name != sid:
                        names[sid] = name
    except Exception:
        pass
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stocks", nargs="*", default=None,
                    help="指定股票代號（debug 用）；省略則處理 watchlists 全部")
    args = ap.parse_args()

    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(DOCS_STOCK_DIR, exist_ok=True)

    cfg = _load_strategy_cfg()
    bt_start = cfg["backtest"]["start_date"]
    bt_end = cfg["backtest"]["end_date"]

    rec_all = _load_recommendations()
    wl = load_watchlists()

    # 收集首頁 accounts_data
    accounts_data = {}
    main_accounts = ["Takeshi", "Katie", "universe"]  # 順序
    for acc in main_accounts:
        if acc not in wl:
            continue
        latest_md = os.path.join(BASE_DIR, "output", "reports", "latest",
                                   f"signals_{acc}.md")
        rows = parse_signals_md(latest_md)
        # 標準化 keys
        std_rows = []
        for r in rows:
            in_pos_raw = r.get("在倉", "—")
            std_rows.append({
                "sid": r.get("股票", ""),
                "name": r.get("名稱", "") or rec_all.get(r.get("股票", ""), {}).get("name", ""),
                "in_pos": "yes" if in_pos_raw == "✅" else "no",
                "close": r.get("收盤", "—"),
                "action": r.get("動作", "—"),
                "tier": r.get("Tier", "—"),
                "pos": r.get("倉位上限", "—"),
                "order": r.get("掛單目標", "—"),
                "rsi": r.get("RSI", "—"),
                "trend": r.get("個股趨勢", "—").replace("[", "").replace("]", ""),
                "regime": r.get("市場Regime", "—"),
            })
        accounts_data[acc] = std_rows

    # 1. 寫首頁
    print("產生首頁 /index.html ...")
    idx_html = render_index_html(accounts_data)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(idx_html)
    print(f"  ✓ /index.html ({len(idx_html)//1024} KB)")

    # 2. 收集所有需要產個股頁的股票
    if args.stocks:
        target_sids = args.stocks
    else:
        target_sids = set()
        for acc in main_accounts:
            for r in accounts_data.get(acc, []):
                if r["sid"]:
                    target_sids.add(r["sid"])
        target_sids = sorted(target_sids)

    print(f"\n產生 {len(target_sids)} 檔個股頁...")
    bench = benchmark_0050_returns()

    # 預載 watchlists 註解中的股名（修 final_report fallback name=sid 的 bug）
    wl_names = _build_stock_names_from_watchlists()

    success, failed = 0, []
    for sid in target_sids:
        try:
            rec = rec_all.get(sid, {})
            # 優先 watchlists 註解；其次 recommendations.name（過濾 name==sid 偽值）；fallback sid
            rec_name = rec.get("name") if rec else None
            if rec_name == sid:
                rec_name = None
            name = wl_names.get(sid) or rec_name or sid
            template = rec.get("template", "")
            pos_max = rec.get("position_pct_max", 0.0) or 0.0
            tradeable = rec.get("tradeable", False)

            res, bnh_close = None, None
            if template and tradeable:
                params = load_per_stock_params(sid, template)
                if params:
                    try:
                        res, bnh_close = run_full_backtest(
                            sid, template, params, bt_start, bt_end, pos_max)
                    except Exception as e:
                        print(f"  [{sid}] 回測失敗：{e}")
            if bnh_close is None:
                df = _load_adj_ohlcv(sid)
                if df is not None and not df.empty:
                    bnh_close = df["close"]

            html = render_stock_html(sid, name, rec, res, bnh_close, bench)
            path = os.path.join(DOCS_STOCK_DIR, f"{sid}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✓ {sid} {name}")
            success += 1
        except Exception as e:
            print(f"  ✗ {sid} 失敗：{e}")
            failed.append(sid)

    print(f"\n完成：{success} 檔成功，{len(failed)} 檔失敗")
    if failed:
        print(f"失敗清單：{failed}")
    print(f"\n本機預覽：開瀏覽器 file:///{DOCS_DIR.replace(os.sep, '/')}/index.html")


if __name__ == "__main__":
    main()
