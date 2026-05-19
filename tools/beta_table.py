from __future__ import annotations

import glob
import re

import pandas as pd

BETAS = []
frames = []
for path in sorted(glob.glob("summary_b*.csv")):
    match = re.search(r"summary_b(.+)\.csv", path)
    if not match:
        continue
    beta = float(match.group(1))
    BETAS.append(beta)
    df = pd.read_csv(path)
    df["beta"] = beta
    frames.append(df)
BETAS = sorted(set(BETAS))

if not frames:
    raise SystemExit("no summary_b*.csv files found")

combined = pd.concat(frames, ignore_index=True)

# pivot: rows are (domain, obs_pct), columns are beta, values are p_true
pivot = combined.pivot_table(
    index=["domain", "obs_pct"], columns="beta", values="p_true"
).round(3)
pivot = pivot[BETAS]

domain_order = ["block-words", "campus", "grid", "intrusion-detection", "kitchen", "logistics"]
pivot = pivot.reindex(domain_order, level="domain")

print("=== plain table ===")
print(pivot.to_string())
print()

print("=== LaTeX (paste into Results section) ===")
print(r"\begin{table}[h]")
print(r"\centering")
print(r"\caption{Posterior probability mass on the true goal, $P(G^* \mid O)$, as a function of"
      r" $\beta$. Computed by averaging the posterior probability assigned to the true goal"
      r" across all trials in each (domain, observation \%) cell. $\beta$ affects this metric"
      r" even though $Q$ and $|G^*|$ are $\beta$-invariant for integer-cost domains.}")
print(r"\label{tab:beta-ptrue}")
print(r"\small")
beta_cols = " & ".join(f"$\\beta{{=}}{b}$" for b in BETAS)
print(r"\begin{tabular}{ll" + "r" * len(BETAS) + r"}")
print(r"\toprule")
print(rf"Domain & Obs \% & {beta_cols} \\")
print(r"\midrule")
last_domain = None
for (domain, obs_pct), row in pivot.iterrows():
    domain_cell = domain if domain != last_domain else ""
    values = " & ".join(f"{row[b]:.2f}" if pd.notna(row[b]) else "--" for b in BETAS)
    if last_domain is not None and domain != last_domain:
        print(r"\midrule")
    print(rf"{domain_cell} & {obs_pct} & {values} \\")
    last_domain = domain
print(r"\bottomrule")
print(r"\end{tabular}")
print(r"\end{table}")
