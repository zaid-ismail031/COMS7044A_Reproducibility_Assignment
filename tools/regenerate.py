from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent

SPECS = {
    "campus": {"args": ["1", "0.0"]},
    "kitchen": {"args": ["1"]},
}


def expand(domain, source_dir, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(source_dir / "domain.pddl", dest_dir / "domain.pddl")
    count = 0
    for archive in sorted(source_dir.glob("*.tar.bz2")):
        stem = archive.name.replace(".tar.bz2", "")
        match = re.search(r"_(\d+|full)_(\d+)$", stem)
        if not match:
            continue
        ratio, idx = match.groups()
        true_hyp = re.search(r"hyp-(\d+)_", stem).group(1)
        prefix = stem.split("_generic_")[0]
        instance = f"{prefix}_h{true_hyp}_r{ratio}_i{idx}"
        instance_dir = dest_dir / instance
        instance_dir.mkdir(exist_ok=True)
        with tarfile.open(archive, "r:bz2") as tar:
            tar.extractall(instance_dir, filter="data")
        template = (instance_dir / "template.pddl").read_text()
        hyps = [
            line.strip()
            for line in (instance_dir / "hyps.dat").read_text().splitlines()
            if line.strip()
        ]
        planning = instance_dir / "planning"
        planning.mkdir(exist_ok=True)
        for k, goal in enumerate(hyps):
            atoms = " ".join(part.strip() for part in goal.split(","))
            problem = template.replace("<HYPOTHESIS>", atoms)
            problem = problem.replace("<NAME>", f"{instance}_hyp{k}")
            (planning / f"problem-{instance}-hyp_{k}.pddl").write_text(problem)
        count += 1
    for archive in source_dir.glob("*.tar.bz2"):
        archive.unlink()
    return count


def run(domain, extra_args):
    spec = SPECS[domain]
    source_dir = ROOT / domain
    args = extra_args if extra_args else spec["args"]
    subprocess.run(
        [sys.executable, "generator.py", *args],
        cwd=source_dir,
        check=True,
    )
    dest_dir = PROJECT / "benchmarks" / domain
    if dest_dir.exists():
        for child in dest_dir.iterdir():
            if child.is_dir() and child.name != "domain.pddl":
                shutil.rmtree(child)
    n = expand(domain, source_dir, dest_dir)
    print(f"{domain}: {n} instances written to benchmarks/{domain}/")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("domain", choices=sorted(SPECS))
    parser.add_argument("generator_args", nargs="*")
    args = parser.parse_args()
    run(args.domain, args.generator_args)


if __name__ == "__main__":
    main()
