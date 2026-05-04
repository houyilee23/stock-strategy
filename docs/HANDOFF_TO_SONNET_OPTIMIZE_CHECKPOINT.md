# Handoff: Optimize Trials Checkpointing 修復

> 開新 Sonnet session 用。**這是小範圍外科手術，不要重構，做完寫驗證報告。**

---

## 任務一句話

把 `optuna.create_study()` 加上 SQLite storage，讓 trials 即時落盤、可中斷續跑、可邊跑邊監看進度。

---

## 為什麼要做

目前 `src/strategy/optimize/walk_forward.py` 的 study 完全在記憶體，後果：
- 跑 300 trials 要 40 分鐘，中途 Ctrl+C 或當機 → 全沒了
- 沒辦法看當下進度、收斂曲線、參數分布
- 之後要跑 style2 / 擴大 universe，預估 3~6 小時，不能沒 checkpoint

---

## 範圍（嚴守）

| 改 | 不改 |
|---|---|
| `src/strategy/optimize/walk_forward.py`（study 建立 & callback） | objective.py、search_space.py |
| `src/strategy/optimize/runner.py`（CLI 入口加 --resume） | strategy.yaml |
| `main.py`（CLI 解析 --resume 參數） | 任何回測邏輯 |
| 新增測試 `tests/test_optimize_checkpoint.py` | best_params.yaml 結構 |

---

## 實作細節

### 1. `walk_forward.py` 修改

目前（約 line 79-82）：
```python
study = optuna.create_study(
    direction="maximize",
    sampler=optuna.samplers.TPESampler(n_startup_trials=min(50, n_trials // 3)),
)
```

改成：
```python
db_path = os.path.join(out_dir, "study.db")
storage_url = f"sqlite:///{db_path.replace(os.sep, '/')}"  # Windows 路徑要轉斜線
study_name = f"style1_{os.path.basename(out_dir)}"

study = optuna.create_study(
    study_name=study_name,
    storage=storage_url,
    direction="maximize",
    sampler=optuna.samplers.TPESampler(
        n_startup_trials=min(50, n_trials // 3),
        seed=42,  # 順便加 seed，重現性
    ),
    load_if_exists=True,
)

# 印出 dashboard 提示
print(f"  storage: {storage_url}")
print(f"  即時監看：optuna-dashboard {storage_url}")
```

**重要**：
- `load_if_exists=True` 是關鍵，沒這個 resume 會 raise 重複建立錯誤
- Windows 上 `sqlite:///C:/...` 三斜線後接磁碟代號（`/` 不要 `\`）

### 2. `walk_forward.py` 的 enqueue 邏輯要保護

目前 line 84-91 enqueue current_params 是無條件的。Resume 時不能再 enqueue（會造成重複）。改成：
```python
# 只在「全新 study」（沒任何 trial）時 enqueue current_params
if len(study.trials) == 0:
    current_params = _get_current_params(base_cfg)
    try:
        enqueue_params = {k: current_params[k] for k in SEARCH_SPACE if k in current_params}
        study.enqueue_trial(enqueue_params)
    except Exception:
        pass
else:
    print(f"  resume 模式：已有 {len(study.trials)} trials，從第 {len(study.trials)+1} 個續跑")
    current_params = _get_current_params(base_cfg)  # 還是要拿來算 diff
```

### 3. `walk_forward.py` 的 n_trials 處理

resume 時，`n_trials` 應該是「**還要再跑幾個**」而不是「總共要跑幾個」。

兩種設計擇一：
- **方案 A（推薦）**：`n_trials` 一律當「再跑幾個」，新 study 跑 300，resume 時打 50 就再跑 50
- 方案 B：`n_trials` 是「總數」，resume 時自動算差額

選 A。改 `study.optimize(...)` 時印一行：
```python
print(f"  本次將執行 {n_trials} trials（study 累計將達 {len(study.trials)+n_trials}）")
study.optimize(objective_fn, n_trials=n_trials, callbacks=[_callback])
```

### 4. `runner.py` 加 --resume 支援

修改 `run_optimize()` signature，加 `resume_run_id: str | None = None`：

```python
def run_optimize(
    style: str = "style1_pullback",
    n_trials: int = 300,
    train_end: str = "2022-12-31",
    test_start: str = "2023-01-01",
    train_start: str = "2017-01-01",
    test_end: str = "2026-04-22",
    universe_arg: str = "all",
    resume_run_id: str | None = None,   # 新增
) -> None:
    ...
    if resume_run_id:
        run_id = resume_run_id
        out_dir = os.path.join(BASE_DIR, "output", "optimize", run_id)
        if not os.path.exists(os.path.join(out_dir, "study.db")):
            print(f"[錯誤] 找不到 {out_dir}/study.db，無法 resume")
            return
        print(f"  → RESUME 模式 from run_id={run_id}")
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(BASE_DIR, "output", "optimize", run_id)
    
    os.makedirs(out_dir, exist_ok=True)
    ...
