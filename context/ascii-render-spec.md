# ASCII Render Spec -- Terminal 2x2

`unknowns:unknowns-cartographer` renders `.ai/unknowns-map.dot` as a terminal
2x2 in every response, so the map is visible even without opening a PNG.

## Layout

- Quadrant order matches the article's matrix: **KK** top-left, **KU**
  top-right, **UK** bottom-left, **UU** bottom-right.
- Use box-drawing characters (`┌ ┐ └ ┘ │ ─ ┬ ┴ ┼`) for the grid.
- The **UU** cell gets a heavy/double border (`╔ ╗ ╚ ╝ ║ ═`) -- the danger
  quadrant convention carried over from the DOT dark-card treatment.
- Each cell shows: the quadrant name, a count of `status=open` items, and up
  to 3 highest-severity item names (severity order: high, med, low; ties
  broken by insertion order). Truncate long labels to fit the column width.
- Footer line: iceberg progress -- `N open / M total unknowns`.

## Worked example

```
┌─ KNOWN KNOWNS (0 open) ──────┬─ KNOWN UNKNOWNS (2 open) ─────┐
│ (all given, nothing open)    │ ! token refresh strategy      │
│                               │   which session store?        │
├───────────────────────────────╔═ UNKNOWN UNKNOWNS (2 open) ══╗
│ UNKNOWN KNOWNS (1 open)       ║ ! clock-skew on JWT validate  ║
│   login UX feel               ║   legacy SAML users exist     ║
└───────────────────────────────╚════════════════════════════════╝
  3 open / 6 total unknowns
```

`!` prefixes a `severity=high` item. Adjust column widths to terminal width
when possible; fall back to a fixed 78-column layout otherwise.
