"""Deterministic core tests: seed -> add -> counts -> triage -> mutate -> render."""

from pathlib import Path

import pytest

from unknowns_map import map_ops


@pytest.fixture
def seeded(tmp_path: Path) -> Path:
    m = tmp_path / ".ai" / "unknowns-map.dot"
    map_ops.seed_map(m, task="test the map")
    return m


def test_seed_creates_map_with_task(seeded: Path):
    content = seeded.read_text()
    assert "test the map" in content
    assert "cluster_uu" in content


def test_seed_refuses_overwrite(seeded: Path):
    with pytest.raises(FileExistsError):
        map_ops.seed_map(seeded, task="again")
    map_ops.seed_map(seeded, task="again", force=True)  # force works


def test_add_and_counts(seeded: Path):
    map_ops.prune_placeholders(seeded)
    map_ops.add_unknown(seeded, "kk", "user wants X", status="given")
    map_ops.add_unknown(seeded, "ku", "which session store?", severity="med")
    map_ops.add_unknown(seeded, "ku", "token refresh strategy", severity="high")
    map_ops.add_unknown(seeded, "uu", "legacy SAML users exist")
    c = map_ops.quadrant_counts(map_ops.parse_map(seeded))
    assert c["kk"]["total"] == 1 and c["kk"]["open"] == 0
    assert c["ku"]["open"] == 2
    assert c["uu"]["open"] == 1


def test_triage_precedence(tmp_path: Path):
    m = tmp_path / "map.dot"
    map_ops.seed_map(m, task="t")
    map_ops.prune_placeholders(m)
    assert map_ops.dominant_quadrant(m) == "clear"
    # ku only -> ku
    map_ops.add_unknown(m, "ku", "q1")
    assert map_ops.dominant_quadrant(m) == "ku"
    # uk ties ku -> uk wins (uk >= ku)
    map_ops.add_unknown(m, "uk", "pref1")
    assert map_ops.dominant_quadrant(m) == "uk"
    # uu ties both -> uu wins
    map_ops.add_unknown(m, "uu", "surprise")
    assert map_ops.dominant_quadrant(m) == "uu"
    # resolve uu; uk still >= ku -> uk
    map_ops.reclassify(m, "uu_1", status="resolved", technique="blindspot pass")
    assert map_ops.dominant_quadrant(m) == "uk"
    # high-severity uu beats larger counts elsewhere
    map_ops.add_unknown(m, "ku", "q2")
    map_ops.add_unknown(m, "ku", "q3")
    map_ops.add_unknown(m, "uu", "clock skew", severity="high")
    assert map_ops.dominant_quadrant(m) == "uu"


def test_missing_map_is_clear(tmp_path: Path):
    assert map_ops.dominant_quadrant(tmp_path / "nope.dot") == "clear"


def test_reclassify_moves_quadrant(seeded: Path):
    map_ops.prune_placeholders(seeded)
    nid = map_ops.add_unknown(seeded, "uu", "found it")
    map_ops.reclassify(seeded, nid, quadrant="ku", technique="blindspot pass")
    nodes = {n.node_id: n for n in map_ops.parse_map(seeded)}
    assert nodes[nid].quadrant == "ku"
    assert "reclassified via blindspot pass" in seeded.read_text()


def test_reclassify_unknown_node_raises(seeded: Path):
    with pytest.raises(KeyError):
        map_ops.reclassify(seeded, "nope_1", status="resolved")


def test_prune_placeholders(seeded: Path):
    removed = map_ops.prune_placeholders(seeded)
    assert removed >= 4  # 4 placeholder nodes + 2 example edges
    # No placeholder NODES remain (template comments may still say "placeholder")
    assert map_ops.parse_map(seeded) == []
    assert "_placeholder [" not in seeded.read_text()
    assert "->" not in seeded.read_text()  # example edges gone too


def test_render_ascii_smoke(seeded: Path):
    map_ops.prune_placeholders(seeded)
    map_ops.add_unknown(seeded, "ku", "token refresh strategy", severity="high")
    out = map_ops.render_ascii(seeded)
    assert "KNOWN KNOWNS" in out and "UNKNOWN UNKNOWNS" in out
    assert "! token refresh strategy" in out
    assert "1 open / 1 total unknowns" in out
    assert max(len(line) for line in out.splitlines()) <= 78


def test_render_ascii_missing_map(tmp_path: Path):
    assert "no unknowns map" in map_ops.render_ascii(tmp_path / "nope.dot")
