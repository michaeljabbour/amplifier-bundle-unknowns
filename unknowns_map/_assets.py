"""Asset resolution for the unknowns lib -- dev tree vs installed wheel.

Dev tree (this repo checked out):
    <repo>/pipelines/unknowns-lifecycle.dot
    <repo>/context/map-template.dot
    <repo>/scripts/dominant_quadrant.sh

Installed wheel (hatch force-include, see pyproject.toml):
    site-packages/unknowns_map_assets/pipelines/unknowns-lifecycle.dot
    site-packages/unknowns_map_assets/map-template.dot
    site-packages/unknowns_map_assets/scripts/dominant_quadrant.sh
"""

from __future__ import annotations

from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent


def _dev_root() -> Path | None:
    root = _PKG_DIR.parent
    if (root / "pipelines" / "unknowns-lifecycle.dot").exists():
        return root
    return None


def _wheel_assets() -> Path | None:
    assets = _PKG_DIR.parent / "unknowns_map_assets"
    if assets.exists():
        return assets
    return None


def pipeline_dot() -> Path:
    """Path to pipelines/unknowns-lifecycle.dot for the active layout."""
    dev = _dev_root()
    if dev is not None:
        return dev / "pipelines" / "unknowns-lifecycle.dot"
    wheel = _wheel_assets()
    if wheel is not None:
        return wheel / "pipelines" / "unknowns-lifecycle.dot"
    raise FileNotFoundError(
        "unknowns-lifecycle.dot not found in dev tree or installed assets"
    )


def map_template() -> Path:
    """Path to the unknowns-map DOT template."""
    dev = _dev_root()
    if dev is not None:
        return dev / "context" / "map-template.dot"
    wheel = _wheel_assets()
    if wheel is not None:
        return wheel / "map-template.dot"
    raise FileNotFoundError(
        "map-template.dot not found in dev tree or installed assets"
    )


def triage_script() -> Path:
    """Path to the zero-dependency shell mirror of the triage guard."""
    dev = _dev_root()
    if dev is not None:
        return dev / "scripts" / "dominant_quadrant.sh"
    wheel = _wheel_assets()
    if wheel is not None:
        return wheel / "scripts" / "dominant_quadrant.sh"
    raise FileNotFoundError(
        "dominant_quadrant.sh not found in dev tree or installed assets"
    )
