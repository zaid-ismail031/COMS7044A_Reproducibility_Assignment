from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def summarise(df, value, fmt="{:.2f}"):
    pivot = df.pivot_table(
        index="domain",
        columns="obs_pct",
        values=value,
        aggfunc="mean",
    )
    pivot = pivot.map(lambda x: fmt.format(x) if pd.notna(x) else "-")
    return pivot


def counts(df):
    return df.pivot_table(
        index="domain", columns="obs_pct", values="correct", aggfunc="count"
    ).fillna(0).astype(int)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--in", dest="in_path", default="results.csv", type=Path)
    parser.add_argument("--out", default=None, type=Path)
    parser.add_argument("--beta", type=float, default=None)
    args = parser.parse_args()

    df = pd.read_csv(args.in_path)
    if args.beta is not None:
        df = df[df.beta == args.beta]

    df["q"] = df["correct"] / df["spread"]

    accuracy = summarise(df, "correct", "{:.2%}")
    spread = summarise(df, "spread", "{:.2f}")
    q = summarise(df, "q", "{:.2f}")
    n = counts(df)

    print("=== Accuracy (recognizer's top set contains the true goal) ===")
    print(accuracy.to_string())
    print()
    print("=== Spread |G*| (size of the top set) ===")
    print(spread.to_string())
    print()
    print("=== Q = correct / spread (paper's headline metric) ===")
    print(q.to_string())
    print()
    print("=== Trial counts ===")
    print(n.to_string())

    if args.out:
        with args.out.open("w") as handle:
            handle.write("# Recognition results\n\n")
            handle.write("## Accuracy\n\n")
            handle.write(accuracy.to_markdown())
            handle.write("\n\n## Spread |G*|\n\n")
            handle.write(spread.to_markdown())
            handle.write("\n\n## Q\n\n")
            handle.write(q.to_markdown())
            handle.write("\n\n## Trial counts\n\n")
            handle.write(n.to_markdown())
            handle.write("\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
