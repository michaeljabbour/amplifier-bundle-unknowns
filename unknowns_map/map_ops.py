"""Deterministic operations on .ai/unknowns-map.dot.

This module is the SINGLE Python home for the map's deterministic logic:
parsing, quadrant counts, triage precedence, seeding, node add/reclassify,
and the plain-language terminal briefing render (per
unknowns:context/ascii-render-spec.md).

The zero-dependency shell mirror ``scripts/dominant_quadrant.sh`` implements
the SAME triage precedence for environments without this package installed
(the pipeline's parallelogram guard shells it). ``tests/test_triage_contract.py``
asserts the two never drift.

Quadrant codes (see unknowns:context/unknowns-matrix.md):
    kk = known knowns      ku = known unknowns
    uk = unknown knowns    uu = unknown unknowns
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ._assets import map_template

DEFAULT_MAP = Path(".ai/unknowns-map.dot")

QUADRANTS = ("kk", "ku", "uk", "uu")
QUADRANT_TITLES = {
    "kk": "KNOWN KNOWNS",
    "ku": "KNOWN UNKNOWNS",
    "uk": "UNKNOWN KNOWNS",
    "uu": "UNKNOWN UNKNOWNS",
}

_SEVERITY_ORDER = {"high": 0, "med": 1, "low": 2, None: 3}
_DOT_KEYWORDS = {"graph", "node", "edge", "subgraph", "digraph"}

_LABEL_RE = re.compile(r'label="([^"]*)"')
_NODE_ID_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*\[")


@dataclass
class Unknown:
    """One node parsed from the map."""

    node_id: str
    desc: str
    quadrant: str | None
    status: str | None
    severity: str | None
    line_no: int  # 0-based index into the file's lines


def _parse_label_attrs(label: str) -> tuple[str, str | None, str | None, str | None]:
    desc = label.split("\\n")[0].strip()
    q = re.search(r"quadrant=(\w+)", label)
    s = re.search(r"status=(\w+)", label)
    sev = re.search(r"severity=(\w+)", label)
    return (
        desc,
        q.group(1) if q else None,
        s.group(1) if s else None,
        sev.group(1) if sev else None,
    )


def parse_map(map_path: Path | str = DEFAULT_MAP) -> list[Unknown]:
    """Parse map nodes line-oriented (matches the shell mirror's assumptions:
    quadrant=/status=/severity= live on the same physical label line)."""
    path = Path(map_path)
    if not path.exists():
        return []
    nodes: list[Unknown] = []
    for i, line in enumerate(path.read_text().splitlines()):
        if "->" in line:
            continue  # edge line
        m = _NODE_ID_RE.match(line)
        if not m or m.group(1) in _DOT_KEYWORDS:
            continue
        lm = _LABEL_RE.search(line)
        if not lm or "quadrant=" not in lm.group(1):
            continue
        desc, quadrant, status, severity = _parse_label_attrs(lm.group(1))
        nodes.append(Unknown(m.group(1), desc, quadrant, status, severity, i))
    return nodes


def quadrant_counts(nodes: list[Unknown]) -> dict[str, dict[str, int]]:
    """Per-quadrant open/total counts plus open-high counts."""
    counts = {q: {"open": 0, "total": 0, "open_high": 0} for q in QUADRANTS}
    for n in nodes:
        if n.quadrant not in counts:
            continue
        counts[n.quadrant]["total"] += 1
        if n.status == "open":
            counts[n.quadrant]["open"] += 1
            if n.severity == "high":
                counts[n.quadrant]["open_high"] += 1
    return counts


def dominant_quadrant(map_path: Path | str = DEFAULT_MAP) -> str:
    """Triage routing token: uu | uk | ku | clear.

    EXACT precedence of scripts/dominant_quadrant.sh (first match wins):
      1. any high-severity open unknown-unknown             -> uu
      2. uu open > 0 and >= both uk-open and ku-open        -> uu
      3. uk open > 0 and >= ku open                         -> uk
      4. ku open > 0                                        -> ku
      5. otherwise (including missing map)                  -> clear
    """
    path = Path(map_path)
    if not path.exists():
        return "clear"  # nothing to triage yet; cartography creates the map
    c = quadrant_counts(parse_map(path))
    uu, uk, ku = c["uu"]["open"], c["uk"]["open"], c["ku"]["open"]
    if c["uu"]["open_high"] > 0:
        return "uu"
    if uu > 0 and uu >= uk and uu >= ku:
        return "uu"
    if uk > 0 and uk >= ku:
        return "uk"
    if ku > 0:
        return "ku"
    return "clear"


# ---------------------------------------------------------------------------
# Seeding and mutation
# ---------------------------------------------------------------------------


def seed_map(
    map_path: Path | str = DEFAULT_MAP, task: str = "", force: bool = False
) -> Path:
    """Seed a fresh map from the bundled template. Refuses to overwrite
    an existing map unless ``force`` -- the map is a living artifact."""
    path = Path(map_path)
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists (pass force=True to overwrite)")
    content = map_template().read_text()
    if task:
        content = content.replace("<describe the task here>", task.replace('"', "'"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _cluster_span(lines: list[str], quadrant: str) -> tuple[int, int]:
    """(start, end) line indexes of ``subgraph cluster_<q> { ... }``.
    ``end`` is the index of the closing brace line."""
    start = None
    for i, line in enumerate(lines):
        if f"subgraph cluster_{quadrant}" in line:
            start = i
            break
    if start is None:
        raise ValueError(f"cluster_{quadrant} not found in map")
    depth = 0
    for i in range(start, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if depth == 0 and i > start:
            return start, i
    raise ValueError(f"unbalanced braces in cluster_{quadrant}")


def _node_line(node_id: str, desc: str, quadrant: str, status: str, severity: str | None) -> str:
    attrs = f"quadrant={quadrant}, status={status}"
    if severity:
        attrs += f", severity={severity}"
    desc = desc.replace('"', "'")
    extra = ""
    if quadrant == "uu":
        extra = ', fillcolor="#3A3A36", fontcolor="#DDD8CC", color="#777770"'
    elif severity == "high":
        extra = ', color="#C46A4A", penwidth=2'
    return f'    {node_id} [label="{desc}\\n[{attrs}]"{extra}]'


def add_unknown(
    map_path: Path | str,
    quadrant: str,
    desc: str,
    status: str = "open",
    severity: str | None = None,
) -> str:
    """Append a node to a quadrant's cluster. Returns the new node id."""
    if quadrant not in QUADRANTS:
        raise ValueError(f"quadrant must be one of {QUADRANTS}, got {quadrant!r}")
    path = Path(map_path)
    lines = path.read_text().splitlines()
    existing = {n.node_id for n in parse_map(path)}
    n = 1
    while f"{quadrant}_{n}" in existing:
        n += 1
    node_id = f"{quadrant}_{n}"
    _, end = _cluster_span(lines, quadrant)
    lines.insert(end, _node_line(node_id, desc, quadrant, status, severity))
    path.write_text("\n".join(lines) + "\n")
    return node_id


