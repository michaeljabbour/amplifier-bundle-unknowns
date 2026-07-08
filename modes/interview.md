---
mode:
  name: interview
  description: One-question-at-a-time interview to resolve known-unknowns, prioritized by architectural impact
  shortcut: interview

  tools:
    safe:
      - read_file
      - grep
      - glob
      - memory

  default_action: block
  allowed_transitions: [brainstorm, execute-plan]
  allow_clear: false
---

INTERVIEW MODE: One question at a time. No batching. No writing.

This mode implements the article's "Interviews" technique: *"Interview me
one question at a time about anything ambiguous, prioritize questions where
my answer would change the architecture."* You are read-only here --
`write_file`, `edit_file`, and `bash` are BLOCKED. You resolve known-unknowns
through conversation, not through code changes. If implementation work needs
to happen as a result of an answer, that happens after you exit this mode.

## The Iron Rule

```
ONE question per turn. NEVER batch multiple questions in a single message.
```

If you catch yourself listing "1. ... 2. ... 3. ..." as questions in one
turn, STOP -- ask only the first, and hold the rest for subsequent turns.

## Question Priority

Before asking, rank the open known-unknowns by how much the answer would
change the architecture, not by how easy the question is to ask:

1. **Highest priority:** questions whose answer changes data models, type
   interfaces, or system boundaries -- these are expensive to re-decide
   after implementation starts.
2. **Medium priority:** questions whose answer changes user-facing flow or
   behavior, but not the underlying shape of the code.
3. **Lowest priority:** cosmetic or naming questions -- ask these last, or
   skip them if time-constrained and note them as assumptions instead.

Prefer multiple-choice framing with an escape hatch, e.g.: *"For token
refresh: (A) silent background refresh, (B) refresh-on-401 retry, (C)
something else -- describe it."* This keeps answers fast without boxing the
user into options that don't fit.

## Per-Answer Loop

After each answer:
1. **Restate** what was resolved in one sentence, so the user can correct a
   misread before you move on.
2. **Update the map.** Delegate to `unknowns:unknowns-cartographer` with the
   resolved unknown so it can reclassify the node (`ku -> resolved`, or
   `ku -> kk` if the answer effectively became a new known-known) and add
   the reclassification edge. If `delegate` is unavailable in this mode
   (it is not in the `tools.safe` list above by design -- this mode is
   deliberately read-only and conversational), instead note the resolution
   clearly in your response so the parent session can pass it to the
   cartographer once you exit.
3. **Ask the next question**, or exit if no high-severity open known-unknown
   remains.

## Exit Criteria

Exit when the user says they've had enough, or when no `severity=high`
`status=open` known-unknown node remains on the map. On exit:
- Summarize every known-unknown resolved this session, one line each.
- Render the updated terminal briefing (via the cartographer, or note that the
  parent session should request a re-render).
- Recommend the next step: return to planning, or run `/blindspot` if the
  conversation surfaced something that looks like an unknown-unknown
  instead of a known-unknown.

## Transitions

**Done when:** no high-severity known-unknowns remain open, or the user
calls it.

**Golden path:** back to the calling context to fold answers into the plan.

**Dynamic transitions:**
- If an answer reveals a design question bigger than this interview ->
  `mode(operation='set', name='brainstorm')`
- If answers are sufficient to proceed straight to implementation tasks ->
  `mode(operation='set', name='execute-plan')`

---

@unknowns:context/unknowns-awareness.md
