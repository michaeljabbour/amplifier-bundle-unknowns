# amplifier-bundle-unknowns

Find and resolve unknowns -- the gap between your prompt (the map) and the
codebase/reality (the territory) -- before they get expensive to fix.

Implements the 4-quadrant unknowns matrix and lifecycle techniques from
Thariq's ([@trq212](https://x.com/trq212)) article
["A Field Guide to Fable: Finding Your Unknowns"](https://x.com/trq212/status/2073100352921215386)
as a living Amplifier bundle: a DOT artifact (`.ai/unknowns-map.dot`) that
every technique reads and writes, plus the techniques themselves wired as a
mode, an inline skill, a context-sink agent, and an
[attractor](https://github.com/microsoft/amplifier-bundle-attractor)
pipeline.

**Status:** experimental, v0.1.0.

## The map is the spine

Every stage -- blindspot pass, interview, prototype fan-out, plan, quiz --
is defined as a transformation of one artifact: `.ai/unknowns-map.dot`. It's
a DOT digraph with four quadrant clusters (known knowns, known unknowns,
unknown knowns, unknown unknowns); each unknown is a node tagged
`quadrant=`/`status=`/`severity=`, and dashed reclassification edges record
which technique moved it. The `unknowns:unknowns-cartographer` agent owns
this file: it seeds it from your prompt and a repo scan, renders it as an
ASCII 2x2 in every response (so you see the territory *before* any
technique runs), and updates it as unknowns get resolved. Nothing is ever
deleted -- `resolved` is a status, not a disappearance; the history of how
something moved through the quadrants is the point.

## Quick start

Include this bundle (composes onto foundation):

```yaml
includes:
  - bundle: git+https://github.com/YOUR_ORG/amplifier-bundle-unknowns@main
```

Then, in conversation:

```
/blindspot
"I'm adding a new OIDC auth provider but know nothing about this codebase's auth module."
```

```
/interview
```

Run the full lifecycle (pre -> during -> post) via the pipeline tool that
ships with attractor:

```
run_pipeline(dot_file="unknowns:pipelines/unknowns-lifecycle.dot", goal="Add a new OIDC auth provider")
```

Render the lifecycle diagram yourself at any time:

```bash
dot -Tpng pipelines/unknowns-lifecycle.dot -o pipelines/unknowns-lifecycle.png
```

## File tour

| Path | What it is |
|---|---|
| `bundle.md` | Root bundle: includes foundation + attractor's interactive entry point + this bundle's own behavior |
| `behaviors/unknowns.yaml` | The reusable capability: agent, mode wiring, skill wiring, always-on awareness context |
| `context/unknowns-awareness.md` | Always-on, <500-token pointer: map-vs-territory framing + triggers table |
| `context/unknowns-matrix.md` | Heavy methodology reference -- loaded only by the cartographer agent |
| `context/map-template.dot` | Seed template for a fresh `.ai/unknowns-map.dot`, with the node-attr schema documented inline |
| `context/ascii-render-spec.md` | Terminal 2x2 rendering spec, with a worked example |
| `agents/unknowns-cartographer.md` | Context-sink agent that owns `.ai/unknowns-map.dot` |
| `modes/interview.md` | `/interview` -- one-question-at-a-time, read-only tools, architecture-impact priority |
| `skills/blindspot-pass/SKILL.md` | `/blindspot` -- inline skill (must converse with the user; cannot be a fork skill) |
| `pipelines/unknowns-lifecycle.dot` | The full pre/during/post lifecycle as an attractor pipeline |
| `scripts/dominant_quadrant.sh` | Deterministic shell guard: counts open unknowns per quadrant, routes the pipeline's triage node |

## Composes with

- **[superpowers](https://github.com/microsoft/amplifier-bundle-superpowers)** --
  this bundle is an entry ramp before `/brainstorm` and an exit gate before
  `/finish`, not a replacement for the TDD workflow.
- **[stories](https://github.com/microsoft/amplifier-module-stories)** --
  pitches and explainer artifacts (post-implementation technique) render
  well as HTML stories.
- **[design-intelligence](https://github.com/microsoft/amplifier-bundle-design-intelligence)** --
  the prototype fan-out technique (unknown-knowns quadrant) benefits from
  design-intelligence's HTML artifact conventions.
- **[attractor](https://github.com/microsoft/amplifier-bundle-attractor)** --
  hard dependency. Provides the `run_pipeline` tool, the human-gate
  (`hexagon`) mechanism used by every gate in the lifecycle, and the DOT
  execution engine itself.

## Credit

Thariq ([@trq212](https://x.com/trq212)), Claude Code @ Anthropic --
["A Field Guide to Fable: Finding Your Unknowns"](https://x.com/trq212/status/2073100352921215386),
published July 3, 2026.