def reclassify(
    map_path: Path | str,
    node_id: str,
    quadrant: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    technique: str = "",
) -> None:
    """Update a node's label attrs; physically move it if the quadrant changes.
    Never deletes -- resolved is a status, not a disappearance."""
    path = Path(map_path)
    lines = path.read_text().splitlines()
    nodes = {n.node_id: n for n in parse_map(path)}
    if node_id not in nodes:
        raise KeyError(f"node {node_id!r} not found in {path}")
    node = nodes[node_id]
    line = lines[node.line_no]
    if quadrant:
        line = re.sub(r"quadrant=\w+", f"quadrant={quadrant}", line)
    if status:
        line = re.sub(r"status=\w+", f"status={status}", line)
    if severity:
        if "severity=" in line:
            line = re.sub(r"severity=\w+", f"severity={severity}", line)
        else:
            line = line.replace("]\"", f", severity={severity}]\"", 1)
    if technique:
        line = line.rstrip()
        line += f"  // reclassified via {technique}"
    if quadrant and quadrant != node.quadrant:
        del lines[node.line_no]
        _, end = _cluster_span(lines, quadrant)
        lines.insert(end, line)
    else:
        lines[node.line_no] = line
    path.write_text("\n".join(lines) + "\n")


def prune_placeholders(map_path: Path | str) -> int:
    """Remove template placeholder nodes (labels still wrapped in <...>) and
    any edges referencing them. Returns the number of lines removed."""
    path = Path(map_path)
    lines = path.read_text().splitlines()
    placeholder_ids = {
        n.node_id for n in parse_map(path) if n.desc.startswith("<") and n.desc.endswith(">")
    }
    if not placeholder_ids:
        return 0
    kept: list[str] = []
    removed = 0
    for line in lines:
        tokens = re.findall(r"[A-Za-z_]\w*", line.split("[")[0])
        if any(t in placeholder_ids for t in tokens) and ("[" in line or "->" in line):
            removed += 1
            continue
        kept.append(line)
    path.write_text("\n".join(kept) + "\n")
    return removed


