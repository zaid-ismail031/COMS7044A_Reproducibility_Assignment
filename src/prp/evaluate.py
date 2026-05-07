from __future__ import annotations

import argparse
import csv
import re
import sys
import tempfile
import time
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
    k = len(problem_paths)
    for j, problem_path in enumerate(problem_paths, start=1):
        sys.stdout.write(f"\r    candidate {j}/{k} (obs={len(observations)})    ")
        sys.stdout.flush()
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
            sys.stdout.write("\r")
            print(f"    ! no plan for {problem_path.name} (compliant={cost_c}, non={cost_n})")
            deltas.append(float("inf"))
        else:
            deltas.append(cost_c - cost_n)
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()
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


def count_pending(root, pct_list, done):
    total = 0
    for domain_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        domain = domain_dir.name
        if not (domain_dir / "domain.pddl").exists():
            continue
        for instance_dir, problems in load_instances(domain_dir):
            instance = instance_dir.name
            for true_idx in range(len(problems)):
                for pct in pct_list:
                    if (domain, instance, pct, true_idx) not in done:
                        total += 1
    return total


def fmt_eta(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def run(root, out_path, beta, pct_list):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(out_path, beta)
    new_file = not out_path.exists()
    handle = out_path.open("a", newline="")
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if new_file:
        writer.writeheader()

    total = count_pending(root, pct_list, done)
    print(f"=== {total} trials pending (beta={beta}) ===")
    started = time.time()
    completed = 0
    correct_count = 0

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
                    completed += 1
                    elapsed = time.time() - started
                    eta = elapsed / completed * (total - completed) if completed else 0
                    accuracy = (correct_count / max(completed - 1, 1)) if completed > 1 else 0
                    print(
                        f"[{completed}/{total} | {fmt_eta(elapsed)} elapsed, ~{fmt_eta(eta)} left | "
                        f"acc={accuracy:.0%}] {domain}/{instance} true={true_idx} pct={pct}",
                        flush=True,
                    )
                    trial_started = time.time()
                    result = trial(
                        domain_text, instance_dir, problems, true_idx, pct
                    )
                    if result is None:
                        print("    skipped (no .soln for true goal)", flush=True)
                        continue
                    deltas, obs_count = result
                    probs = posterior(deltas, beta=beta)
                    predicted, spread = predict(probs)
                    correct = int(predicted == true_idx)
                    correct_count += correct
                    writer.writerow({
                        "domain": domain,
                        "instance": instance,
                        "obs_pct": pct,
                        "true_idx": true_idx,
                        "predicted_idx": predicted,
                        "spread": spread,
                        "correct": correct,
                        "obs_count": obs_count,
                        "deltas": ",".join(str(d) for d in deltas),
                        "posterior": ",".join(f"{p:.4f}" for p in probs),
                        "beta": beta,
                    })
                    handle.flush()
                    print(
                        f"    -> predicted={predicted} {'OK' if correct else 'WRONG'} "
                        f"spread={spread} ({fmt_eta(time.time() - trial_started)})",
                        flush=True,
                    )
    handle.close()
    print(f"=== done. {completed} trials, {correct_count} correct, {fmt_eta(time.time() - started)} total ===")


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
