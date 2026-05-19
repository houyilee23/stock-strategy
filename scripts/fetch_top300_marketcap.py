"""列出市值前 300 大的上市 + 上櫃公司（100% 官方來源，不用 FinMind）。

來源：
  TWSE 上市股價：openapi.twse.com.tw STOCK_DAY_ALL（當日全市場 close）
  TWSE 上市基本：openapi.twse.com.tw opendata/t187ap03_L（實收資本額）
  TPEX 上櫃合併：tpex.org.tw openapi/v1/tpex_mainboard_quotes（含 Capitals + Close）

市值 = (實收資本額 / 普通股面額 10) × close = 已發行股數 × close

輸出：
  config/top_300_marketcap.yaml      機器讀（sid: market_cap）
  docs/top_300_list.md               人類讀（含排名、名稱、市值、市場別）

用法：
  python scripts/fetch_top300_marketcap.py            # 預設 top 300
  python scripts/fetch_top300_marketcap.py --top 500  # 改 top N
"""
from __future__ import annotations
import argparse, os, sys, json, re
import requests
import urllib3
import pandas as pd
from datetime import date

urllib3.disable_warnings()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _safe_float(x) -> float | None:
    try:
        s = str(x).replace(",", "").strip()
        return float(s) if s and s not in ("--","---","N/A","") else None
    except Exception:
        return None


def fetch_twse_listed() -> pd.DataFrame:
    """TWSE 上市：合併 close + 實收資本額計算市值。"""
    # 1. 當日全市場 close
    r = requests.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
                     timeout=60, verify=False)
    r.raise_for_status()
    price = pd.DataFrame(r.json())
    price["close"] = price["ClosingPrice"].apply(_safe_float)
    price = price[["Code", "Name", "close"]].dropna()

    # 2. 上市公司基本資料（含實收資本額）
    r = requests.get("https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
                     timeout=60, verify=False)
    r.raise_for_status()
    base = pd.DataFrame(r.json())
    base = base.rename(columns={"公司代號":"Code", "公司簡稱":"Name",
                                "實收資本額":"capital_raw",
                                "普通股每股面額":"par_str"})
    base["capital"] = base["capital_raw"].apply(_safe_float)
    # 解析面額（"新台幣 10.0000元"）
    def _par(s: str) -> float:
        if not isinstance(s, str): return 10.0
        m = re.search(r"([\d.]+)", s)
        return float(m.group(1)) if m else 10.0
    base["par"] = base["par_str"].apply(_par)
    base = base[["Code", "Name", "capital", "par"]].dropna()
    base["shares"] = base["capital"] / base["par"]
    base = base[["Code", "shares"]]

    # 3. 合併計算市值
    df = price.merge(base, on="Code", how="inner")
    df["market_cap"] = df["close"] * df["shares"]
    df["market"] = "twse"
    return df[["Code", "Name", "close", "shares", "market_cap", "market"]]


def fetch_tpex_listed() -> pd.DataFrame:
    """TPEX 上櫃：mainboard_quotes 已含 Close + Capitals（股本）。"""
    r = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes",
                     timeout=60, verify=False)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    df["close"] = df["Close"].apply(_safe_float)
    df["capital"] = df["Capitals"].apply(_safe_float)
    df = df.rename(columns={"SecuritiesCompanyCode":"Code", "CompanyName":"Name"})
    df = df[["Code","Name","close","capital"]].dropna()
    # TPEX 面額預設 10（OpenAPI 沒給，多數 TPEX 股都是 10）
    df["shares"] = df["capital"] / 10.0
    df["market_cap"] = df["close"] * df["shares"]
    df["market"] = "tpex"
    return df[["Code","Name","close","shares","market_cap","market"]]


def write_outputs(top: pd.DataFrame, n: int):
    # YAML：sid 排序按市值降冪、附 market 與名稱
    import yaml
    yaml_path = os.path.join(BASE_DIR, "config", f"top_{n}_marketcap.yaml")
    out = []
    for i, row in top.iterrows():
        out.append({
            "rank": int(row["rank"]),
            "sid": str(row["Code"]),
            "name": row["Name"],
            "market": row["market"],
            "market_cap": int(row["market_cap"]),
            "close": float(row["close"]),
        })
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(out, f, allow_unicode=True, sort_keys=False)
    print(f"✓ 寫入 {yaml_path}")

    # Markdown
    md_path = os.path.join(BASE_DIR, "docs", f"top_{n}_list.md")
    today = date.today().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# 市值前 {n} 大上市/上櫃公司（{today}）")
    lines.append("")
    lines.append(f"_自動產出。來源：TWSE 上市 OpenAPI + TPEX 上櫃 OpenAPI。完全不使用 FinMind。_")
    lines.append("")
    lines.append("市值 = 已發行股數 × 當日收盤價")
    lines.append("")
    n_twse = (top["market"] == "twse").sum()
    n_tpex = (top["market"] == "tpex").sum()
    lines.append(f"- 總共 {n} 檔：TWSE 上市 **{n_twse}**、TPEX 上櫃 **{n_tpex}**")
    total_cap = top["market_cap"].sum()
    lines.append(f"- 累計市值：{total_cap/1e12:.2f} 兆元")
    lines.append("")
    lines.append("| Rank | 代號 | 名稱 | 市場 | 收盤 | 市值（億元）|")
    lines.append("|---:|---|---|:---:|---:|---:|")
    for _, row in top.iterrows():
        cap_yi = row["market_cap"] / 1e8  # 億元
        lines.append(f"| {int(row['rank'])} | {row['Code']} | {row['Name']} | "
                     f"{row['market'].upper()} | {row['close']:,.2f} | {cap_yi:,.0f} |")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ 寫入 {md_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=300, help="取前 N 名（預設 300）")
    args = ap.parse_args()

    print("=== 抓 TWSE 上市公司 ===")
    twse = fetch_twse_listed()
    print(f"  {len(twse)} 檔 TWSE 有完整 close + 股本")

    print("\n=== 抓 TPEX 上櫃公司 ===")
    tpex = fetch_tpex_listed()
    print(f"  {len(tpex)} 檔 TPEX 有完整 close + 股本")

    all_df = pd.concat([twse, tpex], ignore_index=True)
    all_df = all_df.sort_values("market_cap", ascending=False).reset_index(drop=True)
    all_df["rank"] = all_df.index + 1
    top = all_df.head(args.top).copy()

    write_outputs(top, args.top)

    print(f"\n=== Top {args.top} 摘要 ===")
    print(f"  市場分佈：TWSE {(top['market']=='twse').sum()}、TPEX {(top['market']=='tpex').sum()}")
    print(f"  最大市值：{top['market_cap'].iloc[0]/1e12:.2f} 兆 ({top['Code'].iloc[0]} {top['Name'].iloc[0]})")
    print(f"  第 {args.top} 名：{top['market_cap'].iloc[-1]/1e8:.0f} 億 ({top['Code'].iloc[-1]} {top['Name'].iloc[-1]})")


if __name__ == "__main__":
    main()
