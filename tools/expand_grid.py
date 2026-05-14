from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "grid"

# (instance_name, base_instance, candidate_goal_nodes)
NEW_INSTANCES = [
    ("p03", "p01", ["node_A", "node_E"]),
    ("p04", "p01", ["node_B", "node_D", "node_E"]),
    ("p05", "p01", ["node_F", "node_G", "node_E"]),
    ("p06", "p02", ["node_A", "node_F", "node_E"]),
    ("p07", "p02", ["node_C", "node_G"]),
    ("p08", "p02", ["node_D", "node_H", "node_J"]),
]


def make_instance(name, base, goal_nodes):
    base_dir = ROOT / base
    new_dir = ROOT / name
    if new_dir.exists():
        shutil.rmtree(new_dir)
    new_dir.mkdir()

    template = (base_dir / "planning" / "template.pddl").read_text() \
        if (base_dir / "planning" / "template.pddl").exists() else None
    base_problem = next((base_dir / "planning").glob(f"problem-{base}-hyp_0.pddl")).read_text()

    (new_dir / "hyps.dat").write_text(
        "\n".join(f"(at-robot {n})" for n in goal_nodes) + "\n"
    )

    planning = new_dir / "planning"
    planning.mkdir()
    if template:
        (planning / "template.pddl").write_text(template)

    for k, node in enumerate(goal_nodes):
        problem = re.sub(
            r"\(:goal\s*\(and\s*\(at-robot [^\)]+\)\s*\)\s*\)",
            f"(:goal (and (at-robot {node})))",
            base_problem,
            count=1,
        )
        problem = re.sub(r"\(problem strips-grid-\d+\)", f"(problem strips-grid-{name})", problem)
        (planning / f"problem-{name}-hyp_{k}.pddl").write_text(problem)

    print(f"created {name}: {len(goal_nodes)} candidates ({base} grid)")


def main():
    for name, base, goals in NEW_INSTANCES:
        base_dir = ROOT / base
        if not base_dir.exists():
            print(f"skip {name}: base {base} not found")
            continue
        make_instance(name, base, goals)


if __name__ == "__main__":
    main()
