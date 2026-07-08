# Working in amplifier-bundle-unknowns

This is an Amplifier **bundle repo** — composition (YAML/markdown/DOT), not a
Python package. There is no test suite; validation happens through bundle
tooling.

## Validate

- **Bundle validity:** run the `validate-bundle-repo` flow from an Amplifier
  session (it checks composition, namespaces, and auto-regenerates a stale
  `bundle.dot`).
- **Conformance:** run `/audit-bundle .` (conformance bundle) before opening
  a PR or after any structural change.
- **Pipeline DOT sanity:** `dot -Tpng pipelines/unknowns-lifecycle.dot -o /tmp/lifecycle.png`
  (Graphviz must parse it cleanly).
- **Shell guard:** `bash scripts/dominant_quadrant.sh` against a sample
  `.ai/unknowns-map.dot` if you touch the triage logic.

## Regenerate docs diagram

`bundle.dot` + `bundle.png` at the repo root follow the bundle-to-dot v3
convention (embedded `source_hash` freshness tracking). Regenerate after
changing `bundle.md`, anything in `behaviors/`, `agents/`, `context/`,
`modes/`, or `skills/`:

```python
from amplifier_foundation.bundle_docs import bundle_repo_dot
open("bundle.dot", "w").write(bundle_repo_dot("."))
```

```bash
dot -Tpng bundle.dot -o bundle.png
```

Note: `.gitignore` excludes `*.png` but explicitly re-includes `bundle.png`.

## Pitfalls

- **Include the modes *behavior*, NOT the full amplifier-bundle-modes bundle**
  in `behaviors/unknowns.yaml` — the full bundle transitively includes
  foundation, which would re-run foundation's includes a second time
  (see the comment at `behaviors/unknowns.yaml:15-19`).
- **`context/unknowns-awareness.md` is propagated via `context.include` in
  `behaviors/unknowns.yaml` only.** Do NOT also `@mention` it from
  `bundle.md` — that duplicates its content in the system prompt of every
  direct user of this bundle.
- **The living map (`.ai/unknowns-map.dot`) is a runtime artifact** — it is
  generated per-task and gitignored. Never commit one.
- **`docs/` is gitignored** — it holds a local reference copy of the original
  article and images (not redistributed). Don't reference `docs/` paths from
  bundle composition files.
- **`/blindspot` must remain an inline skill** (it converses with the user);
  do not convert it to a fork skill.
- **`tool-skills` has NO @mention resolution** — a `config.skills:` entry like
  `"@unknowns:skills"` is *silently ignored* (skills sit on disk, never
  materialize, no error anywhere). Use the git self-reference form:
  `git+https://github.com/michaeljabbour/amplifier-bundle-unknowns@main#subdirectory=skills`.
  Note the asymmetry: `hooks-mode`'s `search_paths` DOES resolve @mentions —
  the two modules use different code paths. Live-confirmed in a DTU run
  (2026-07-08); a static conformance audit had passed the @mention form.
- **`/unknownfinder` is a thin alias** for the `unknowns:unknownfinder` agent —
  the method lives only in `agents/unknownfinder.md`. Never re-implement the
  procedure in the skill; edit the agent.
