# Summary CSVs

Aggregated recognition results, produced by `src/prp/analyze.py`. Each row is one cell of the paper's headline tables — a single (domain, observation %) combination, averaged over many recognition trials.

```bash
python3 src/prp/analyze.py --out summary.csv                # default: uses results.csv at β = whatever is in there
python3 src/prp/analyze.py --in results_b2.0.csv --out summary_b2.0.csv --beta 2.0
```

## Files in this repo

| File | Source data | Notes |
|---|---|---|
| `summary.csv` | `results.csv` | Main run, β = 1.0. The headline numbers. |
| `summary_b0.1.csv` | `results_b0.1.csv` | β-sensitivity sweep point. |
| `summary_b0.5.csv` | `results_b0.5.csv` | β-sensitivity sweep point. |
| `summary_b1.0.csv` | `results_b1.0.csv` | Same trials as `summary.csv`; kept for the sweep ensemble. |
| `summary_b2.0.csv` | `results_b2.0.csv` | β-sensitivity sweep point. |
| `summary_b5.0.csv` | `results_b5.0.csv` | β-sensitivity sweep point. |
| `summary_b10.0.csv` | `results_b10.0.csv` | β-sensitivity sweep point. |
| `beta_sweep.csv` | concatenation of all `summary_b*.csv` files | Long-format, has a `beta` column. Use this for plotting and the report's Figure on β sensitivity. |

## Columns (each `summary*.csv`)

| Column | Type | Description |
|---|---|---|
| `domain` | string | Planning domain (block-words, campus, grid, intrusion-detection, kitchen, logistics). |
| `obs_pct` | int | Observation percentage — the recogniser saw the first `obs_pct%` of the agent's optimal plan. |
| `n` | int | Number of recognition trials averaged in this cell. |
| `accuracy` | float ∈ [0, 1] | Fraction of trials where the true goal was in the recogniser's top-ranked set. |
| `spread` | float ≥ 1 | Mean size of the top-ranked set. 1.0 = always a single, unambiguous winner. |
| `q` | float ∈ [0, 1] | Paper's headline metric: `q = accuracy / spread`. Combines correctness with decisiveness. |
| `beta` | float | (Only in `beta_sweep.csv`.) The β value used for that row's posterior calculation. |

## How to read each value

### `accuracy`

Pure correctness — did the true goal end up among the top-probability candidates? Ignores how many candidates tied. A recogniser that always returns "every goal is equally likely" trivially scores `accuracy = 1.0` but is useless in practice. Read it together with `spread`.

### `spread`

How decisive the recogniser was, averaged across trials. Range `[1, K]` where K is the number of candidate goals for that instance.

- `1.0` — every trial picked a single goal as the unambiguous winner.
- `2.0` — on average, the recogniser couldn't decide between two equally likely goals.
- Large values — the posterior is essentially flat; recogniser has little information.

Should fall as `obs_pct` rises (more evidence → narrower posterior).

### `q`

The paper's primary score. Penalises tied predictions so a recogniser can't game accuracy by being indecisive.

- `q = 1.0` — perfect: always right, always with one clear winner.
- `q = 0.5` — could be "always right but tied 2-ways", or "right half the time with single winners". Either way, the answer is only half as useful as a perfect recogniser's.
- `q < 0.1` — recogniser is essentially noise.

Should rise as `obs_pct` rises. The paper claims `q ≥ 0.8` is achievable by 70% observation across all six domains.

### `beta`

The temperature parameter in the Boltzmann likelihood:

```
P(O | G) ∝ exp(-β · Δ(G, O))
```

- Small β (0.1) → likelihood is nearly flat; posterior dominated by the prior. Spread stays high.
- Large β (10) → likelihood is sharp; even small Δ produces a confident winner. Spread drops.

The paper does not specify what β was used. `summary.csv` uses β = 1.0 as a default. The `summary_b*.csv` family lets you study sensitivity.

## Typical patterns

A well-behaved cell sequence (intrusion-detection at β = 1.0):

```
intrusion-detection,10,30,0.2667,4.0667,0.0917
intrusion-detection,30,30,0.7000,1.8333,0.5972
intrusion-detection,50,30,0.8333,1.2667,0.7806
intrusion-detection,70,30,1.0000,1.0000,1.0000
intrusion-detection,100,30,1.0000,1.0000,1.0000
```

Accuracy climbs, spread shrinks, Q rises to 1.0 — the curve the paper predicts.

## Long-format vs wide-format

`summary*.csv` files are **long-format** (one row per cell), which is what plotting and stats libraries want. For a wide pivot table suitable for a report:

```python
import pandas as pd
df = pd.read_csv("summary.csv")
df.pivot(index="domain", columns="obs_pct", values="q")
```

## Building `beta_sweep.csv`

Once you have multiple `summary_b*.csv` files, concatenate them with the β value tagged as a column:

```python
import pandas as pd
frames = []
for beta in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
    df = pd.read_csv(f"summary_b{beta}.csv")
    df["beta"] = beta
    frames.append(df)
pd.concat(frames, ignore_index=True).to_csv("beta_sweep.csv", index=False)
```

That single CSV is the input to your β-sensitivity figure in the report.

## Plotting the β sweep

```python
import pandas as pd, seaborn as sns, matplotlib.pyplot as plt
df = pd.read_csv("beta_sweep.csv")
g = sns.relplot(
    data=df, x="beta", y="q", col="domain", col_wrap=3,
    hue="obs_pct", kind="line", marker="o", height=3,
)
g.set(xscale="log")
plt.savefig("report/figures/beta_sweep.png", dpi=150, bbox_inches="tight")
```

Six panels (one per domain), each showing Q vs β with one line per obs_pct. Cells whose lines are flat are β-insensitive (the method's answer doesn't depend on the assumption). Cells whose lines slope steeply are β-sensitive — likely candidates for the discussion of the paper's underspecification.
