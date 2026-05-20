# COMS7044A Reproducibility Assignment

Group:

- Okwukwechukwu Mbajiorgu (2430639)
- Zaid Ismail (1695814)
- Michael Anokye-Boateng (2382971)

School of Computer Science and Applied Mathematics, University of the Witwatersrand.

Independent reproduction of:

> Miquel Ramirez and Hector Geffner. *Probabilistic Plan Recognition Using Off-the-Shelf Classical Planners*. AAAI-10, 2010.

The paper turns goal recognition into a planning problem. For each candidate goal the recogniser asks an off-the-shelf classical planner two questions. What is the cheapest plan that includes the observed actions, and what is the cheapest plan that does not. The cost difference goes through a Boltzmann likelihood and Bayes' rule to give a posterior over the candidate goals.

This repository implements that pipeline and runs it across the six benchmark domains used in the paper.

## What's in the repo

```
.
├── README.md
├── SUMMARY.md                  notes on the summary CSV files
├── benchmarks/                 PDDL inputs for the six paper domains
│   ├── block-words/
│   ├── campus/
│   ├── grid/
│   ├── intrusion-detection/
│   ├── kitchen/
│   └── logistics/
├── src/prp/                    the recognition pipeline
│   ├── compiler.py             PDDL transform (compliant + non-compliant)
│   ├── planner.py              Fast Downward subprocess wrapper
│   ├── scoring.py              Boltzmann posterior
│   ├── evaluate.py             outer loop, writes results.csv
│   ├── precompute_plans.py     one-off step, generates missing .soln files
│   └── analyze.py              aggregates results.csv into summary tables
├── tools/                      auxiliary scripts
│   ├── regenerate.py           regenerates Campus and Kitchen instances
│   ├── beta_table.py           builds the beta-sweep LaTeX table
│   ├── expand_grid.py          adds hand-crafted Grid instances
│   ├── campus/                 Python 3 port of the upstream Campus generator
│   ├── kitchen/                Python 3 port of the upstream Kitchen generator
│   └── demo/                   scripted live demo
│       ├── demo.sh             the demo script
│       └── setup.sh            downloads demo-magic.sh
├── reproducibility_assignment/ LaTeX report
│   ├── main.tex
│   ├── references.bib
│   └── neurips_2019.sty
└── results files (after a run)
    ├── results.csv             one row per recognition trial at beta = 1.0
    ├── results_b*.csv          per-beta CSVs from the sweep
    ├── summary.csv             aggregated table from analyze.py
    ├── summary_b*.csv          per-beta aggregated tables
    ├── beta_sweep.csv          combined beta sweep
    └── eval.log                live progress log from evaluate.py
```

## Setup

### Requirements

- WSL 2 with Ubuntu 22.04 or 24.04, or any Linux box.
- Python 3.10 or newer.
- Fast Downward, built from source.
- A few apt packages: `cmake g++ make python3 git bzip2 tmux tree`.

### One-time install

Inside WSL:

```bash
sudo apt update
sudo apt install -y cmake g++ make python3 git bzip2 tmux tree

git clone https://github.com/aibasel/downward.git ~/downward
cd ~/downward && ./build.py

echo 'export FAST_DOWNWARD=$HOME/downward/fast-downward.py' >> ~/.bashrc
source ~/.bashrc
```

Quick check:

```bash
$FAST_DOWNWARD --help
```

You should see Fast Downward's usage output. Then a smoke test against a real benchmark:

```bash
cd /mnt/c/path/to/COMS7044A_ReproducibilityAssignment
$FAST_DOWNWARD \
  benchmarks/intrusion-detection/domain.pddl \
  benchmarks/intrusion-detection/p10/planning/problem-p10-hyp_0.pddl \
  --search "astar(lmcut())"
```

You should see translator output, search output, and `Solution found.` at the end.

For result aggregation you also need pandas and tabulate:

```bash
pip3 install pandas tabulate
```

## Running the pipeline

### 1. (Optional) Regenerate Campus and Kitchen instances

The shipped `benchmarks/campus/` and `benchmarks/kitchen/` have about fifty instances each. To regenerate or to get a larger sample:

