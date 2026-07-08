---
name: blindspot-pass
description: "Surface the user's unknown unknowns before starting unfamiliar work -- a taught, teach-don't-list pass over blindspots in a codebase area or domain. Triggers on 'blindspot pass', 'unknown unknowns', 'what am I missing', 'help me prompt you better'."
user-invocable: true
model_role: reasoning
---

# Blindspot Pass

You are running **inline, in this conversation** -- not forked. This skill
must converse with the user, so it cannot be a fork skill (a forked
sub-session cannot see this conversation and cannot ask follow-up
questions). Implements the article's "Blind Spot Pass" technique: surfacing
unknown unknowns for someone entering unfamiliar territory (a new part of
the codebase, or an unfamiliar domain).

## User Instruction

$ARGUMENTS

## Procedure

1. **Establish who the user is, relative to this task**, if it isn't already
   evident from context. One or two questions max: their experience with
   this codebase/domain, and what they already know. Don't interrogate --
   if the prompt already gives you enough (see the example prompts below),
   skip straight to step 2.

2. **Survey the relevant territory.** Read the codebase area or research the
   domain in question. You're looking for the things a newcomer wouldn't
   know to ask about: undocumented conventions, historical decisions,
   common failure modes, non-obvious constraints.

3. **Produce 5-10 candidate unknown-unknowns.** Group them by theme. Each
   one must be a concrete, falsifiable statement -- not a vague warning.
   Tag each with a severity (low/med/high) based on how expensive it would
   be to discover this the hard way, mid-implementation.

   Bad: "Auth is complicated, be careful."
   Good: "This codebase uses two parallel session stores (Redis for web,
   JWT for mobile) -- a new provider needs to write to both or mobile
   sessions silently desync. [severity=high]"

4. **Teach, don't just list.** For each item, add one line of *why* it
   matters -- what breaks, or what decision it changes, if the user doesn't
   know it. The goal is the user leaving with better intuition, not just a
   checklist.

5. **Add them to the map.** Delegate to `unknowns:unknowns-cartographer`
   with the full list of surfaced unknowns so it can seed or update
   `.ai/unknowns-map.dot` -- these land in the `uu` (unknown unknowns)
   quadrant, most will immediately get a reclassification edge to `ku` since
   surfacing them converts "didn't know to ask" into "now known to ask."

6. **End with the re-rendered map and a next-step suggestion.** Show the
   updated terminal briefing (from the cartographer's response) and suggest the next
   technique -- usually `/interview` to resolve the newly-surfaced
   known-unknowns, one at a time.

## Example Prompts (from the article)

> "I'm working on adding a new auth provider but I know nothing about the
> auth modules in this codebase. Can you do a blindspot pass to help me
> figure out my relevant unknown unknowns and help me prompt you better."

> "I don't know what color grading is but I need to grade this video. Can
> you teach me to understand my unknown unknowns about color grading, so
> that I can prompt better?"

---

@foundation:context/shared/common-agent-base.md
