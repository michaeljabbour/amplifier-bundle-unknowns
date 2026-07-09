"""Tests for the pretty presentation renderer (render_pretty_dot / render_png).

Design decision under test: DATA vs PRESENTATION is a hard split. The
canonical map file (parsed by map_ops.parse_map / mirrored by
scripts/dominant_quadrant.sh) must NEVER be touched by rendering -- these
functions only read it and produce a separate, presentation-only DOT string.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from unknowns_map import map_ops, render_pretty_dot, render_png


def _mark_accepted_risk(map_path: Path, node_id: str) -> None:
    """Hand-edit a node's line to add the accepted_risk marker -- add_unknown
    has no first-class parameter for it (only status/severity), matching how
    a maintainer would hand-annotate a knowingly-accepted risk in the DOT."""
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
    else:
        raise AssertionError(f"node {node_id} not found in {map_path}")
    map_path.write_text("\n".join(lines) + "\n")


def _add_real_edge(map_path: Path, src: str, dst: str, label: str) -> None:
    """Append a hand-added dependency/reclassification edge before the
    closing brace -- exactly how an agent would record one manually."""
    lines = map_path.read_text().splitlines()
    insert_at = len(lines) - 1  # last line is the closing '}'
    lines.insert(
        insert_at,
        f'  {src} -> {dst} [label="{label}", style=dashed, color="#A63A1C", '
        f'fontcolor="#A63A1C", constraint=false]',
    )
    map_path.write_text("\n".join(lines) + "\n")


@pytest.fixture
def rich_map(tmp_path: Path) -> Path:
    m = tmp_path / ".ai" / "unknowns-map.dot"
    map_ops.seed_map(m, task="render the pretty map")
    map_ops.prune_placeholders(m)
    map_ops.add_unknown(m, "kk", "user wants a genuinely readable map", status="given")
    map_ops.add_unknown(
        m, "ku", "which layout engine communicates hierarchy best?", severity="high"
    )
    map_ops.add_unknown(m, "ku", "what palette should mark severity?", severity="med")
    crit_id = map_ops.add_unknown(
        m,
        "uu",
        "the default render was unreadable for the maintainer himself",
        severity="critical",
    )
    map_ops.add_unknown(
        m, "uu", "no visual convention existed for an accepted risk", severity="high"
    )
    map_ops.add_unknown(m, "uk", "a layout that reads calm and walkable, not busy")
    risk_id = map_ops.add_unknown(
        m,
        "ku",
        "accepted the false-kill risk knowingly",
        status="resolved",
        severity="high",
    )
    _mark_accepted_risk(m, risk_id)
    _add_real_edge(m, risk_id, crit_id, "named before the risk\\nwas accepted")
    return m


# ---------------------------------------------------------------------------
# Plain language, no jargon
# ---------------------------------------------------------------------------


def test_pretty_dot_has_plain_language_clusters_and_legend(rich_map: Path):
    dot = render_pretty_dot(rich_map)
    assert "WHAT WE KNOW FOR SURE" in dot
    assert "QUESTIONS WE'RE WORKING ON" in dot
    assert "THINGS YOU'D RECOGNIZE ON SIGHT" in dot
    assert "BLINDSPOTS WE FOUND" in dot
    assert "HOW TO READ THIS" in dot


def test_pretty_dot_has_no_jargon_in_output(rich_map: Path):
    dot = render_pretty_dot(rich_map)
    lowered = dot.lower()
    assert "known unknown" not in lowered
    assert "unknown known" not in lowered
    assert "quadrant=" not in dot
    assert "status=open" not in dot and "status=resolved" not in dot


# ---------------------------------------------------------------------------
# Canonical file is never mutated
# ---------------------------------------------------------------------------


def test_pretty_dot_does_not_mutate_canonical_file(rich_map: Path):
    before = rich_map.read_bytes()
    render_pretty_dot(rich_map)
    assert rich_map.read_bytes() == before


@pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz `dot` not installed")
def test_render_png_does_not_mutate_canonical_file(rich_map: Path, tmp_path: Path):
    before = rich_map.read_bytes()
    out = render_png(rich_map, tmp_path / "out.png")
    assert rich_map.read_bytes() == before
    assert out.exists() and out.stat().st_size > 0


# ---------------------------------------------------------------------------
# Label wrapping
# ---------------------------------------------------------------------------


_NODE_LABEL_RE = re.compile(r'^\s+\w+\s*\[label="([^"]*)"', re.MULTILINE)


def test_pretty_dot_wraps_labels(rich_map: Path):
    """Node (and legend) labels wrap at ~38 chars, max 4 lines. This
    deliberately excludes the graph-level title label, which is a two-line
    header with its own format, not a wrapped node description."""
    dot = render_pretty_dot(rich_map)
    labels = _NODE_LABEL_RE.findall(dot)
    assert labels, "expected at least one node/legend label"
    for raw_label in labels:
        parts = raw_label.split("\\n")
        for part in parts:
            assert len(part) <= 42, f"line too long: {part!r}"
        assert len(parts) <= 4


# ---------------------------------------------------------------------------
# Severity color ramp + accepted-risk convention
# ---------------------------------------------------------------------------


def test_pretty_dot_colors_severity_ramp(rich_map: Path):
    dot = render_pretty_dot(rich_map)
    assert "#EC9A79" in dot and "#A63A1C" in dot  # critical fill + border
    assert "#F5DDA6" in dot and "#A87A1F" in dot  # high fill + border
    assert "#DCE9DA" in dot and "#6B8E63" in dot  # settled fill + border


def test_pretty_dot_marks_accepted_risk(rich_map: Path):
    dot = render_pretty_dot(rich_map)
    # settled fill (green) with the orange accepted-risk border, distinct
    # from the plain settled border color.
    assert "#B5552D" in dot
    assert 'fillcolor="#DCE9DA", color="#B5552D"' in dot


# ---------------------------------------------------------------------------
# Real edges carried over, spine/legend plumbing skipped
# ---------------------------------------------------------------------------


def test_pretty_dot_carries_real_edges(rich_map: Path):
    dot = render_pretty_dot(rich_map)
    assert "constraint=false" in dot
    assert "carried-over edges from the canonical map" in dot


def test_pretty_dot_is_parseable_graphviz(rich_map: Path):
    dot = render_pretty_dot(rich_map)
    assert dot.strip().startswith("digraph UnknownsMapPretty {")
    assert dot.strip().endswith("}")
    assert dot.count("{") == dot.count("}")


# ---------------------------------------------------------------------------
# Canonical parser/triage contract untouched by any of the above
# ---------------------------------------------------------------------------


def test_canonical_parser_and_triage_survive_pretty_rendering(rich_map: Path):
    before_nodes = map_ops.parse_map(rich_map)
    before_token = map_ops.dominant_quadrant(rich_map)
    render_pretty_dot(rich_map)
    after_nodes = map_ops.parse_map(rich_map)
    after_token = map_ops.dominant_quadrant(rich_map)
    assert before_nodes == after_nodes
    assert before_token == after_token
