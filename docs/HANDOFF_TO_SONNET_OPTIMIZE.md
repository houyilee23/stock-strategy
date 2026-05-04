# Handoff: Opus → Sonnet（參數優化階段）

> 開新 Sonnet session 時，把這整份貼進去當第一個 prompt。**全自動執行，做完寫報告給 Opus。**

---

## 任務一句話

`config/strategy.yaml` 的 style1_pullback 參數從沒做過正規優化，全是經驗預設。
你要建一個 `optimize` 子命令、用 walk-forward 找出最佳參數、寫報告，**不要直接改 strategy.yaml**。

---

## 為什麼現在做

剛修完 P0-12.1（OHLC 還原一致性 bug）。在那之前，`close_adj` 對、但 `open/high/low` 是 raw 值，導致：
- C4 反轉條件 `close > open` 在歷史段幾乎永遠 False
- Signal mode 9 年只給 0~2 個訊號 / 個股
- 之前的所有參數都是在「壞資料」上看績效調的

現在資料對了，所有參數都應重新驗證一次。

---

## 必讀（按順序）

1. `docs/SPEC_strategy_system.md` — 策略設計（規格不變，只調參數）
2. `config/strategy.yaml` — 目前參數
3. `src/strategy/signals/style1_pullback.py` — 訊號邏輯
4. `src/strategy/runner.py` — backtest 入口（注意已修的 `_load_adj_ohlcv`）
5. `tests/test_sanity_gates.py` — 不能讓任何測試紅
6. `~/.claude/projects/C--TronFuture-lee-stock/memory/bugs_fixed.md` — 已知雷

---

## 範圍限制（嚴守）

| 可動 | 不可動 |
|---|---|
| `style1_pullback.*` 全部子參數 | `fees.*`（成本模型固定） |
| 新增 `src/strategy/optimize/` 模組 | `regime.*`（regime 邏輯不調） |
| 新增 `main.py optimize` 子命令 | `style2_momentum.*`（這次先不碰） |
| 寫到 `output/optimize/{run_id}/` | `config/strategy.yaml`（**只讀**，不要寫） |
| 新增 `tests/test_optimize.py` | `data/`、`config/watchlists.yaml` |

---

## 階段 A：建 optimize 模組（搭建）

### A.1 依賴

`optuna` 已在 conda env，直接 `import optuna` 即可。Python 路徑：
```
C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe
```

### A.2 模組結構

```
src/strategy/optimize/
  __init__.py
  search_space.py      # 定義可調參數的範圍與型別
  objective.py         # 把一組 params 轉成績效分數
  walk_forward.py      # 切時間窗、做 in-sample / out-of-sample
  runner.py            # optuna study 包裝器
```

### A.3 search_space.py 建議內容

```python
# 12 個可調參數，類型與範圍依據 docs/SPEC_strategy_system.md 與經驗
SEARCH_SPACE = {
    # 趨勢過濾（保守，動範圍小）
    "ma_long":          {"type": "categorical", "choices": [150, 200, 250]},
    "ma_short":         {"type": "categorical", "choices": [30, 50, 100]},
    # 回檔判斷
    "rsi_period":       {"type": "categorical", "choices": [10, 14, 21]},
    "rsi_oversold":     {"type": "int",  "low": 25, "high": 50, "step": 5},
    "bollinger_period": {"type": "categorical", "choices": [15, 20, 25]},
    "bollinger_k":      {"type": "float", "low": 1.5, "high": 2.5, "step": 0.25},
    # 量能
    "volume_ma_period": {"type": "categorical", "choices": [10, 20, 30]},
    "volume_min_ratio": {"type": "float", "low": 0.5, "high": 1.5, "step": 0.1},
    # 出場
    "atr_period":       {"type": "categorical", "choices": [10, 14, 20]},
    "atr_stop_k":       {"type": "float", "low": 1.5, "high": 3.5, "step": 0.25},
    "trend_break_days": {"type": "int",  "low": 1, "high": 5, "step": 1},
    "rsi_overbought":   {"type": "int",  "low": 70, "high": 85, "step": 5},
    "max_hold_days":    {"type": "categorical", "choices": [60, 90, 120, 180, 240]},
}
```

> **設計理由**：12 個參數 × optuna TPESampler，建議 trials 200~400。Grid search 太大（>10^6 組合），TPE 會聚焦在好區域。

### A.4 objective.py 設計

```python
def objective(trial, universe, train_start, train_end, base_cfg):
    """
    回傳：要最大化的分數
    建議：加權後的中位數 PF，並對「廢策略」打懲罰
    """
    params = sample_from_space(trial)  # 從 SEARCH_SPACE 採一組
    cfg = deep_merge(base_cfg, {"style1_pullback": params})
    
    # 跑 universe 上每檔個股的回測（時間段限定 train）
    per_stock = run_backtests(universe, cfg, train_start, train_end)
    
    # 基本健全性過濾
    n_active = (per_stock["n_trades"] >= 3).sum()
    if n_active < len(universe) * 0.3:    # 至少 30% 個股要有交易
        return -10.0                       # 太多檔零訊號 → 廢策略
    
    median_pf = per_stock.loc[per_stock["n_trades"] >= 3, "profit_factor"]\
                         .replace([np.inf, -np.inf], np.nan).dropna().median()
    median_dd = per_stock["max_drawdown"].abs().median()
    
    # 罰 MaxDD > 30%
    dd_penalty = max(0, median_dd - 0.30) * 5
    
    return median_pf - dd_penalty
```

