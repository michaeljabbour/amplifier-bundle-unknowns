#!/usr/bin/env bash
# dominant_quadrant.sh -- deterministic triage guard for the unknowns
# lifecycle pipeline (unknowns:pipelines/unknowns-lifecycle.dot).
#
# Reads a .ai/unknowns-map.dot file and counts open nodes per quadrant,
# then prints a single routing token as the LAST line of stdout (attractor's
# `condition="context.tool.last_line=..."` reads exactly that last line).
#
# Usage: dominant_quadrant.sh [path/to/unknowns-map.dot]
#   Default path: .ai/unknowns-map.dot
#
# Output (last line only, one of): uu | uk | ku | clear
#
# Precedence (mirrors unknowns:context/unknowns-matrix.md "Recommending a
# technique"), evaluated in this order -- first match wins:
#   1. Any high-severity open unknown-unknown            -> uu
#   2. uu open count > 0 and >= both uk and ku open count -> uu
#   3. uk open count > 0 and >= ku open count             -> uk
#   4. ku open count > 0                                  -> ku
#   5. otherwise                                          -> clear

set -euo pipefail

MAP_FILE="${1:-.ai/unknowns-map.dot}"

# Missing map -> nothing to triage yet. Don't fail the pipeline; route to
# "clear" so cartography (which creates the map) can run first.
if [ ! -f "$MAP_FILE" ]; then
    echo "clear"
    exit 0
fi

# Line-oriented count (not a real DOT parser): the node schema in
# unknowns-matrix.md keeps quadrant= and status= (and severity=, when
# present) on the same physical label line, which is sufficient here.
#
# Each grep may legitimately match zero lines (a quadrant can be empty).
# Under `set -o pipefail`, grep's own non-zero "no match" exit status would
# otherwise abort the script via `set -e` even though the pipeline's final
# `wc -l` output (0) is exactly the answer we want -- so `|| true` guards
# each assignment without masking real errors (a missing/unreadable file is
# already handled above, before these greps run).
UU_OPEN=$(grep -E "quadrant=uu[^]]*status=open" "$MAP_FILE" 2>/dev/null | wc -l | tr -d ' ') || true
UK_OPEN=$(grep -E "quadrant=uk[^]]*status=open" "$MAP_FILE" 2>/dev/null | wc -l | tr -d ' ') || true
KU_OPEN=$(grep -E "quadrant=ku[^]]*status=open" "$MAP_FILE" 2>/dev/null | wc -l | tr -d ' ') || true
UU_HIGH=$(grep -E "quadrant=uu[^]]*status=open[^]]*severity=high" "$MAP_FILE" 2>/dev/null | wc -l | tr -d ' ') || true

# Precedence, first match wins:
if [ "$UU_HIGH" -gt 0 ]; then
    echo "uu"
elif [ "$UU_OPEN" -gt 0 ] && [ "$UU_OPEN" -ge "$UK_OPEN" ] && [ "$UU_OPEN" -ge "$KU_OPEN" ]; then
    echo "uu"
elif [ "$UK_OPEN" -gt 0 ] && [ "$UK_OPEN" -ge "$KU_OPEN" ]; then
    echo "uk"
elif [ "$KU_OPEN" -gt 0 ]; then
    echo "ku"
else
    echo "clear"
fi
