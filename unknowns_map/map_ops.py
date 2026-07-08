"""Deterministic operations on .ai/unknowns-map.dot.

This module is the SINGLE Python home for the map's deterministic logic:
parsing, quadrant counts, triage precedence, seeding, node add/reclassify,
and the terminal ASCII 2x2 render (per unknowns:context/ascii-render-spec.md).

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
# ASCII render (unknowns:context/ascii-render-spec.md)
# ---------------------------------------------------------------------------

_CELL = 34  # inner text width per column (fixed 78-col-safe fallback)


def _fit(text: str, width: int) -> str:
    if len(text) > width:
        return text[: width - 1] + "\u2026"
    return text.ljust(width)


def _items(nodes: list[Unknown], quadrant: str) -> list[str]:
    open_nodes = [n for n in nodes if n.quadrant == quadrant and n.status == "open"]
    open_nodes.sort(key=lambda n: _SEVERITY_ORDER.get(n.severity, 3))
    out = []
    for n in open_nodes[:3]:
        prefix = "! " if n.severity == "high" else "  "
        out.append(prefix + n.desc)
    return out


def render_ascii(map_path: Path | str = DEFAULT_MAP) -> str:
    """Terminal 2x2: KK top-left, KU top-right, UK bottom-left,
    UU bottom-right with heavy/double border (the danger quadrant)."""
    nodes = parse_map(map_path)
    if not nodes:
        return "(no unknowns map found -- seed one with `unknowns seed <task>`)"
    c = quadrant_counts(nodes)

    kk_items = _items(nodes, "kk") or ["(all given, nothing open)"]
    ku_items = _items(nodes, "ku") or ["(none)"]
    uk_items = _items(nodes, "uk") or ["(none)"]
    uu_items = _items(nodes, "uu") or ["(none)"]

    def hdr(ch_l: str, fill: str, ch_m: str, ch_r: str, t1: str, t2: str) -> str:
        left = f"{ch_l}{fill} {t1} "
        left += fill * (_CELL + 2 - (len(left) - 1))
        right = f"{ch_m}{fill} {t2} " if t2 else ch_m
        right += fill * (_CELL + 2 - (len(right) - 1))
        return left + right + ch_r

    def row(l_text: str, r_text: str, r_heavy: bool = False) -> str:
        rv = "\u2551" if r_heavy else "\u2502"
        return f"\u2502 {_fit(l_text, _CELL)} {rv} {_fit(r_text, _CELL)} {rv}"

    top = hdr("\u250c", "\u2500", "\u252c",
              "\u2510",
              f"{QUADRANT_TITLES['kk']} ({c['kk']['open']} open)",
              f"{QUADRANT_TITLES['ku']} ({c['ku']['open']} open)")

    top_rows = []
    for i in range(max(len(kk_items), len(ku_items))):
        top_rows.append(row(kk_items[i] if i < len(kk_items) else "",
                            ku_items[i] if i < len(ku_items) else ""))

    # Middle divider: plain on the left, heavy opening for the UU cell.
    mid_left = "\u251c" + "\u2500" * (_CELL + 2)
    uu_title = f" {QUADRANT_TITLES['uu']} ({c['uu']['open']} open) "
    mid_right = "\u2554\u2550" + uu_title
    mid_right += "\u2550" * (_CELL + 2 - (len(mid_right) - 1)) + "\u2557"
    mid = mid_left + mid_right

    bottom_left = [f"{QUADRANT_TITLES['uk']} ({c['uk']['open']} open)"] + uk_items
    bottom_rows = []
    for i in range(max(len(bottom_left), len(uu_items))):
        bottom_rows.append(row(bottom_left[i] if i < len(bottom_left) else "",
                               uu_items[i] if i < len(uu_items) else "",
                               r_heavy=True))

    bot = ("\u2514" + "\u2500" * (_CELL + 2)
           + "\u255a" + "\u2550" * (_CELL + 2) + "\u255d")

    total = sum(c[q]["total"] for q in QUADRANTS)
    open_n = sum(c[q]["open"] for q in QUADRANTS)
    footer = f"  {open_n} open / {total} total unknowns"

    return "\n".join([top, *top_rows, mid, *bottom_rows, bot, footer])
