# The Unknowns Matrix -- Full Methodology

Credit: Thariq ([@trq212](https://x.com/trq212)), Claude Code @ Anthropic --
"A Field Guide to Fable: Finding Your Unknowns"
([original thread](https://x.com/trq212/status/2073100352921215386)).

This document is the heavy reference for `unknowns:unknowns-cartographer`.
It is loaded only when the cartographer is spawned -- never in root sessions.

## Map vs. territory

The map is the representation of the work to be done: your prompts, skills,
and context -- what you give the agent. The territory is where the work
actually happens: the codebase, the real world, its actual constraints. The
difference between the map and the territory is what we call **unknowns**.
When an agent runs into an unknown, it makes a decision based on its best
guess of what you want. The more work being done, the more unknowns it may
run into. Just planning ahead isn't always enough -- unknowns surface deep in
implementation too, and sometimes point to solving the problem a different
way altogether. Finding unknowns is an iterative process that spans before,
during, and after implementation.

## The four quadrants

| Quadrant | Subtitle | Definition |
|---|---|---|
| **Known knowns (KK)** | "what's in your prompt" | What you tell the agent you want, explicitly. |
| **Known unknowns (KU)** | "questions you know to ask" | What you haven't figured out yet, but are aware that you haven't. |
| **Unknown knowns (UK)** | "I'll know it when I see it" | So obvious you'd never write it down, but you'd recognize it if you saw it. |
| **Unknown unknowns (UU)** | "what you never considered" | What you haven't considered at all -- knowledge you don't know you lack. |

Instructing well is a delicate balance: too specific and the agent follows
instructions even when a pivot would be better; too vague and it falls back
on generic best practices that may not fit. Unaccounted-for unknowns fail
both ways -- you don't know when the path is obstructed, and you don't know
when it's clear but the agent still hedges. The best agentic coders have
relatively few unknowns because they are deeply in-sync with the codebase
and the model. But they also *assume* unknowns and plan around them --
reducing and pre-empting your unknowns is the core skill of agentic coding,
and it improves with practice.

## Per-quadrant resolution techniques

### Blindspot pass (targets: UU)
When starting work in unfamiliar territory -- a new part of the codebase, an
unfamiliar domain -- you likely carry unknown unknowns: you don't know what
questions to ask, what good looks like, what history exists, or what
potholes to avoid. Ask explicitly for a "blindspot pass" on your "unknown
unknowns," and give context on who you are and what you already know. This
is the trigger for the `/blindspot` skill in this bundle.

### Brainstorms and prototypes (targets: UK)
In areas with a lot of unknown-knowns -- criteria you only recognize when
you see them -- brainstorm and prototype before implementing. Verbalizing
unknown-knowns early is cheap; discovering them mid-implementation is
expensive, because small spec changes can cause drastically different code
and are hard to revert. Visual design is the classic example: ask for
several wildly different directions and react to them rather than describing
taste in words. This is the trigger for the pipeline's `fanout` node
(parallel prototype generation, human picks).

### Interviews (targets: KU)
After sufficient brainstorming, unknowns usually remain. Ask the agent to
interview you **one question at a time**, prioritizing questions whose
answers would change the architecture (data models, interfaces, UX flows)
over cosmetic ones. This is the trigger for the `/interview` mode.

### References (targets: KU/UK)
Sometimes you can't describe what you want in words -- you lack the
language, or it would take too long. Point the agent at source code instead:
a library, a component you like, a module on a site whose underlying markup
you want reproduced. Source is the richest reference; screenshots alone lose
structure.

### Decision-first implementation plans (targets: KU, pre-merge check on UK)
Before implementing, ask for a plan that leads with the decisions most
likely to change -- data model changes, new type interfaces, user-facing
behavior -- and buries mechanical refactoring at the bottom. This surfaces
things you might actually need to alter, instead of burying them under
boilerplate. This is the `plan` node in the lifecycle pipeline, gated by a
human review (`plan_gate`).

### Deviations log (during implementation)
No matter how much planning happens, unknown unknowns lurk during
implementation. Keep a temporary `implementation-notes.md` file. When an
edge case forces a deviation from the plan: pick the conservative option,
log it under `## Deviations`, and keep going. This turns implementation-time
discoveries into a durable record instead of silent, unreviewable choices.

### Pitches and explainers (post-implementation)
Getting buy-in requires reviewers to share your unknowns quickly. A pitch
artifact that packages the prototype, the spec, and the implementation notes
accelerates both understanding (reviewers start where you started) and
approval (experts see that you accounted for the failure points they'd
anticipate).

### Quiz gates (post-implementation, targets: verifying your own understanding)
After a long session, code diffs alone give only a shallow read of what
happened -- much of the behavior depends on existing code paths you didn't
touch. Ask the agent to quiz you on the change after providing context,
intuition, and a summary. Only merge after passing the quiz. This is the
`quiz` / `quiz_gate` / `grade` cycle in the lifecycle pipeline.

## Map node schema

Every unknown is a DOT node in `.ai/unknowns-map.dot`, inside one of four
quadrant clusters (`cluster_kk`, `cluster_ku`, `cluster_uk`, `cluster_uu`).
Node attributes (encoded in the label, since DOT node records don't have
first-class custom attrs in the rendered form):

```
node_id [label="<short description>\n[quadrant=kk|ku|uk|uu, status=given|open|resolved, severity=low|med|high]"]
```

- **quadrant**: which of the four cells the unknown currently lives in.
- **status**: `given` (stated up front, KK only), `open` (unresolved), or
  `resolved` (closed out by a technique).
- **severity**: `low` | `med` | `high` -- how much this unknown could change
  the architecture or the outcome if answered differently.

**Reclassification edges** are dashed, colored `#C46A4A` (terracotta) for
uu-origin moves and `#5E7A56` (green) for ku-to-resolved moves, and carry a
label naming the technique that moved the node: `"blindspot pass\nsurfaced
it"`, `"interview\nresolved it"`, `"prototype reaction\nnamed the
criterion"`. These edges are the point of the whole system -- they are the
audit trail of how the map converged on the territory.

## Lifecycle and severity/color conventions

Unknowns migrate `uu -> ku -> resolved` (or `uk -> ku -> resolved`) as
techniques run. Never delete a node -- `resolved` is a status, not a
disappearance; the history of how something moved through the quadrants is
the point. Progress is measured like an iceberg: the count of `open` nodes
shrinks over the lifecycle while `resolved` grows.

Styling (shared with `unknowns:context/map-template.dot` and
`unknowns:pipelines/unknowns-lifecycle.dot`):

- Background `#F8F5EE` (cream), font Georgia -- matches the article's HTML
  artifact design system.
- Grey (`#E8E4DA` / unstyled) -- minor, low-severity, or mechanical/guard
  nodes.
- Terracotta (`#E5A88E` fill / `#C46A4A` stroke) -- severe, human gates, or
  reclassifications that originated from a danger-quadrant (uu) finding.
- Dark card (`#2B2B28` fill, `#DDD8CC`/`#E5A88E` font) -- reserved for the
  **unknown-unknowns cluster only**, per the article's danger-quadrant
  convention. Nothing else uses the dark treatment.
- Green (`#DDE8D9`) -- resolved.

## Worked example: launching Fable

The article's own closing example shows the quadrants in motion. Thariq
edited an entire launch video with Claude Code -- a domain he wasn't expert
in. He started from what he *did* know (KK: Claude could use code to edit
and transcribe video). He didn't know if transcription was accurate enough
to cut pauses cleanly with ffmpeg, so he asked Claude to explain how
transcription (Whisper-style) worked -- a KU resolved by explanation rather
than an interview, because the question was technical, not preferential. He
wanted UI timed to his speech but wasn't sure it would work, so he asked for
a Remotion prototype -- a UK resolved by prototyping, not description. The
video looked "muted," which he knew was about color grading, but he didn't
know what color grading *was* -- a pure UU. His first instinct (ask for a
few graded variations to pick from) would have treated it as a UK, but he
realized he didn't even know what "good" looked like -- so he asked Claude
to teach him first, converting the UU into a UK he could then judge. This is
the general pattern: identify which quadrant an unknown actually belongs to
before picking a technique, because the wrong technique for the quadrant
(asking to "pick a favorite" when you don't know what good looks like yet)
wastes a round trip.

## Recommending a technique

When asked to recommend the next technique, count `status=open` nodes per
quadrant. Recommend in this order of precedence: any high-severity `uu`
node present -> blindspot pass; else `uk` open count is the largest ->
prototype fan-out; else any `ku` open count > 0 -> interview; else -> plan
(everything sufficiently resolved). This precedence is also encoded
deterministically in `unknowns:scripts/dominant_quadrant.sh` for the
pipeline's shell-guard triage node -- the cartographer's recommendation and
the script's routing token should agree.
