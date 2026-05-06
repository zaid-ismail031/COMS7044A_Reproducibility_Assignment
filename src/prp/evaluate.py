from __future__ import annotations

import argparse
import csv
import re
import tempfile
from pathlib import Path

from compiler import compile_problem
from planner import plan, sample_observations
from scoring import posterior, predict

FIELDS = [
    "domain", "instance", "obs_pct", "true_idx", "predicted_idx",
    "spread", "correct", "obs_count", "deltas", "posterior", "beta",
]


def load_instances(domain_dir):
    for inst in sorted(p for p in domain_dir.iterdir() if p.is_dir()):
        planning = inst / "planning"
        if not planning.exists():
            continue
        problems = {}
        for problem in planning.glob("problem-*-hyp_*.pddl"):
            match = re.search(r"hyp_(\d+)", problem.stem)
            if match:
                problems[int(match.group(1))] = problem
        if not problems:
            continue
        ordered = [problems[k] for k in sorted(problems)]
        yield inst, ordered


def find_soln(instance_dir, hyp_idx):
    matches = list((instance_dir / "planning").glob(f"OPT_*hyp_{hyp_idx}.soln"))
    return matches[0] if matches else None


def trial(domain_text, instance_dir, problem_paths, true_idx, obs_pct):
    soln = find_soln(instance_dir, true_idx)
    if soln is None:
        return None
    observations = sample_observations(soln, obs_pct)
    deltas = []
    for problem_path in problem_paths:
        problem_text = problem_path.read_text(encoding="utf-8")
        domain_compliant, problem_compliant = compile_problem(
            domain_text, problem_text, observations, non_compliant=False
        )
        domain_non, problem_non = compile_problem(
            domain_text, problem_text, observations, non_compliant=True
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            (tmp_dir / "d_c.pddl").write_text(domain_compliant)
            (tmp_dir / "p_c.pddl").write_text(problem_compliant)
            (tmp_dir / "d_n.pddl").write_text(domain_non)
            (tmp_dir / "p_n.pddl").write_text(problem_non)
            _, cost_c = plan(tmp_dir / "d_c.pddl", tmp_dir / "p_c.pddl")
            _, cost_n = plan(tmp_dir / "d_n.pddl", tmp_dir / "p_n.pddl")
        if cost_c is None or cost_n is None:
            print(f"  ! no plan for {problem_path.name} (compliant={cost_c}, non={cost_n})")
            deltas.append(float("inf"))
        else:
            deltas.append(cost_c - cost_n)
    return deltas, len(observations)


def load_done(csv_path, beta):
    done = set()
    if not csv_path.exists():
        return done
    with csv_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if abs(float(row["beta"]) - beta) > 1e-9:
                continue
            done.add((row["domain"], row["instance"],
                      int(row["obs_pct"]), int(row["true_idx"])))
    return done


def run(root, out_path, beta, pct_list):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(out_path, beta)
    new_file = not out_path.exists()
    handle = out_path.open("a", newline="")
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if new_file:
        writer.writeheader()

    for domain_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        domain = domain_dir.name
        domain_pddl = domain_dir / "domain.pddl"
        if not domain_pddl.exists():
            continue
        domain_text = domain_pddl.read_text(encoding="utf-8")
        for instance_dir, problems in load_instances(domain_dir):
            instance = instance_dir.name
            for true_idx in range(len(problems)):
                for pct in pct_list:
                    key = (domain, instance, pct, true_idx)
                    if key in done:
                        continue
                    print(f"{domain}/{instance} true={true_idx} pct={pct}")
                    result = trial(
                        domain_text, instance_dir, problems, true_idx, pct
                    )
                    if result is None:
                        continue
                    deltas, obs_count = result
                    probs = posterior(deltas, beta=beta)
                    predicted, spread = predict(probs)
                    writer.writerow({
                        "domain": domain,
                        "instance": instance,
                        "obs_pct": pct,
                        "true_idx": true_idx,
                        "predicted_idx": predicted,
                        "spread": spread,
                        "correct": int(predicted == true_idx),
                        "obs_count": obs_count,
                        "deltas": ",".join(str(d) for d in deltas),
                        "posterior": ",".join(f"{p:.4f}" for p in probs),
                        "beta": beta,
                    })
                    handle.flush()
    handle.close()


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", default="benchmarks", type=Path)
    parser.add_argument("--out", default="results.csv", type=Path)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--pct", default="10,30,50,70,100")
    args = parser.parse_args()
    pct_list = tuple(int(x) for x in args.pct.split(","))
    run(args.root, args.out, args.beta, pct_list)


if __name__ == "__main__":
    main()
