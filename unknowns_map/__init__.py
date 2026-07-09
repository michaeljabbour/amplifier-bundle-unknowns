"""amplifier-unknowns -- deterministic core + engine seam for the unknowns map.

Leverage levels over this one home (see the amplifier-tool-leverage-patterns
skill and the wiki-weaver exemplar):

    L1  pipelines/unknowns-lifecycle.dot (+ .resolver.yaml)  -- attractor/Resolve
    L2  this package                                          -- import it
    L3  modules/tool-unknowns                                 -- agent-callable tool
    L4  `unknowns` CLI (unknowns_map.cli)                     -- humans + L1 guards

Deterministic map logic lives HERE (map_ops); the LLM logic lives in the
DOT pipeline + agent prompts. scripts/dominant_quadrant.sh is the
zero-dependency shell mirror of ``dominant_quadrant`` (contract-tested).

Rendering is a DATA vs PRESENTATION split: render_ascii and render_pretty_dot
both read the canonical map and never write to it. render_png always renders
through render_pretty_dot -- there is no path in this package that produces a
PNG from the raw machine DOT.
"""

from .engine_runner import load_pipeline, pipeline_path, run_lifecycle
from .map_ops import (
    DEFAULT_MAP,
    QUADRANT_TITLES,
    QUADRANTS,
    Unknown,
    add_unknown,
    dominant_quadrant,
    parse_map,
    prune_placeholders,
    quadrant_counts,
    reclassify,
    render_ascii,
    render_png,
    render_pretty_dot,
    seed_map,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_MAP",
    "QUADRANTS",
    "QUADRANT_TITLES",
    "Unknown",
    "add_unknown",
    "dominant_quadrant",
    "load_pipeline",
    "parse_map",
    "pipeline_path",
    "prune_placeholders",
    "quadrant_counts",
    "reclassify",
    "render_ascii",
    "render_png",
    "render_pretty_dot",
    "run_lifecycle",
    "seed_map",
    "__version__",
]
