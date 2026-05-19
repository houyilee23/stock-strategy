import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils import setup_logger, ensure_dirs

logger = setup_logger()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLISTS_PATH = os.path.join(BASE_DIR, "config", "watchlists.yaml")


def get_all_stock_ids(source: str = "raw") -> list:
    """自動掃描資料夾取得股票代號清單。
    source="raw"      → 掃 data/raw/        （fetch / update 用：抓資料的對象）
    source="adjusted" → 掃 data/adjusted/   （signals / backtest 用：策略可用對象）
    """
    folder = os.path.join(BASE_DIR, "data", source)
    if not os.path.exists(folder):
        return []
    ids = [f[:-4] for f in os.listdir(folder) if f.endswith(".csv")]
    return sorted(ids)


def get_watchlist(name: str) -> list:
    """從 config/watchlists.yaml 讀取指定清單"""
    import yaml
    if not os.path.exists(WATCHLISTS_PATH):
        print(f"[錯誤] 找不到 watchlists.yaml：{WATCHLISTS_PATH}")
        return []
    with open(WATCHLISTS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if name not in data:
        available = list(data.keys())
        print(f"[錯誤] 找不到清單 '{name}'，可用清單：{available}")
        return []
    # YAML 空 list（`Takeshi:` 後面留空）會被 parse 成 None，需 `or []` fallback
    ids = [str(s) for s in (data[name] or [])]
    print(f"  --list {name}：共 {len(ids)} 支股票 {ids}")
    return ids


def _get_exception_ids() -> set:
    """從 watchlists.yaml 讀取 exception 清單，--all 時絕對排除。"""
    import yaml
    if not os.path.exists(WATCHLISTS_PATH):
        return set()
    with open(WATCHLISTS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # YAML 中 `exception:` 後面留空時，data.get('exception') 會回傳 None
    # 必須 `or []` fallback，否則迭代會 TypeError（2026-05-19 修）
    return {str(s) for s in (data.get("exception") or [])}


def _parse_stock_ids(args, source: str = "raw"):
    """
    解析指令參數中的股票代號：
      --all          → 掃描 data/{source}/ 全部股票（排除 exception 清單）
      --list 名稱    → 讀取 config/watchlists.yaml 中的指定清單
      1301 2330 ...  → 直接使用指定代號
      （無參數）      → 回傳 None，由各模組自行決定

    source 預設 "raw"（fetch / update 用），策略類指令傳 "adjusted"
    確保只回測「資料完整可用」的股票，不會被尚未 fetch-adjusted 的孤兒 raw 拖累
    """
    args = list(args)

    if "--list" in args:
        idx = args.index("--list")
        if idx + 1 >= len(args):
            print("[錯誤] --list 後面需要指定清單名稱，例如：--list Takeshi")
            return []
        return get_watchlist(args[idx + 1])

    if "--all" in args:
        exception_ids = _get_exception_ids()
        all_ids = get_all_stock_ids(source=source)
        ids = [sid for sid in all_ids if sid not in exception_ids]
        excluded = len(all_ids) - len(ids)
        msg = f"  --all：偵測到 {len(ids)} 支股票（來源：data/{source}/）"
        if excluded:
            msg += f"，已排除 exception 清單 {excluded} 支"
        print(msg)
        return ids

    return args if args else None


def cmd_screen():
    from src.screener import run_screener
    run_screener()


def cmd_fetch(stock_ids=None):
    from src.fetcher import run_fetcher
    run_fetcher(stock_ids=stock_ids)


def cmd_fetch_adjusted(args: list):
    """P0-10：用 FinMind 抓還原股價到 data/adjusted/"""
    from src.finmind_fetcher import fetch_all, DEFAULT_START
    from datetime import date

    args = list(args)

    # 解析 --start / --end
    start_date = DEFAULT_START
    end_date = date.today().strftime("%Y-%m-%d")
    token = ""
    skip_existing = "--skip-existing" in args
    if "--skip-existing" in args:
        args.remove("--skip-existing")

    for flag in ("--start", "--end", "--token"):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                val = args[idx + 1]
                if flag == "--start":   start_date = val
                elif flag == "--end":   end_date = val
                elif flag == "--token": token = val
                args.pop(idx + 1)
                args.pop(idx)

    stock_ids = _parse_stock_ids(args)
    if not stock_ids:
        print("[錯誤] 請指定股票清單，例如：python main.py fetch-adjusted --all --start 2010-01-01")
        return

    print(f"\n  FinMind 還原股價抓取 — {len(stock_ids)} 檔")
    print(f"  期間：{start_date} ~ {end_date}")
    print(f"  目標：data/adjusted/ + data/dividends/\n")

    result = fetch_all(stock_ids, start_date, end_date, token=token,
                       skip_existing=skip_existing)
    print(f"\n  完成：{len(result['success'])} 檔成功，{len(result['failed'])} 檔失敗")
    if result["failed"]:
        print(f"  失敗清單：{result['failed']}")


def cmd_fetch_revenue(args: list):
    """抓 FinMind 月營收 (TaiwanStockMonthRevenue) 到 data/monthly_revenue/"""
    from src.strategy.auto_iterate.revenue_fetcher import (
        fetch_all_revenue, DEFAULT_START,
    )
    from datetime import date

    args = list(args)

    start_date = DEFAULT_START
    end_date = date.today().strftime("%Y-%m-%d")
    skip_existing = "--skip-existing" in args
    if "--skip-existing" in args:
        args.remove("--skip-existing")
    # 預設 skip_existing=True（避免 rate-limit）；可用 --force 覆寫
    force = "--force" in args
    if "--force" in args:
        args.remove("--force")
    if force:
        skip_existing = False
    elif not skip_existing:
        skip_existing = True  # 預設增量

    for flag in ("--start", "--end"):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                val = args[idx + 1]
                if flag == "--start":   start_date = val
                else:                   end_date = val
                args.pop(idx + 1)
                args.pop(idx)

    # 月營收只對 adjusted 中的真實股票有意義（不含 ETF）
    stock_ids = _parse_stock_ids(args, source="adjusted")
    if not stock_ids:
        print("[錯誤] 請指定股票清單，例如：python main.py fetch-revenue --all")
        return

    print(f"\n  FinMind 月營收抓取 — {len(stock_ids)} 檔")
    print(f"  期間：{start_date} ~ {end_date}")
    print(f"  目標：data/monthly_revenue/")
    print(f"  skip_existing：{skip_existing} (用 --force 覆寫)\n")

    result = fetch_all_revenue(stock_ids, start_date, end_date,
                               skip_existing=skip_existing)
    print(f"\n  完成：{len(result['success'])} 檔成功，{len(result['failed'])} 檔失敗")
    if result["failed"]:
        print(f"  失敗清單：{result['failed']}")


def cmd_positions(sub: str, args: list):
    from src.positions import run_positions
    run_positions(sub, args)


def cmd_inventory(args: list):
    """庫存進出分析（從 Excel 投資款.xlsx 同步 + 給建議）。

    用法：
        python main.py inventory                  # sync + 分析（預設 account=Personal）
        python main.py inventory --sync-only      # 只 sync 不分析
        python main.py inventory --analyze-only   # 不 sync 直接分析
        python main.py inventory --account X      # 指定 account
    """
    import subprocess
    args = list(args)
    account = "Takeshi"  # 5/19 改：直接同步 Excel 到 Takeshi 帳戶（signals 用同一份）
    sync_only = False
    analyze_only = False
    if "--account" in args:
        i = args.index("--account")
        if i + 1 < len(args):
            account = args[i + 1]
            args.pop(i + 1)
            args.pop(i)
    if "--sync-only" in args:
        sync_only = True
        args.remove("--sync-only")
    if "--analyze-only" in args:
        analyze_only = True
        args.remove("--analyze-only")

    if not analyze_only:
        print("\n" + "="*64)
        print("  STEP 1/2  從 Excel 同步交易紀錄")
        print("="*64)
        rc = subprocess.call([sys.executable,
                              os.path.join("scripts", "sync_positions_from_excel.py"),
                              "--account", account])
        if rc != 0:
            print(f"[ERR] sync 失敗 (rc={rc})")
            return

    if not sync_only:
        print("\n" + "="*64)
        print("  STEP 2/2  分析庫存進出點")
        print("="*64)
        rc = subprocess.call([sys.executable,
                              os.path.join("scripts", "inventory_analysis.py"),
                              "--account", account])
        if rc != 0:
            print(f"[ERR] analyze 失敗 (rc={rc})")


def cmd_signals(args: list):
    """訊號模式：對 watchlist 產出今日建議。"""
    from src.strategy.runner import run_signals
    # 策略類指令掃 adjusted，避免 raw 已抓但 adj 還沒算的股票被 silent skip
    stock_ids = _parse_stock_ids(args, source="adjusted")
    if not stock_ids:
        print("[錯誤] 請用 --list <帳戶> 指定清單，例如：python main.py signals --list Takeshi")
        return
    # 取 account name（--list 後的名稱）
    account_name = "Unknown"
    if "--list" in args:
        idx = list(args).index("--list")
        if idx + 1 < len(args):
            account_name = args[idx + 1]
    run_signals(stock_ids, account_name)


def cmd_backtest(args: list):
    """回測模式。"""
    from src.strategy.runner import run_backtest
    args = list(args)
    portfolio_mode = "--portfolio" in args
    if "--portfolio" in args:
        args.remove("--portfolio")

    # 解析 --start / --end
    start_date = None
    end_date = None
    for flag in ("--start", "--end"):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                val = args[idx + 1]
                if flag == "--start":
                    start_date = val
                else:
                    end_date = val
                args.pop(idx + 1)
                args.pop(idx)

    # 策略類指令掃 adjusted，避免 raw 已抓但 adj 還沒算的股票被 silent skip
    stock_ids = _parse_stock_ids(args, source="adjusted")
    if not stock_ids:
        print("[錯誤] 請用 --list <帳戶> 指定清單，例如：python main.py backtest --list Takeshi")
        return
    account_name = "Unknown"
    if "--list" in args:
        idx = list(args).index("--list")
        if idx + 1 < len(args):
            account_name = args[idx + 1]
    run_backtest(stock_ids, account_name, portfolio_mode, start_date, end_date)


def cmd_update(args: list):
    """每日例行 wrapper：先抓 raw，再抓 FinMind 還原資料 (一條指令搞定)"""
    args = list(args)
    stock_ids = _parse_stock_ids(args)
    if not stock_ids:
        print("[錯誤] 請用 --list <帳戶> 或 --all 指定股票")
        print("       例如：python main.py update --all")
        return

    print("\n" + "="*64)
    print("  STEP 1/2  抓 raw 股價 (TWSE / TPEX)")
    print("="*64)
    cmd_fetch(stock_ids=stock_ids)

    print("\n" + "="*64)
    print("  STEP 2/2  抓 FinMind 還原 (除權息 + 拆分事件 → adj close)")
    print("="*64)
    # 復用 cmd_fetch_adjusted 的參數解析（透過 args，但 list 已被 _parse_stock_ids 解掉了）
    # 直接呼叫 fetch_all
    from src.finmind_fetcher import fetch_all, DEFAULT_START
    from datetime import date
    fetch_all(stock_ids, start=DEFAULT_START,
              end=date.today().strftime("%Y-%m-%d"),
              token="", skip_existing=False)


def cmd_evaluate(args: list):
    """重算指標、產 Markdown 報表。"""
    from src.strategy.runner import run_evaluate
    args = list(args)
    run_id = None
    if "--run-id" in args:
        idx = args.index("--run-id")
        if idx + 1 < len(args):
            run_id = args[idx + 1]
    if not run_id:
        print("[錯誤] 請指定 --run-id，例如：python main.py evaluate --run-id 20260422_120000")
        return
    run_evaluate(run_id)


def cmd_optimize(args: list):
    """Walk-forward 參數優化。"""
    from src.strategy.optimize.runner import run_optimize
    args = list(args)

    def _get_flag(flag, default=None):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                val = args[idx + 1]
                args.pop(idx + 1)
                args.pop(idx)
                return val
        return default

    style       = _get_flag("--style",      "style1_pullback")
    trials_s    = _get_flag("--trials",     "300")
    train_end   = _get_flag("--train-end",  "2022-12-31")
    test_start  = _get_flag("--test-start", "2023-01-01")
    train_start = _get_flag("--train-start","2017-01-01")
    test_end    = _get_flag("--test-end",   "2026-04-22")
    universe    = _get_flag("--universe",   "all")
    resume      = _get_flag("--resume",     None)

    try:
        n_trials = int(trials_s)
    except (TypeError, ValueError):
        print(f"[錯誤] --trials 必須是整數，收到：{trials_s}")
        return

    run_optimize(
        style=style,
        n_trials=n_trials,
        train_end=train_end,
        test_start=test_start,
        train_start=train_start,
        test_end=test_end,
        universe_arg=universe,
        resume_run_id=resume,
    )


def cmd_auto_iterate(args: list):
    """auto_iterate: per-stock per-template optimisation."""
    from src.strategy.auto_iterate.runner import run_auto_iterate, TEMPLATE_NAMES

    def _get_flag(flag, default):
        args_list = list(args)
        if flag in args_list:
            idx = args_list.index(flag)
            if idx + 1 < len(args_list):
                return args_list[idx + 1]
        return default

    trials_s    = _get_flag("--trials-per-pair", "80")
    timeout_s   = _get_flag("--timeout-per-pair", "300")
    train_end   = _get_flag("--train-end",  "2023-12-31")
    test_start  = _get_flag("--test-start", "2024-01-01")
    train_start = _get_flag("--train-start","2017-01-01")
    test_end    = _get_flag("--test-end",   "2026-04-22")
    universe_s  = _get_flag("--universe",   "all")
    templates_s = _get_flag("--templates",  None)
    resume      = _get_flag("--resume",     None)
    wide_search = "--wide-search" in args

    try:
        n_trials = int(trials_s)
        timeout  = int(timeout_s)
    except (TypeError, ValueError) as e:
        print(f"[錯誤] 數值參數不合法：{e}")
        return

    # Resolve universe
    if universe_s == "all":
        universe = _parse_stock_ids(["--all"], source="adjusted")
        universe = [s for s in universe if s != "0050"]  # exclude market proxy
    elif "," in universe_s:
        universe = [s.strip() for s in universe_s.split(",")]
    else:
        universe = [universe_s]

    # Resolve templates
    if templates_s:
        tmap = {f"T{i+1}": n for i, n in enumerate(TEMPLATE_NAMES)}
        templates = []
        for t in templates_s.split(","):
            t = t.strip()
            templates.append(tmap.get(t, t))
    else:
        templates = None  # all

    run_auto_iterate(
        universe=universe,
        n_trials=n_trials,
        timeout_per_pair=timeout,
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
        templates_to_run=templates,
        resume_run_id=resume,
        wide_search=wide_search,
    )


USAGE = """
用法：
  python main.py screen                              執行股票篩選

  ── 抓資料（每天例行：直接用 update 一條搞定）─────────
  python main.py update --all                        ★ 一條搞定：raw + 還原（推薦每日用）
  python main.py update --list Katie                 只更新 Katie 清單

  ── 抓 raw 股價（TWSE / TPEX 直連）──────────────────
  python main.py fetch 1301 2330                     指定股票代號下載
  python main.py fetch --list Takeshi                下載 Takeshi 清單的股票
  python main.py fetch --all                         更新所有已下載股票的資料

  ── 抓還原股價（FinMind 免費 / 含拆分除權息）────────
  python main.py fetch-adjusted --list Katie         抓 Katie 清單的除權息+拆分事件 → 算 adj close
  python main.py fetch-adjusted --all                抓 watchlist 全部 80 檔
  python main.py fetch-adjusted --all --skip-existing  增量更新（已抓過的跳過）

  ── 抓月營收（FinMind 免費 / 台股獨有，每月 10 號前公布）─
  python main.py fetch-revenue --list Takeshi        抓 Takeshi 清單的月營收 (TaiwanStockMonthRevenue)
  python main.py fetch-revenue --all                 抓 adjusted 全部股票的月營收
  python main.py fetch-revenue --all --force         強制重抓（已存在也覆寫）

  ── 策略訊號 ──────────────────────────────────────────
  python main.py signals --list Takeshi              產出今日訊號建議（訊號模式）
  python main.py signals --list Katie                產出 Katie 清單今日訊號
  python main.py signals --all                       對 data/adjusted/ 全部股票產出今日訊號

  ── 策略回測 ──────────────────────────────────────────
  python main.py backtest --list Takeshi             訊號模式回測（單股層，per_stock CSV）
  python main.py backtest --list Takeshi --start 2017-01-01 --end 2024-12-31
  python main.py backtest --list Katie --portfolio   組合模式回測（portfolio CSV + equity）
  python main.py backtest --all                      對 data/adjusted/ 全部股票回測（自動排除 raw 已抓但 adj 未算的）

  ── 評價報表 ──────────────────────────────────────────
  python main.py evaluate --run-id 20260422_120000   重算指標、產 Markdown 報表

  ── 持倉管理 ──────────────────────────────────────────
  ※ 持倉記錄請直接編輯 data/trades_{帳戶}.csv（流水帳），格式：
     date,stock_id,action,price,shares,note
     2026-04-20,1301,BUY,53.4,1000,手動買入
     2026-05-10,1301,SELL,58.0,500,部分獲利
  預設帳戶：Takeshi（用 --account 切換）

  python main.py positions list                              列出目前持倉 + 更新快照 CSV
  python main.py positions list --account Katie              列出 Katie 持倉
  python main.py positions history                           列出歷史已實現損益（含手續費）
  python main.py positions open 1301 82.5 1000               手動開倉（寫入 trades_{帳戶}.csv）
  python main.py positions open 1301 82.5 1000 --date 2026-04-18  指定日期
  python main.py positions close 1301                        手動平倉（自動取最新收盤價）
  python main.py positions close 1301 95.0                   手動平倉並指定價格
  python main.py positions close 1301 --shares 500           部分平倉（指定股數）

  ── 庫存（Excel 同步）─────────────────────────────────
  從 Excel 「投資款.xlsx」的「交易紀錄」sheet 同步個人實際持倉，
  接著對每檔庫存給進出建議（依 tier + 損益 + 倉位偏離）：

  python main.py inventory                           sync + 分析（預設 account=Personal）
  python main.py inventory --sync-only               只 sync，不分析
  python main.py inventory --analyze-only            不 sync，只跑分析
  python main.py inventory --account MyAccount       指定帳戶名稱

  輸出：output/reports/inventory_advice_<account>.md / .csv

  ── 清單管理 ──────────────────────────────────────────
  清單設定檔：config/watchlists.yaml
  排除清單：exception（--all 時絕對排除）
"""


if __name__ == "__main__":
    ensure_dirs()
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
    elif args[0] == "screen":
        cmd_screen()
    elif args[0] == "fetch":
        stock_ids = _parse_stock_ids(args[1:])
        cmd_fetch(stock_ids=stock_ids)
    elif args[0] in ("fetch-adjusted", "fetch_adjusted"):
        cmd_fetch_adjusted(args[1:])
    elif args[0] in ("fetch-revenue", "fetch_revenue"):
        cmd_fetch_revenue(args[1:])
    elif args[0] == "update":
        cmd_update(args[1:])
    elif args[0] == "positions":
        if len(args) < 2:
            print("用法：python main.py positions <list|history|open|close> [參數]")
        else:
            cmd_positions(sub=args[1], args=args[2:])
    elif args[0] == "signals":
        cmd_signals(args[1:])
    elif args[0] == "backtest":
        cmd_backtest(args[1:])
    elif args[0] == "evaluate":
        cmd_evaluate(args[1:])
    elif args[0] == "optimize":
        cmd_optimize(args[1:])
    elif args[0] in ("auto_iterate", "auto-iterate"):
        cmd_auto_iterate(args[1:])
    elif args[0] == "inventory":
        cmd_inventory(args[1:])
    else:
        print(f"未知指令：{args[0]}")
        print(USAGE)
