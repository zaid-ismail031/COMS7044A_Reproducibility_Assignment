# summary.csv

Aggregated recognition results, produced by:

```bash
python3 src/prp/analyze.py --out summary.csv
```

Each row is one cell of the paper's headline tables — a single (domain, observation %) combination, averaged over many recognition trials.

## Columns

| Column | Type | Description |
|---|---|---|
| `domain` | string | Planning domain name (one of: block-words, campus, grid, intrusion-detection, kitchen, logistics). |
| `obs_pct` | int | Observation percentage. The recogniser was shown the first `obs_pct%` of the agent's optimal plan. |
| `n` | int | Number of recognition trials averaged. One trial per (instance, true goal, obs_pct) combination. |
| `accuracy` | float ∈ [0, 1] | Fraction of trials where the true goal was in the recogniser's top-ranked set. |
| `spread` | float ≥ 1 | Mean size of the top-ranked set. 1.0 = always unambiguous winner. Larger = more ties. |
| `q` | float ∈ [0, 1] | Paper's headline metric. `q = accuracy / spread`. Combines correctness with decisiveness. |

## How to read each value

### `accuracy`

Pure correctness — did the true goal end up among the top-probability candidates? Ignores how many tied for the top. So a recogniser that always returns "every goal is equally likely" scores `accuracy = 1.0` but is useless.

### `spread`

How decisive the recogniser was, averaged across trials. Range `[1, K]` where K is the number of candidate goals for that instance.

- `1.0` — every trial picked a single goal as the unambiguous winner.
- `2.0` — on average, the recogniser couldn't decide between two equally likely goals.
- Large values — the posterior is essentially flat; recogniser has little information.

Should decrease as `obs_pct` rises (more evidence → narrower posterior).

### `q`

The paper's primary score. Penalises tied predictions so a recogniser can't game accuracy by being indecisive.

- `q = 1.0` — perfect: always right, always with one clear winner.
- `q = 0.5` — could be "always right but tied 2-ways", or "right half the time with single winners". Either way, the answer is only half as useful as a perfect recogniser's.
- `q < 0.1` — recogniser is essentially noise.

Should rise as `obs_pct` rises. The paper claims `q ≥ 0.8` is achievable across all six domains by 70% observation.

## Typical patterns

Reading a well-behaved domain like `intrusion-detection`:

```
intrusion-detection,10,30,0.2667,4.0667,0.0917
intrusion-detection,30,30,0.7000,1.8333,0.5972
intrusion-detection,50,30,0.8333,1.2667,0.7806
intrusion-detection,70,30,1.0000,1.0000,1.0000
intrusion-detection,100,30,1.0000,1.0000,1.0000
```

Accuracy climbs, spread shrinks, Q rises to 1.0 — exactly the curve the paper predicts.

## Long-format vs wide-format

`summary.csv` is long-format (one row per cell). For wide-format pivot tables suitable for a report:

```python
import pandas as pd
df = pd.read_csv("summary.csv")
df.pivot(index="domain", columns="obs_pct", values="q")
```

## Comparing across β values

For the group-of-3 β-sensitivity extension, run the evaluation with multiple β values, save each summary to its own file, then concatenate:

```bash
for beta in 0.1 0.5 1.0 2.0 5.0; do
  python3 src/prp/evaluate.py --out results_b${beta}.csv --beta $beta
  python3 src/prp/analyze.py --in results_b${beta}.csv --out summary_b${beta}.csv
done
```

```python
import pandas as pd
frames = []
for beta in [0.1, 0.5, 1.0, 2.0, 5.0]:
    frame = pd.read_csv(f"summary_b{beta}.csv")
    frame["beta"] = beta
    frames.append(frame)
combined = pd.concat(frames, ignore_index=True)
```

Then plot Q against β per (domain, obs_pct) to see the β-sensitivity surface.
