"""Amplifier tool module for the unknowns map (leverage level L3).

Thin wrapper over the unknowns_map lib -- no map logic lives here.
Blocking file work runs via asyncio.to_thread per the module guidelines.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from amplifier_core import ToolResult

logger = logging.getLogger(__name__)

try:  # installed wheel path (dependency declared in pyproject)
    import unknowns_map
except ImportError:  # in-repo dev fallback: modules/tool-unknowns/pkg/__init__.py -> repo root
    _repo_root = Path(__file__).resolve().parents[3]
    if (_repo_root / "unknowns_map" / "__init__.py").exists():
        sys.path.insert(0, str(_repo_root))
    import unknowns_map


class UnknownsMapTool:
    """Deterministic operations on .ai/unknowns-map.dot."""

    @property
    def name(self) -> str:
        return "unknowns_map"

    @property
    def description(self) -> str:
        return (
            "Deterministic operations on the unknowns map (.ai/unknowns-map.dot): "
            "seed a fresh map from the template, add/reclassify unknowns, triage "
            "the dominant quadrant (uu|uk|ku|clear), prune template placeholders, "
            "and render the plain-language terminal briefing. Use for exact map "
            "mutations and counts instead of hand-editing the DOT"
            "counts instead of hand-editing the DOT; the LLM techniques "
            "(blindspot pass, interview, quiz) decide WHAT to record -- this tool "
            "records it."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["seed", "status", "triage", "add", "reclassify", "prune"],
                    "description": "Map operation to perform.",
                },
                "map_path": {
                    "type": "string",
                    "description": "Path to the map (default: .ai/unknowns-map.dot).",
                },
                "task": {
                    "type": "string",
                    "description": "seed: one-line task description for the map title.",
                },
                "force": {
                    "type": "boolean",
                    "description": "seed: overwrite an existing map (default false).",
                },
                "quadrant": {
                    "type": "string",
                    "enum": ["kk", "ku", "uk", "uu"],
                    "description": "add: target quadrant. reclassify: new quadrant.",
                },
                "text": {
                    "type": "string",
                    "description": "add: short description of the unknown.",
                },
                "status": {
                    "type": "string",
                    "enum": ["given", "open", "resolved"],
                    "description": "add: initial status (default open). reclassify: new status.",
                },
                "severity": {
                    "type": "string",
                    "enum": ["low", "med", "high"],
                    "description": "Severity for add/reclassify.",
                },
                "node_id": {
                    "type": "string",
                    "description": "reclassify: id of the node to update.",
                },
                "technique": {
                    "type": "string",
                    "description": "reclassify: what moved it (blindspot pass, interview, ...).",
                },
            },
            "required": ["operation"],
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        op = input_data["operation"]
        map_path = input_data.get("map_path") or str(unknowns_map.DEFAULT_MAP)

        def _run() -> str:
            if op == "seed":
                path = unknowns_map.seed_map(
                    map_path,
                    task=input_data.get("task", ""),
                    force=bool(input_data.get("force", False)),
                )
                return f"seeded {path}\n" + unknowns_map.render_ascii(path)
            if op == "status":
                return unknowns_map.render_ascii(map_path)
            if op == "triage":
                return unknowns_map.dominant_quadrant(map_path)
            if op == "add":
                if "quadrant" not in input_data or "text" not in input_data:
                    raise ValueError("add requires 'quadrant' and 'text'")
                node_id = unknowns_map.add_unknown(
                    map_path,
                    input_data["quadrant"],
                    input_data["text"],
                    status=input_data.get("status", "open"),
                    severity=input_data.get("severity"),
                )
                return f"added {node_id}\n" + unknowns_map.render_ascii(map_path)
            if op == "reclassify":
                if "node_id" not in input_data:
                    raise ValueError("reclassify requires 'node_id'")
                unknowns_map.reclassify(
                    map_path,
                    input_data["node_id"],
                    quadrant=input_data.get("quadrant"),
                    status=input_data.get("status"),
                    severity=input_data.get("severity"),
                    technique=input_data.get("technique", ""),
                )
                return (
                    f"reclassified {input_data['node_id']}\n"
                    + unknowns_map.render_ascii(map_path)
                )
            if op == "prune":
                removed = unknowns_map.prune_placeholders(map_path)
                return f"pruned {removed} placeholder line(s)"
            raise ValueError(f"unknown operation: {op}")

        try:
            output = await asyncio.to_thread(_run)
            return ToolResult(success=True, output=output)
        except (FileExistsError, FileNotFoundError, KeyError, ValueError) as exc:
            return ToolResult(success=False, output=f"error: {exc}")


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mount the unknowns_map tool into the coordinator."""
    tool = UnknownsMapTool()
    await coordinator.mount("tools", tool, name=tool.name)
    logger.info("tool-unknowns mounted: registered 'unknowns_map'")
    return {
        "name": "tool-unknowns",
        "version": "0.1.0",
        "provides": ["unknowns_map"],
    }