# ---------------------------------------------------------------------------
# Terminal briefing render (unknowns:context/ascii-render-spec.md)
#
# The terminal render is a plain-language BRIEFING, not a grid: the 2x2
# matrix visual belongs to the PNG (`unknowns png`). Rules: wrap, never
# truncate; no quadrant jargon (kk/ku/uk/uu stay internal); every render
# ends with a NEXT step derived from the triage token.
# ---------------------------------------------------------------------------

_WIDTH = 78

_SECTION_TITLES = {
    "ku": "Open questions you know about",
    "uk": "Things you'd recognize but haven't said",
    "uu": "Blindspots surfaced",
}

_NEXT_LINES = {
    "ku": 'Answer the numbered questions under "Open questions" -- '
          'say "interview me" to go one at a time.',
    "uk": "These are preferences you'll recognize on sight but can't describe "
          "yet -- ask for a quick prototype fan-out and react to options.",
    "uu": 'Probe the blindspots before planning -- say "blindspot pass" to dig '
          "into them; a high-severity one can reshape the whole approach.",
    "clear": "No open unknowns -- proceed to planning.",
}

import textwrap as _textwrap


def _task_title(map_path: Path) -> str:
    """Extract the task description from the graph title, if present."""
    try:
        m = re.search(r'task:\s*([^"\\]+)"', map_path.read_text())
        return m.group(1).strip() if m else ""
    except OSError:
        return ""


def _wrap_item(text: str, first_prefix: str) -> list[str]:
    cont = " " * len(first_prefix)
    return _textwrap.wrap(
        text, width=_WIDTH, initial_indent=first_prefix, subsequent_indent=cont
    ) or [first_prefix.rstrip()]


def render_ascii(map_path: Path | str = DEFAULT_MAP) -> str:
    """Plain-language terminal briefing of the map.

    Sections: settled items first, then the three open-unknown sections in
    reading order (known unknowns, unknown knowns, unknown unknowns) with
    continuous numbering, `!!` marking high severity, and a `start here`
    marker on the triage-dominant section. Ends with `NEXT ->`.
    """
    path = Path(map_path)
    nodes = parse_map(path)
    if not nodes:
        return "(no unknowns map found -- seed one with `unknowns seed <task>`)"
    c = quadrant_counts(nodes)
    total = sum(c[q]["total"] for q in QUADRANTS)
    open_n = sum(c[q]["open"] for q in QUADRANTS)
    token = dominant_quadrant(path)

    lines: list[str] = []

    # Header: title left, iceberg progress right.
    title = _task_title(path)
    left = f"UNKNOWNS -- {title}" if title else "UNKNOWNS"
    right = f"{open_n} open / {total} total"
    if len(left) + len(right) + 2 > _WIDTH:
        lines.append(left)
        lines.append(right.rjust(_WIDTH))
    else:
        lines.append(left + " " * (_WIDTH - len(left) - len(right)) + right)

    # Settled: known knowns plus anything already resolved.
    settled_kk = [n for n in nodes if n.quadrant == "kk" and n.status != "open"]
    resolved = [n for n in nodes if n.quadrant != "kk" and n.status == "resolved"]
    lines.append("")
    lines.append("Settled (what you've told me, plus anything already resolved)")
    if not settled_kk and not resolved:
        lines.append("  (nothing yet)")
    for n in settled_kk[:6]:
        lines.extend(_wrap_item(n.desc, "  * "))
    for n in resolved[:6]:
        lines.extend(_wrap_item(n.desc + " (resolved)", "  + "))
    hidden = max(0, len(settled_kk) - 6) + max(0, len(resolved) - 6)
    if hidden:
        lines.append(f"  ... and {hidden} more")

    # Open sections with continuous numbering.
    num = 1
    for q in ("ku", "uk", "uu"):
        open_items = [n for n in nodes if n.quadrant == q and n.status == "open"]
        open_items.sort(key=lambda n: _SEVERITY_ORDER.get(n.severity, 3))
        header = f"{_SECTION_TITLES[q]} ({len(open_items)})"
        if token == q and open_items:
            header += "   <- start here"
        lines.append("")
        lines.append(header)
        if not open_items:
            lines.append("  (none)")
        for n in open_items:
            mark = "!!" if n.severity == "high" else "  "
            lines.extend(_wrap_item(n.desc, f" {mark} {num}. "))
            num += 1

    lines.append("")
    lines.extend(_wrap_item(_NEXT_LINES[token], "NEXT -> "))
    return "\n".join(lines)
