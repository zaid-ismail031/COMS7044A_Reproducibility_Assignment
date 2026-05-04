from __future__ import annotations

import argparse
import re
from pathlib import Path

from planner import plan

DOMAIN_TAGS = {
    "block-words": "BW",
    "logistics": "LOG",
    "grid": "EASY_IPC_GRID",
    "intrusion-detection": "ID",
    "campus": "CAM",
    "kitchen": "KIT",
}


def write_soln(path, actions, cost):
    lines = [
        "; Time 0.0",
        "; ParsingTime 0.0",
        "; NrActions ",
        "; MakeSpan ",
        f"; MetricValue {cost}",
    ]
    for i, (name, args) in enumerate(actions):
        formatted = " ".join([name, *args])
        lines.append(f"{i} : ({formatted}) [1]")
    path.write_text("\n".join(lines) + "\n")


def soln_path_for(planning_dir, problem_pddl, idx, tag):
    return planning_dir / f"OPT_{tag}_{idx}_{problem_pddl.stem}.soln"


def precompute(domain_dir, tag, force):
    domain_path = domain_dir / "domain.pddl"
    if not domain_path.exists():
        print(f"skip {domain_dir.name}: no domain.pddl")
        return 0
    written = 0
    for instance in sorted(p for p in domain_dir.iterdir() if p.is_dir()):
        planning = instance / "planning"
        if not planning.exists():
            continue
        for problem in sorted(planning.glob("problem-*-hyp_*.pddl")):
            match = re.search(r"hyp_(\d+)", problem.stem)
            if not match:
                continue
            idx = int(match.group(1))
            soln = soln_path_for(planning, problem, idx, tag)
            if soln.exists() and not force:
                continue
            actions, cost = plan(domain_path, problem)
            if actions is None:
                print(f"  ! no plan: {problem.relative_to(domain_dir)}")
                continue
            write_soln(soln, actions, cost)
            print(f"  + {soln.name} (cost={cost}, steps={len(actions)})")
            written += 1
    return written


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("domains", nargs="*")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--root", default="benchmarks")
    args = parser.parse_args()

    targets = args.domains or sorted(DOMAIN_TAGS)
    root = Path(args.root)
    total = 0
    for domain in targets:
        if domain not in DOMAIN_TAGS:
            print(f"unknown domain: {domain}")
            continue
        domain_dir = root / domain
        if not domain_dir.exists():
            print(f"skip {domain}: {domain_dir} not found")
            continue
        print(f"=== {domain} ===")
        total += precompute(domain_dir, DOMAIN_TAGS[domain], args.force)
    print(f"wrote {total} new .soln files")


if __name__ == "__main__":
    main()
