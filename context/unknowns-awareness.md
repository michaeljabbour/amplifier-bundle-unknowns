# Unknowns: Map vs. Territory

Agentic work quality is bottlenecked by unknowns -- gaps between your prompt
(the map) and the codebase/reality (the territory). Four kinds:

- **Known knowns** -- what's in your prompt
- **Known unknowns** -- flagged, unresolved questions
- **Unknown knowns** -- obvious to you, never stated ("I'll know it when I see it")
- **Unknown unknowns** -- never considered at all

## The map is the spine

Before non-trivial work, delegate to `unknowns:unknowns-cartographer` to seed
and render `.ai/unknowns-map.dot` -- a 4-quadrant DOT graph -- so the user
sees the territory *before* any technique runs. The cartographer always
renders a plain-language terminal briefing in its response (numbered open
questions ending with a NEXT step), plus the 2x2 PNG when graphviz is
available.

## Triggers

| Map state | Technique |
|---|---|
| Unknown-unknowns heavy | `/blindspot` skill |
| Known-unknowns heavy | `/interview` mode |
| Unknown-knowns heavy | Prototype fan-out (the lifecycle pipeline) |
| Before merging significant changes | Quiz gate (the lifecycle pipeline) |

Run the full lifecycle: `unknowns:pipelines/unknowns-lifecycle.dot` via the
`run_pipeline` tool.

## During implementation

Keep an `implementation-notes.md` with a `## Deviations` section. On an edge
case that forces a plan deviation: pick the conservative option, log it, keep
going.

## Layers on superpowers

This bundle is an entry ramp (before `/brainstorm`) and an exit gate (before
`/finish`) -- not a replacement for the TDD workflow. For the full 4-quadrant
methodology, resolution techniques, and map node schema, delegate to
`unknowns:unknowns-cartographer`.

Credit: Thariq, "A Field Guide to Fable: Finding Your Unknowns."
