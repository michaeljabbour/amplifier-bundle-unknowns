"""The seam between the deterministic lib and the attractor engine.

The unknowns lifecycle is LLM-logic: the graph + prompts in
``pipelines/unknowns-lifecycle.dot`` ARE the logic (leverage-pattern DRY rule).
This module never re-implements them -- it fills the ``$goal`` token and hands
the graph to a runner:

1. **In an Amplifier session** (primary L1 path): the attractor bundle's
   ``run_pipeline`` tool runs ``unknowns:pipelines/unknowns-lifecycle.dot``
   directly -- no code here involved.
2. **Programmatic / CLI** (``run_lifecycle``): the PreparedBundle path modeled
   on wiki-weaver's engine_runner -- load the attractor bundle, overlay a
   ``loop-pipeline`` orchestrator with our filled DOT, run one session.

``amplifier-foundation`` is an OPTIONAL runtime prerequisite (install the
``engine`` extra); the deterministic lib and CLI work without it.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ._assets import pipeline_dot

logger = logging.getLogger(__name__)

# The attractor bundle: provides the loop-pipeline orchestrator + engine.
ATTRACTOR_BUNDLE = "git+https://github.com/microsoft/amplifier-bundle-attractor@main"

_MISSING_FOUNDATION = (
    "run_lifecycle requires amplifier-foundation (and a configured Amplifier "
    "install for API keys / bundle cache). Install with:\n"
    "    pip install 'amplifier-unknowns[engine]'\n"
    "or run the pipeline inside an Amplifier session via the attractor "
    "run_pipeline tool: unknowns:pipelines/unknowns-lifecycle.dot"
)


def pipeline_path() -> Path:
    """Path to the canonical lifecycle DOT (dev tree or installed wheel)."""
    return pipeline_dot()


def load_pipeline(goal: str) -> str:
    """Return the lifecycle DOT with the ``$goal`` token substituted."""
    dot = pipeline_path().read_text()
    return dot.replace("$goal", goal.replace('"', "'"))


async def run_lifecycle(
    goal: str,
    cwd: Path | str | None = None,
    execute_prompt: str = "Run the pipeline",
) -> Any:
    """Run the unknowns lifecycle through the attractor engine.

    PreparedBundle path (same shape as wiki-weaver's engine_runner):
        base     = await load_bundle(ATTRACTOR_BUNDLE)
        overlay  = Bundle(session={"orchestrator": {"module": "loop-pipeline",
                                                    "config": {"dot_source": dot}}})
        prepared = await base.compose(overlay).prepare()
        session  = await prepared.create_session(session_cwd=cwd)
        async with session: return await session.execute(execute_prompt)
    """
    try:
        from amplifier_foundation import Bundle, load_bundle
    except ImportError as exc:  # fail loud, with the fix
        raise RuntimeError(_MISSING_FOUNDATION) from exc

    dot_source = load_pipeline(goal)
    base = await load_bundle(ATTRACTOR_BUNDLE)
    overlay = Bundle(
        session={
            "orchestrator": {
                "module": "loop-pipeline",
                "config": {"dot_source": dot_source},
            }
        }
    )
    prepared = await base.compose(overlay).prepare()
    session = await prepared.create_session(session_cwd=str(cwd or Path.cwd()))

    # Pipeline box nodes spawn per-node sub-sessions via the session.spawn
    # capability. PreparedBundle exposes a default spawn; register it when
    # present so LLM nodes work outside a full Amplifier app session.
    spawn = getattr(prepared, "spawn", None)
    coordinator = getattr(session, "coordinator", None)
    if spawn is not None and coordinator is not None:
        try:
            coordinator.register_capability("session.spawn", spawn)
        except Exception as exc:
            logger.warning("could not register session.spawn capability: %s", exc)

    async with session:
        return await session.execute(execute_prompt)