```

### 5. `main.py` 的 CLI 整合

找到 `cmd_optimize` 解析的地方，加：
```python
parser.add_argument("--resume", type=str, default=None,
                    help="續跑指定 run_id（例：--resume 20260423_124208 --trials 50）")
```

並把 `resume_run_id=args.resume` 傳給 `run_optimize()`。

### 6. callback 進度輸出強化

目前 callback 每 20 trials 印一次。加上「累計 trials」資訊：
```python
def _callback(study, trial):
    total = len(study.trials)
    if total % 20 == 0 or trial.number < 5:
        print(f"    trial {trial.number+1:>3}（累計 {total}）  "
              f"score={trial.value:.4f}  best={study.best_value:.4f}")
```

---

## 驗證（必跑）

### Test 1：smoke test（10 trials 看能不能落盤）
```bash
'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py optimize \
    --trials 10 --universe 0050,2330,2454
```

驗證點：
- [ ] `output/optimize/{run_id}/study.db` 檔案存在且 > 0 bytes
- [ ] `trial_log.csv` 有 10 列
- [ ] 終端有印出 `optuna-dashboard sqlite:///...` 提示

### Test 2：resume test（中斷續跑）
```bash
# 跑 5 trials
python main.py optimize --trials 5 --universe 0050,2330,2454
# 假設 run_id=20260423_HHMMSS

# resume 再跑 5 trials
python main.py optimize --resume 20260423_HHMMSS --trials 5 --universe 0050,2330,2454
```

驗證點：
- [ ] 第二次執行印出「resume 模式：已有 5 trials」
- [ ] `trial_log.csv` 最終有 10 列（不是 5 也不是 15）
- [ ] `study.db` 內 trial 編號連續 0~9

### Test 3：強制中斷恢復
```bash
# 跑 50 trials，按 Ctrl+C 中斷在第 ~20 trial
python main.py optimize --trials 50 --universe 0050,2330,2454,3017

# resume
python main.py optimize --resume {run_id} --trials 30
```

驗證點：
- [ ] 中斷時 study.db 已有 ~20 trials
- [ ] resume 後總共 ~50 trials（中斷的部分不重做）

### Test 4：既有測試不能紅
```bash
python -m pytest tests/ -x -q
```

### Test 5：寫單元測試 `tests/test_optimize_checkpoint.py`

至少涵蓋：
1. 全新 study：`load_if_exists=True` 不報錯
2. 已存在 study：第二次呼叫能讀回 trial 數
3. enqueue 邏輯：新 study 會 enqueue current_params，resume 不會

---

## 完成標準

全部勾選才算完成（任何一項失敗 → 寫 `docs/BLOCKED_optimize_checkpoint.md` 停下）：

- [ ] Test 1~5 全綠
- [ ] 之前的 run_id `20260423_124208` 不受影響（不要動已產出的檔）
- [ ] 在終端跑 `optuna-dashboard sqlite:///output/optimize/{某 run_id}/study.db` 能開瀏覽器看到進度（這個只要程式裝得動就跑得起來，沒裝就在報告寫一句「optuna-dashboard 套件可用 pip install optuna-dashboard 加裝」）

---

## 給 Opus 的回報格式

寫到 `docs/OPTIMIZE_CHECKPOINT_REPORT.md`，內容：

```markdown
# Optimize Checkpointing 修復報告

## 完成事項
- [x] walk_forward.py 加 SQLite storage
- [x] runner.py 支援 --resume
- [x] main.py CLI 解析 --resume
- [x] tests/test_optimize_checkpoint.py 新增

## 驗證結果
| Test | 結果 |
|---|---|
| smoke test (10 trials) | ✓ |
| resume test | ✓ |
| 強制中斷恢復 | ✓ |
| pytest 全套 | ✓ |

## 副作用
- （列出任何意外發現或調整）

## 給使用者的指引
- 全新優化：python main.py optimize --trials 300
- 中斷續跑：python main.py optimize --resume YYYYMMDD_HHMMSS --trials N
- 即時監看：optuna-dashboard sqlite:///output/optimize/{run_id}/study.db
```

---

## 不要做的事

1. **不要動 objective.py、search_space.py** — 這次只搞 storage
2. **不要重新跑優化** — 純基礎建設改動
3. **不要動 strategy.yaml** — Opus 還在跟使用者討論要不要套上次的 best_params
4. **不要刪 `output/optimize/20260423_124208/`** — Opus 還在分析
5. **不要為了測試方便寫 silent fallback** — storage 失敗就要噴錯，不要默默跑成記憶體模式

---

開始吧。先讀 `src/strategy/optimize/walk_forward.py` 和 `runner.py` 全文，確認你理解現有結構，再動手。
