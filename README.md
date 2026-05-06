# COMS7044A Reproducibility Assignment

Reproduction of:

> Miquel Ramírez and Hector Geffner. "Probabilistic Plan Recognition Using Off-the-Shelf Classical Planners." *Proceedings of AAAI-10*, 2010.

The paper poses goal recognition as a planning problem: given a domain, a set of candidate goals, and observations of an agent's actions, decide which goal the agent is pursuing. The method compiles each (problem, observations) pair into two modified planning problems and converts the cost difference into a Bayesian posterior over goals.

This repository implements that pipeline and runs it across the six benchmark domains reported in the paper.

---

## Setup

### Requirements

- WSL 2 (Ubuntu 22.04 or 24.04) — or any Linux box.
- Python 3.10+ — preinstalled on modern Ubuntu.
- Fast Downward — built from source (one-time, ~5 minutes).
- `bzip2` — needed by the campus/kitchen regenerators.

### One-time install

Inside WSL:

```bash
sudo apt update
sudo apt install -y cmake g++ make python3 git bzip2 tmux

git clone https://github.com/aibasel/downward.git ~/downward
cd ~/downward && ./build.py

echo 'export FAST_DOWNWARD=$HOME/downward/fast-downward.py' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
$FAST_DOWNWARD --help        # should print usage
```

### Smoke test

```bash
cd /mnt/c/path/to/COMS7044A_ReproducibilityAssignment
$FAST_DOWNWARD \
  benchmarks/intrusion-detection/domain.pddl \
  benchmarks/intrusion-detection/p10/planning/problem-p10-hyp_0.pddl \
  --search "astar(lmcut())"
```

You should see translation output, search output, and finally `Solution found.`

---

## Running the experiments

### 1. (Optional) Regenerate campus and kitchen benchmarks

The shipped `benchmarks/campus/` and `benchmarks/kitchen/` have 5 instances each. For more variance:

```bash
python3 tools/regenerate.py campus 10 0.0       # 10 instances per ratio, 0 noise
python3 tools/regenerate.py kitchen 10
```

### 2. Pre-compute optimal plans

The four domains that don't ship with `.soln` files (block-words, logistics, campus, kitchen) need them generated before recognition can sample observations:

```bash
python3 src/prp/precompute_plans.py
```

Idempotent — re-running skips problems whose `.soln` already exists. Use `--force` to overwrite. Takes a few minutes.

### 3. Run the recognition evaluation

```bash
tmux new -s eval
python3 src/prp/evaluate.py --out results.csv --beta 1.0 | tee eval.log
# Ctrl-B then D to detach. Reattach with: tmux attach -t eval
```

This is the long-running step (hours). Each trial involves up to 2K calls to Fast Downward, where K is the number of candidate goals for the instance. The CSV is appended to incrementally — interrupt and resume safely; previously-completed `(domain, instance, true_idx, obs_pct)` tuples are skipped.

### 4. (Group-of-3 extension) β sensitivity

Sweep β across multiple values, writing each to its own CSV:

```bash
for beta in 0.1 0.5 1.0 2.0 5.0; do
  python3 src/prp/evaluate.py --out results_b${beta}.csv --beta $beta
done
```

### 5. Inspect results

Quick aggregate by domain × observation percentage:

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('results.csv')
print(df.groupby(['domain','obs_pct'])['correct'].agg(['mean','std','count']).to_string())
"
```

---

## Repository layout

```
COMS7044A_ReproducibilityAssignment/
├── README.md
├── benchmarks/                  # PDDL inputs for the six paper domains
│   ├── block-words/
│   ├── campus/
│   ├── grid/
│   ├── intrusion-detection/
│   ├── kitchen/
│   └── logistics/
├── src/prp/                     # The recognition pipeline
│   ├── compiler.py              # PDDL → PDDL transform (Defn 2 / Prop 3)
│   ├── planner.py               # Fast Downward subprocess wrapper
│   ├── scoring.py               # Δ → posterior → prediction
│   ├── evaluate.py              # outer loop, writes results.csv
│   └── precompute_plans.py      # generate .soln files for missing domains
└── tools/                       # campus + kitchen regenerator
    ├── regenerate.py
    ├── campus/
    └── kitchen/
```

### `benchmarks/<domain>/` — one folder per planning domain

```
benchmarks/<domain>/
├── domain.pddl                  # action schemas (one per domain)
└── <instance>/                  # one or more problem instances
    ├── hyps.dat                 # candidate goals, one per line
    ├── obs.dat                  # campus/kitchen only: pre-sampled observations
    ├── real_hyp.dat             # campus/kitchen only: ground truth goal text
    ├── template.pddl            # campus/kitchen only: source template
    └── planning/
        ├── problem-<inst>-hyp_K.pddl    # one per candidate goal
        └── OPT_*hyp_K.soln              # optimal plan for each candidate
```

### `src/prp/<module>.py` — the pipeline

| Module | Role |
|---|---|
| `compiler.py` | Reads (domain, problem, observations) and writes the compliant (G+O) and non-compliant (G+Ō) compiled PDDL pairs by inserting breadcrumb fluents. |
| `planner.py` | Calls Fast Downward as a subprocess, parses `sas_plan` and `.soln` files, samples observations from a plan. |
| `scoring.py` | Pure math — turns a list of cost differences Δ into a posterior probability distribution over candidate goals. |
| `evaluate.py` | Walks `benchmarks/`, runs every recognition trial, appends one row per trial to `results.csv`. Resumable. |
| `precompute_plans.py` | One-off step: solves every original problem and writes its `.soln` so observation sampling works. |

### `tools/` — auxiliary regeneration

The campus and kitchen domains ship as Python generators rather than as a static set of PDDL instances. `tools/regenerate.py <domain> [args]` runs the generator and unpacks its output into the standard `benchmarks/<domain>/` shape. The original generators were Python 2; the copies under `tools/<domain>/` are Python 3 ports.

---

## File types

| Extension | Used for | Notes |
|---|---|---|
| `.pddl` | PDDL — planning domain or problem | Lisp s-expressions. Either a domain (action schemas, predicates) or a problem (objects, init, goal). |
| `.soln` | A plan | Plaintext: `; MetricValue N` header + one ground action per line. Produced by Fast Downward, sampled by the recognition pipeline as observations. |
| `.dat` | Plain text data | Convention varies per file: `hyps.dat` lists candidate goals (one line per goal); `obs.dat` lists observed actions; `real_hyp.dat` holds the ground-truth goal as text. |
| `.tar.bz2` | Bzip2-compressed tar | Transient output of campus/kitchen generators. `tools/regenerate.py` extracts and deletes them — none should persist in a clean tree. |
| `.py` | Python source | All your code under `src/prp/` and `tools/`. |
| `.md` | Markdown | This file. |
| `.csv` | Results | One row per trial: `(domain, instance, obs_pct, true_idx, predicted_idx, spread, correct, obs_count, deltas, posterior, beta)`. |

---

## Known corrections to the original benchmarks

Two PDDL files contained syntax errors that prevent Fast Downward's translator from parsing them. We patched both:

- **`benchmarks/block-words/domain.pddl`** — a typo `(holding ?x -block)` was missing a space between `-` and `block`. Fixed to `(holding ?x - block)`.
- **`benchmarks/kitchen/domain.pddl`** — the `:constants` block listed `cup`, `sugar`, and `bread` twice and contained `toaster` as both an `object` and a `useable`. Removed the duplicates; kept `toaster` as a `useable` only (its only use site).
