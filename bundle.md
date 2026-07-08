---
bundle:
  name: unknowns
  version: 0.1.0
  description: >
    Find and resolve unknowns -- the gap between your prompt (the map) and
    the codebase/reality (the territory). Implements the 4-quadrant unknowns
    matrix (known knowns, known unknowns, unknown knowns, unknown unknowns)
    from Thariq's "A Field Guide to Fable: Finding Your Unknowns" as a living
    DOT artifact (.ai/unknowns-map.dot) that every technique reads and writes.

    Entry points:
      /blindspot    -- surface unknown-unknowns before starting unfamiliar work
      /interview    -- resolve known-unknowns one question at a time
      unknowns:pipelines/unknowns-lifecycle.dot -- full pre/during/post lifecycle,
                       run via the attractor run_pipeline tool

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  # Register the "attractor" namespace, then reference its interactive entry
  # point by name -- mirrors attractor's own bundle.md self-reference to
  # attractor:behaviors/attractor-core. This gives us the run_pipeline tool
  # (tool-pipeline-run) needed to invoke unknowns:pipelines/unknowns-lifecycle.dot,
  # plus an interactive loop-agent orchestrator with filesystem/bash/search tools.
  - bundle: git+https://github.com/microsoft/amplifier-bundle-attractor@main
  - bundle: attractor:bundles/attractor-interactive
  - bundle: unknowns:behaviors/unknowns
---

# Unknowns Explorer

Find and resolve unknowns before they get expensive to fix -- the gap between
your prompt (the map) and the codebase/reality (the territory). Quick start
and composition notes: unknowns:README.md (read on demand -- not eagerly
loaded). The always-on framing this session carries lives below.

@unknowns:context/unknowns-awareness.md

---

@foundation:context/shared/common-system-base.md
