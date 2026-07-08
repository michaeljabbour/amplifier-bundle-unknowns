# Terminal Render Spec -- The Unknowns Briefing

`unknowns:unknowns-cartographer` renders `.ai/unknowns-map.dot` in every
response as a plain-language **briefing**, not a grid. The 2x2 matrix visual
belongs to the PNG (`unknowns png` / graphviz); a terminal cell is too narrow
for real unknowns, and truncated jargon creates no value. The briefing's job
is the research's actual value moment: show the user the questions they should
answer next, in their own language, and move them to answer.

**Canonical renderer:** `unknowns_map.render_ascii` (the `unknowns status`
CLI and the `unknowns_map` tool's `status` operation). When the tool is
mounted, use its output verbatim -- do not improvise a layout.

## Rules

1. **Wrap, never truncate.** Full sentences, hanging indent, <=78 columns.
2. **No quadrant jargon.** The codes (kk/ku/uk/uu) and article vocabulary
   ("known unknowns", "quadrant", "matrix") stay internal. Section names are
   plain language (below).
3. **Continuous numbering across open sections** so the user can say
   "answer 2" or "3 doesn't matter".
4. **`!!` marks high severity.** Highest severity sorts first within a section.
5. **`<- start here`** marks the triage-dominant section (the deterministic
   `dominant_quadrant` token decides -- never judgment).
6. **Always end with `NEXT ->`** -- one concrete move derived from the triage
   token (interview / prototype fan-out / blindspot pass / proceed to plan).

## Layout

```
UNKNOWNS -- <task>                                          N open / M total

Settled (what you've told me, plus anything already resolved)
  * <known knowns; `+ ... (resolved)` for resolved items from any section>

Open questions you know about (N)   <- start here        [internal: ku]
 !! 1. <high-severity question, wrapped with hanging indent>
    2. <question>

Things you'd recognize but haven't said (N)               [internal: uk]
    3. <preference the user will recognize on sight>

Blindspots surfaced (N)                                   [internal: uu]
    4. <thing nobody had considered>

NEXT -> <one move: e.g. Answer the numbered questions under "Open
        questions" -- say "interview me" to go one at a time.>
```

(The `[internal: ...]` annotations above document the mapping for THIS spec
only -- they never appear in output.)

## Worked example

```
UNKNOWNS -- add rate limiting to the API gateway              4 open / 5 total

Settled (what you've told me, plus anything already resolved)
  * Add rate limiting to the API gateway.

Open questions you know about (2)   <- start here
 !! 1. Which rate-limit algorithm? Token bucket vs sliding window vs fixed
       window vs leaky bucket -- this decides your data model and burst
       behavior.
    2. What are the limits, and keyed how? Per-IP, per-API-key, or per-route,
       and at what thresholds.

Things you'd recognize but haven't said (1)
    3. How a 429 should feel to your API consumers -- response body, Retry-
       After / X-RateLimit-* headers, docs tone.

Blindspots surfaced (1)
    4. If the gateway runs multiple replicas, in-memory counters drift and
       your limits silently multiply. Shared state (e.g. Redis) or not?

NEXT -> Answer the numbered questions under "Open questions" -- say "interview
        me" to go one at a time.
```

## After the render: ask, don't just display

The map creates value only when unknowns get resolved. After rendering, the
cartographer (or relaying agent) ends its response by **asking the single
most important open question** -- the first numbered item in the
`<- start here` section -- in one plain sentence. Display without a question
is a dashboard; the research intends a conversation.
