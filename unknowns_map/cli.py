"""`unknowns` -- thin CLI over unknowns_map (leverage level L4).

Every subcommand delegates to the lib; no logic lives here. The `triage`
subcommand prints the routing token as the LAST line of stdout, matching the
contract of the pipeline's parallelogram guard
(condition="context.tool.last_line=...").
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__, engine_runner, map_ops


def _add_map_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--map",
        dest="map_path",
        default=str(map_ops.DEFAULT_MAP),
        help="path to the unknowns map (default: .ai/unknowns-map.dot)",
    )


def _cmd_seed(args: argparse.Namespace) -> int:
    path = map_ops.seed_map(args.map_path, task=args.task, force=args.force)
    print(f"seeded {path}")
    print(map_ops.render_ascii(path))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    print(map_ops.render_ascii(args.map_path))
    return 0


def _cmd_triage(args: argparse.Namespace) -> int:
    # Routing token MUST be the last line of stdout (pipeline guard contract).
    print(map_ops.dominant_quadrant(args.map_path))
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    node_id = map_ops.add_unknown(
        args.map_path, args.quadrant, args.text,
        status=args.status, severity=args.severity,
    )
    print(f"added {node_id} [{args.quadrant}] {args.text}")
    return 0


def _cmd_reclassify(args: argparse.Namespace) -> int:
    map_ops.reclassify(
        args.map_path, args.node_id,
        quadrant=args.quadrant, status=args.status,
        severity=args.severity, technique=args.technique or "",
    )
    print(f"reclassified {args.node_id}")
    print(map_ops.render_ascii(args.map_path))
    return 0


def _cmd_prune(args: argparse.Namespace) -> int:
    removed = map_ops.prune_placeholders(args.map_path)
    print(f"pruned {removed} placeholder line(s)")
    return 0


def _cmd_png(args: argparse.Namespace) -> int:
    if shutil.which("dot") is None:
        print("graphviz `dot` not found on PATH -- install graphviz", file=sys.stderr)
        return 1
    out = args.out or str(Path(args.map_path).with_suffix(".png"))
    subprocess.run(["dot", "-Tpng", args.map_path, "-o", out], check=True)
    print(f"rendered {out}")
    return 0


def _cmd_pipeline(args: argparse.Namespace) -> int:
    dot = engine_runner.load_pipeline(args.goal)
    if args.out:
        Path(args.out).write_text(dot)
        print(f"wrote {args.out}")
    else:
        print(dot)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    result = asyncio.run(engine_runner.run_lifecycle(args.goal, cwd=args.cwd))
    print(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="unknowns",
        description="Deterministic operations on the unknowns map "
        "(.ai/unknowns-map.dot) plus the lifecycle pipeline seam.",
    )
    parser.add_argument("--version", action="version", version=f"unknowns {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("seed", help="seed a fresh map from the template")
    p.add_argument("task", help="one-line description of the task")
    p.add_argument("--force", action="store_true", help="overwrite an existing map")
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_seed)

    p = sub.add_parser("status", help="render the terminal 2x2 view of the map")
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_status)

    p = sub.add_parser("triage", help="print routing token: uu | uk | ku | clear")
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_triage)

    p = sub.add_parser("add", help="add an unknown to a quadrant")
    p.add_argument("quadrant", choices=list(map_ops.QUADRANTS))
    p.add_argument("text", help="short description of the unknown")
    p.add_argument("--status", default="open", choices=["given", "open", "resolved"])
    p.add_argument("--severity", default=None, choices=["low", "med", "high"])
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_add)

    p = sub.add_parser("reclassify", help="move/resolve a node (never deletes)")
    p.add_argument("node_id")
    p.add_argument("--quadrant", default=None, choices=list(map_ops.QUADRANTS))
    p.add_argument("--status", default=None, choices=["given", "open", "resolved"])
    p.add_argument("--severity", default=None, choices=["low", "med", "high"])
    p.add_argument("--technique", default=None,
                   help="what moved it (blindspot pass, interview, prototype, quiz)")
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_reclassify)

    p = sub.add_parser("prune", help="remove template placeholder nodes/edges")
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_prune)

    p = sub.add_parser("png", help="render the map to PNG via graphviz")
    p.add_argument("--out", default=None)
    _add_map_arg(p)
    p.set_defaults(fn=_cmd_png)

    p = sub.add_parser("pipeline", help="print the lifecycle DOT with $goal filled")
    p.add_argument("goal")
    p.add_argument("--out", default=None, help="write to file instead of stdout")
    p.set_defaults(fn=_cmd_pipeline)

    p = sub.add_parser("run", help="run the lifecycle via the attractor engine "
                                   "(requires the [engine] extra + Amplifier install)")
    p.add_argument("goal")
    p.add_argument("--cwd", default=None)
    p.set_defaults(fn=_cmd_run)

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except (FileExistsError, FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