```bash
python3 tools/regenerate.py campus 10 0.0
python3 tools/regenerate.py kitchen 10
```

The first run produces ten instances per observation ratio, with no random noise on Campus.

### 2. Precompute optimal plans

Four domains do not ship with `.soln` files. They need to be generated before observation sampling can run:

```bash
python3 src/prp/precompute_plans.py
```

The step is idempotent. Re-running skips problems that already have `.soln`. Pass `--force` to overwrite.

### 3. Run the recognition evaluation

```bash
tmux new -s eval
python3 src/prp/evaluate.py --out results.csv --beta 1.0 | tee eval.log
```

This is the long step. About 1885 trials per beta value, roughly two hours on a single CPU. Detach the tmux session with `Ctrl-B` then `D`. Reattach later with `tmux attach -t eval`.

`evaluate.py` is resumable. Interrupt and re-run with the same `--out` and `--beta` and it picks up where it left off.

### 4. Optional beta sweep (extension)

```bash
for beta in 0.1 0.5 1.0 2.0 5.0 10.0; do
  python3 src/prp/evaluate.py --out results_b${beta}.csv --beta $beta
done
```

About 12 to 16 hours total across all six beta values.

### 5. Aggregate the results

```bash
python3 src/prp/analyze.py --in results.csv --out summary.csv
```

Prints four tables (accuracy, spread, Q, posterior mass on the true goal) and writes a long-format `summary.csv`.

For the beta sweep:

```bash
for f in results_b*.csv; do
  beta="${f#results_b}"
  beta="${beta%.csv}"
  python3 src/prp/analyze.py --in "$f" --out "summary_b${beta}.csv" --beta "$beta"
done

python3 -c "
import pandas as pd, glob, re
frames = []
for path in sorted(glob.glob('summary_b*.csv')):
    beta = float(re.search(r'summary_b(.+)\.csv', path).group(1))
    df = pd.read_csv(path); df['beta'] = beta; frames.append(df)
pd.concat(frames, ignore_index=True).to_csv('beta_sweep.csv', index=False)
"
```

See `SUMMARY.md` for a description of every column in the summary CSVs.

## Live demo

A scripted walkthrough of the pipeline on one example from the intrusion-detection domain.

One-time setup downloads the demo-magic helper next to the script:

```bash
sudo apt install -y pv tree
cd tools/demo
./setup.sh
```

`pv` is needed for the simulated typing effect. `tree` is used by the first command in the demo.

Then run:

```bash
cd tools/demo
./demo.sh
```

The script types each command character by character. Press Enter at each pause to advance. About 90 seconds of terminal time across eleven commands.

## Known corrections to upstream benchmarks

Two of the upstream PDDL files have syntax errors that Fast Downward rejects. Both are checked into our `benchmarks/` directory with the fix applied. Both are purely syntactical changes that do not alter the semantics of the domain.

- `benchmarks/block-words/domain.pddl` had `(holding ?x -block)` with no space between `-` and `block`. Fixed to `(holding ?x - block)`.
- `benchmarks/kitchen/domain.pddl` listed `cup`, `sugar`, and `bread` twice in the `:constants` block and listed `toaster` as both an `object` and a `useable`. We removed the duplicates and kept `toaster` as a `useable` only.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `precompute_plans.py` prints `! no plan` for everything | `FAST_DOWNWARD` is unset, or path handling is broken. Run FD manually on one problem to see the real error. |
| `bzip2: not found` while running `regenerate.py` | `sudo apt install bzip2`. |
| `tarfile.ReadError: not a bzip2 file` | A previous failed run left zero-byte tarballs. `rm tools/{campus,kitchen}/*.tar.bz2` and re-run. |
| `evaluate.py` finishes in seconds and writes no rows | `.soln` files are missing. Run `precompute_plans.py` first. |
| FD build fails with `concept does not name a type` | g++ is older than 11. `sudo apt install g++-11; export CXX=g++-11; rm -rf builds; ./build.py`. |
| `demo.sh` errors with `pv: not found` | `sudo apt install pv`. |
| `tree: command not found` | `sudo apt install tree`. |
