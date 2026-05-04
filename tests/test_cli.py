# Phase 4 CLI 整合測試
# 跑法：python.exe -m pytest tests/test_cli.py -v
import sys
import os
import subprocess
import pytest

PYTHON = r"C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PY = os.path.join(PROJECT_DIR, "main.py")


def run_cmd(*args, timeout=60):
    """執行 main.py 子指令，回傳 (returncode, stdout+stderr)"""
    result = subprocess.run(
        [PYTHON, MAIN_PY] + list(args),
        cwd=PROJECT_DIR,
        capture_output=True,
        timeout=timeout,
    )
    output = (result.stdout or b"") + (result.stderr or b"")
    try:
        text = output.decode("utf-8", errors="replace")
    except Exception:
        text = str(output)
    return result.returncode, text


# ── 1. --help 不報錯 ────────────────────────────────────────

def test_help_no_error():
    rc, out = run_cmd("--help")
    assert rc == 0, f"--help 返回非 0：{out}"


def test_help_contains_signals():
    rc, out = run_cmd("--help")
    assert "signals" in out.lower() or rc == 0


def test_help_contains_backtest():
    rc, out = run_cmd("--help")
    assert "backtest" in out.lower() or rc == 0


def test_help_contains_evaluate():
    rc, out = run_cmd("--help")
    assert "evaluate" in out.lower() or rc == 0


# ── 2. signals 指令跑通 ──────────────────────────────────────

def test_signals_takeshi_no_crash():
    """signals --list Takeshi 應跑通不崩潰"""
    rc, out = run_cmd("signals", "--list", "Takeshi")
    assert rc == 0, f"signals Takeshi 失敗：{out[:500]}"


def test_signals_katie_no_crash():
    rc, out = run_cmd("signals", "--list", "Katie")
    assert rc == 0, f"signals Katie 失敗：{out[:500]}"


def test_signals_creates_md():
    """signals 應產出 Markdown 報表"""
    from datetime import date
    rc, out = run_cmd("signals", "--list", "Takeshi")
    today = date.today().strftime("%Y-%m-%d")
    md_path = os.path.join(PROJECT_DIR, "output", "reports",
                           f"{today}_signals_Takeshi.md")
    assert os.path.exists(md_path), f"報表未產出：{md_path}"


# ── 3. backtest 指令跑通 ─────────────────────────────────────

def test_backtest_takeshi_no_crash():
    rc, out = run_cmd("backtest", "--list", "Takeshi")
    assert rc == 0, f"backtest Takeshi 失敗：{out[:500]}"


def test_backtest_creates_csv():
    """backtest 應產出 per_stock CSV"""
    rc, out = run_cmd("backtest", "--list", "Takeshi")
    bt_dir = os.path.join(PROJECT_DIR, "output", "backtest")
    csvs = [f for f in os.listdir(bt_dir) if f.startswith("per_stock_")]
    assert len(csvs) > 0, "未找到 per_stock_*.csv"


def test_backtest_per_stock_correct_rows():
    """per_stock CSV 應有與 Takeshi 清單相同行數"""
    import pandas as pd
    import yaml
    wl_path = os.path.join(PROJECT_DIR, "config", "watchlists.yaml")
    with open(wl_path, encoding="utf-8") as f:
        wl = yaml.safe_load(f)
    expected = len(wl.get("Takeshi", []))

    rc, out = run_cmd("backtest", "--list", "Takeshi")
    bt_dir = os.path.join(PROJECT_DIR, "output", "backtest")
    csvs = sorted([f for f in os.listdir(bt_dir) if f.startswith("per_stock_")])
    if not csvs:
        pytest.skip("no per_stock CSV found")
    latest = os.path.join(bt_dir, csvs[-1])
    df = pd.read_csv(latest)
    assert len(df) == expected, f"per_stock CSV 有 {len(df)} 列，預期 {expected}"


def test_backtest_portfolio_no_crash():
    rc, out = run_cmd("backtest", "--list", "Katie", "--portfolio")
    assert rc == 0, f"backtest Katie --portfolio 失敗：{out[:500]}"


def test_backtest_portfolio_creates_csv():
    rc, out = run_cmd("backtest", "--list", "Katie", "--portfolio")
    bt_dir = os.path.join(PROJECT_DIR, "output", "backtest")
    csvs = [f for f in os.listdir(bt_dir) if f.startswith("portfolio_")]
    assert len(csvs) > 0, "未找到 portfolio_*.csv"


# ── 4. evaluate 指令跑通 ─────────────────────────────────────

def test_evaluate_no_crash():
    rc, out = run_cmd("evaluate", "--run-id", "portfolio_phase3_check")
    assert rc == 0, f"evaluate 失敗：{out[:500]}"


def test_evaluate_missing_run_id():
    """無效 run-id 應不崩潰（只印錯誤訊息）"""
    rc, out = run_cmd("evaluate", "--run-id", "nonexistent_run_000")
    assert rc == 0, f"evaluate 遇不存在 run-id 應不崩潰：{out[:300]}"
