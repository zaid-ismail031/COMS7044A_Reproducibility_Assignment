#!/usr/bin/env bash
#
# One-time setup. Downloads demo-magic.sh next to this script.
#
# Usage:
#   cd tools/demo
#   ./setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/demo-magic.sh"

if [ -f "$TARGET" ]; then
    echo "demo-magic.sh already present."
    exit 0
fi

curl -fsSL -o "$TARGET" \
    https://raw.githubusercontent.com/paxtonhare/demo-magic/master/demo-magic.sh
chmod +x "$TARGET"

echo "demo-magic.sh installed. Run ./demo.sh next."
