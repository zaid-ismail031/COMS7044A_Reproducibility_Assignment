from __future__ import annotations

import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

FD_BIN = os.environ.get("FAST_DOWNWARD", "fast-downward.py")
DEFAULT_SEARCH = "astar(lmcut())"


def plan(domain_path, problem_path, search=DEFAULT_SEARCH, timeout=300):
    with tempfile.TemporaryDirectory() as workdir:
        result = subprocess.run(
            [FD_BIN, str(domain_path), str(problem_path), "--search", search],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        plan_file = Path(workdir) / "sas_plan"
        if result.returncode != 0 or not plan_file.exists():
            return None, None
        return parse_sas_plan(plan_file.read_text())


def parse_sas_plan(text):
    actions = []
    cost = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(";"):
            match = re.match(r";\s*cost\s*=\s*(\d+)", line)
            if match:
                cost = int(match.group(1))
            continue
        match = re.match(r"\(([^)]+)\)", line)
        if match:
            tokens = match.group(1).split()
            actions.append((tokens[0], tokens[1:]))
    return actions, cost


def parse_soln(path):
    text = Path(path).read_text()
    actions = []
    cost = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(";"):
            match = re.search(r"MetricValue\s+(\d+)", line)
            if match:
                cost = int(match.group(1))
            continue
        match = re.search(r":\s*\(([^)]+)\)", line)
        if match:
            tokens = match.group(1).split()
            if tokens:
                actions.append((tokens[0], tokens[1:]))
    return actions, cost


def sample_observations(soln_path, pct):
    actions, _ = parse_soln(soln_path)
    if pct >= 100:
        return actions
    count = max(1, math.ceil((pct / 100) * len(actions)))
    return actions[:count]


def goal_for_soln(soln_path):
    soln_path = Path(soln_path)
    match = re.search(r"hyp_(\d+)", soln_path.stem)
    if not match:
        raise ValueError(f"can't find hyp index in {soln_path.name}")
    index = int(match.group(1))
    instance_dir = soln_path.parent.parent
    hyps_file = instance_dir / "hyps.dat"
    lines = [l.strip() for l in hyps_file.read_text().splitlines() if l.strip()]
    if index >= len(lines):
        raise ValueError(f"hyp {index} not in {hyps_file} ({len(lines)} lines)")
    atoms = [part.strip() for part in lines[index].split(",") if part.strip()]
    return index, atoms
