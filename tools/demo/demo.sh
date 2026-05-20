#!/usr/bin/env bash
#
# Live demo script for the recognition pipeline.
#
# Usage:
#   cd tools/demo
#   ./setup.sh        # one-time, downloads demo-magic.sh
#   ./demo.sh         # run during screen recording
#
# Press Enter between commands to advance.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ ! -f "$SCRIPT_DIR/demo-magic.sh" ]; then
    echo "demo-magic.sh not found. Run ./setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
. "$SCRIPT_DIR/demo-magic.sh" -n

cd "$PROJECT_ROOT"

# Clean prompt for the camera.
DEMO_PROMPT="\[\033[01;32m\]$\[\033[00m\] "

DOMAIN="benchmarks/intrusion-detection/domain.pddl"
PROBLEM="benchmarks/intrusion-detection/p10/planning/problem-p10-hyp_0.pddl"
SOLN="benchmarks/intrusion-detection/p10/planning/OPT_ID_0_problem-p10-hyp_0.soln"
HYPS="benchmarks/intrusion-detection/p10/hyps.dat"
COMPILED_DIR="benchmarks/intrusion-detection"

clear

# 1. Project layout.
pe "find src tools benchmarks -maxdepth 2 -not -path '*/__pycache__*' -not -name '*.pyc' | sort"

# 2. A benchmark instance.
pe "ls $(dirname $PROBLEM)/ | head -8"

# 3. The candidate goal set for this instance.
pe "cat $HYPS"

# 4. The PDDL problem file.
pe "head -25 $PROBLEM"

# 5. The optimal plan that the agent followed, source of observations.
pe "head -10 $SOLN"

# 6. Run the compiler with two observed actions.
pe "python3 src/prp/compiler.py $DOMAIN $PROBLEM '[[\"recon\",[\"taurus\"]],[\"recon\",[\"libra\"]]]' --tag demo"

# 7. Show what the compiler added (obs fluents, modified goal).
pe "grep -E 'obs_|:goal' $COMPILED_DIR/problem_demo_compliant.pddl | head -5"

pe "grep -E 'obs_|:goal' $COMPILED_DIR/problem_demo_non_compliant.pddl | head -5"

# 8. Solve the compliant compilation with Fast Downward.
pe "\$FAST_DOWNWARD $COMPILED_DIR/domain_demo_compliant.pddl $COMPILED_DIR/problem_demo_compliant.pddl --search 'astar(lmcut())' 2>&1 | grep -E 'Plan (length|cost):|Solution found'"

# 9. Solve the non-compliant compilation.
pe "\$FAST_DOWNWARD $COMPILED_DIR/domain_demo_non_compliant.pddl $COMPILED_DIR/problem_demo_non_compliant.pddl --search 'astar(lmcut())' 2>&1 | grep -E 'Plan (length|cost):|Solution found'"

# 10. Aggregate results across all six domains.
pe "python3 src/prp/analyze.py --in results.csv | head -40"

# Off-camera cleanup.
rm -f "$COMPILED_DIR"/domain_demo_*.pddl
rm -f "$COMPILED_DIR"/problem_demo_*.pddl
rm -f sas_plan

echo
echo "Demo complete."
