#!/usr/bin/env python3
"""Regenerate docs/images/map-example.png from a small, illustrative sample map.

Usage:
    python scripts/make_example_map.py [--out docs/images/map-example.png]

Builds a small map spanning all four quadrants -- including one CRITICAL
unknown-unknown, one knowingly accepted risk, and one real dependency edge --
then renders it through render_png. render_png ALWAYS goes through
render_pretty_dot: this script never touches `dot -Tpng` on the raw
canonical DOT, so the example image is exactly what every real user of this
bundle gets, not a hand-tuned one-off.

Reproducible: delete the output PNG and re-run any time the render logic
changes (see AGENTS.md's DATA vs PRESENTATION pitfall).
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from unknowns_map import map_ops  # noqa: E402


def _mark_accepted_risk(map_path: Path, node_id: str) -> None:
    """Hand-annotate a resolved node as a knowingly accepted risk -- there is
    no add_unknown parameter for this; it's a manual maintainer annotation,
    same as the accepted_risk convention documented in the unknowns matrix."""
    lines = map_path.read_text().splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"\s*{re.escape(node_id)}\s*\[", line):
            lines[i] = re.sub(
                r"(quadrant=\w+, status=\w+(?:, severity=\w+)?)\]",
                r"\1, accepted_risk=true]",
                line,
                count=1,
            )
            break
    map_path.write_text("\n".join(lines) + "\n")


def build_sample_map(map_path: Path) -> tuple[str, str]:
    """Seed and populate a small sample map. Returns (critical_id, risk_id)."""
    map_ops.seed_map(
        map_path, task="ship a beautifully designed unknowns map", force=True
    )
    map_ops.prune_placeholders(map_path)

    map_ops.add_unknown(
        map_path,
        "kk",
        "the map must be readable by a non-technical exec",
        status="given",
    )
    map_ops.add_unknown(
        map_path,
        "ku",
        "which layout keeps a portrait grid readable at any size?",
        severity="high",
    )
    map_ops.add_unknown(
        map_path,
        "ku",
        "what palette reads as severity, not decoration?",
        severity="med",
    )
    map_ops.add_unknown(map_path, "uk", "a briefing that makes someone act, not admire")
    crit_id = map_ops.add_unknown(
        map_path,
        "uu",
        "the old render had no visual hierarchy at all",
        severity="critical",
    )
    risk_id = map_ops.add_unknown(
        map_path,
        "ku",
        "kept the machine DOT format unchanged to protect the parser contract",
        status="resolved",
        severity="high",
    )
    _mark_accepted_risk(map_path, risk_id)

    # One real, carried-over edge: the format-stability decision was made
    # *because of* the critical blindspot -- a genuine dependency, not
    # spine/legend plumbing.
    lines = map_path.read_text().splitlines()
    lines.insert(
        len(lines) - 1,
        f'  {crit_id} -> {risk_id} [label="drove the decision to\\n'
        'keep the format frozen", style=dashed, color="#A63A1C", '
        'fontcolor="#A63A1C", constraint=false]',
    )
    map_path.write_text("\n".join(lines) + "\n")
    return crit_id, risk_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(_REPO_ROOT / "docs" / "images" / "map-example.png"),
        help="output PNG path (default: docs/images/map-example.png)",
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        sample_map = Path(tmp) / "unknowns-map.dot"
        build_sample_map(sample_map)
        out_path = map_ops.render_png(sample_map, Path(args.out))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