### A.5 walk_forward.py

時間切法（避免 overfitting）：

```
全期間: 2017-01-01 ~ 2026-04-22 (約 9.3 年)

Train (in-sample):    2017-01-01 ~ 2022-12-31  (6 年, 用來優化)
Test  (out-of-sample): 2023-01-01 ~ 2026-04-22 (3.3 年, 不參與優化)
```

**最後一定要報出 in-sample 與 out-of-sample 的對照表，否則無法判斷 overfit**。

### A.6 universe 選擇

用 `data/adjusted/` 內所有個股（35 檔），不要 cherry-pick。
理由：在多檔上中位數穩健的參數，比在少數明星股上極佳的參數更有 generalization。

排除條件：
- `n_trades < 3` 的不算入 median PF（樣本不足噪音大）
- 但**個股零訊號**會反映在 `n_active` penalty 上

---

## 階段 B：CLI 整合

```bash
python main.py optimize \
    --style style1_pullback \
    --trials 300 \
    --train-end 2022-12-31 \
    --test-start 2023-01-01 \
    [--universe research|all|<sids>]
```

預設 `--universe all`（掃 `data/adjusted/`，跟 `backtest --all` 同邏輯）。

輸出：
```
output/optimize/{YYYYMMDD_HHMMSS}/
  trial_log.csv         # 每個 trial 的 params + score
  best_params.yaml      # 最好的一組（純供參考，不自動套用）
  walk_forward.md       # in-sample vs out-of-sample 對照
  per_stock_train.csv   # train 段每檔績效
  per_stock_test.csv    # test 段每檔績效
  summary.md            # 給 Opus 的報告
```

---

## 階段 C：自我驗證（必跑）

跑完後：

1. **既有測試不能紅**：
   ```bash
   python -m pytest tests/ -x -q
   ```

2. **Sanity check**（手寫一個 `tests/test_optimize.py`）：
   - search_space 的所有 key 都對應 strategy.yaml 的 style1_pullback 子鍵
   - 一組已知參數（current strategy.yaml）跑出的 score 和直接 backtest 的結果一致
   - trial 數 < 5 的快速測試能跑通

3. **Walk-forward 健全性**（在 summary.md 一定要報這幾項）：
   - 最佳參數的 in-sample score 和 out-of-sample score 差距
   - 若 out-of-sample 績效 < in-sample × 0.5 → 標記為「可能 overfit」
   - 若 best 和第 2~5 名 score 差 > 30% → 標記為「敏感性高，挑次優更穩」

---

## 完成標準

下列**全部**滿足才算完成（任何一項失敗 → 寫 `docs/BLOCKED_optimize.md` 停下）：

- [ ] `python main.py optimize --trials 5 --universe 0050,2330,2454` 能跑通（smoke test）
- [ ] `python main.py optimize --trials 300` 完整跑完，產出全部 6 個檔案
- [ ] `python -m pytest tests/ -x -q` 全綠
- [ ] `summary.md` 有以下章節：
  - 最佳參數 vs 目前 strategy.yaml 對照表
  - In-sample 與 out-of-sample 的 median PF / median MaxDD / n_active 對照
  - 前 5 名參數組的對照（看穩定性）
  - 是否有 overfit 警訊
  - **建議**：要不要把 best_params 套到 strategy.yaml？理由是？

---

## 給 Opus 的最終回報格式

寫到 `docs/OPTIMIZE_REPORT_TO_OPUS.md`，包含：

```markdown
# Optimize Round 1 報告

## TL;DR
- 跑了 N trials，耗時 X 分鐘
- 最佳 in-sample score = ?, out-of-sample score = ?
- overfit 警訊：有 / 無
- 建議套用 best_params：是 / 否（理由）

## 最佳參數 diff
| 參數 | 目前 | 最佳 | 變化 |
|---|---|---|---|

## In-Sample vs Out-of-Sample
| 指標 | Train (2017-2022) | Test (2023-2026) | 衰減 |
|---|---|---|---|
| median PF | | | |
| median MaxDD | | | |
| n_active | | | |

## Top-5 trial 對照
（看是不是「best 一枝獨秀」還是「top-5 都差不多」）

## 我的判斷
- 建議：...
- 不建議：...
- 下一步：...
```

---

## 不要做的事

1. **不要直接改 `config/strategy.yaml`** — 由使用者自己 review 後手動套用
2. **不要動 `config/watchlists.yaml`** — CLAUDE.md 明令是使用者資產
3. **不要優化 style2_momentum** — 這次只搞 style1
4. **不要為了拉高 score 把 search_space 收得很窄** — 範圍要合理，找到的參數要有意義
5. **不要 silent fail** — 任何 stock 跑不出來要 log 到 `output/errors/`

---

## 卡關時

寫 `docs/BLOCKED_optimize.md`，描述：
- 卡在哪一步
- 看到什麼 error / 不合理結果
- 試過什麼解法
- 你猜可能的原因

然後停下等 Opus。

---

開始吧。第一步：讀 `docs/SPEC_strategy_system.md` 第 4 節「style1 進出場條件」確認你理解策略，再開始建模組。
