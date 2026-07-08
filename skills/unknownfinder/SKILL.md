---
name: unknownfinder
description: "One-shot unknowns discovery: /unknownfinder <goal> surveys the territory and returns the full 4-quadrant unknowns map (known knowns, known unknowns, unknown knowns, unknown unknowns) with prioritized findings and a recommended next technique. Triggers on 'find my unknowns', 'what don't I know', 'map my unknowns', 'unknownfinder'."
user-invocable: true
model_role: fast
---

# Unknownfinder (slash entry point)

This skill is a **thin alias**: the method itself lives in one place -- the
`unknowns:unknownfinder` agent -- so the `/unknownfinder` command and direct
delegation can never drift apart. Do NOT re-implement the discovery
procedure here.

## User Instruction

$ARGUMENTS

## Procedure

1. **Delegate immediately** to the agent, passing the user's goal:

   ```
   delegate(agent="unknowns:unknownfinder",
            instruction="Find the unknowns for this goal: <the user
            instruction above, plus any relevant context from the current
            conversation -- repo area, constraints, what's already known>",
            context_depth="recent")
   ```

   If `$ARGUMENTS` is empty, ask the user one question -- "What's the goal
   or task you want the unknowns mapped for?" -- then delegate.

2. **Relay the full result.** Show the user the agent's ASCII 2x2 map, the
   prioritized unknowns list, and the recommended next technique verbatim.
   Do not summarize away the severity tags or the why-it-matters lines --
   they are the point.

3. **Offer the next step.** Usually `/interview` (resolve the surfaced
   known-unknowns one at a time) or `/blindspot` (go deeper on
   unknown-unknowns, conversationally).
