#!/usr/bin/env python3
"""Test unit untuk Cruzl Labs — graph.py, profile.py, raw_store.py."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph import KnowledgeGraph
from src.profile import UserProfile
from src.raw_store import RawStore


def make_dir():
    return tempfile.mkdtemp(prefix="cruzl_test_")


# ---- Graph ----
def test_graph_add_entity():
    g = KnowledgeGraph(make_dir())
    g.add_entity("u_a", "user")
    assert g.get_entity("u_a")["label"] == "user"


def test_graph_add_edge_and_query():
    g = KnowledgeGraph(make_dir())
    g.add_edge("u_a", "horror", "likes")
    g.add_edge("u_a", "western", "likes")
    assert g.query("u_a", "likes") == ["horror", "western"]


def test_graph_weight_increases():
    g = KnowledgeGraph(make_dir())
    g.add_edge("u_a", "horror", "likes", weight=2.0)
    g.add_edge("u_a", "horror", "likes", weight=1.0)
    n = g.neighbors("u_a")
    assert n[0]["weight"] == 3.0


def test_graph_user_scoped_text():
    g = KnowledgeGraph(make_dir())
    g.add_edge("u_a", "horror", "likes")
    g.add_edge("u_b", "crypto", "likes")
    text_a = g.to_text(user_id="u_a")
    assert "horror" in text_a and "crypto" not in text_a


# ---- Profile ----
def test_profile_create():
    p = UserProfile(make_dir())
    prof = p.get_or_create("u_x")
    assert prof["preferences"] == []


def test_profile_update_from_points():
    p = UserProfile(make_dir())
    points = [
        {"type": "profile", "text": "suka jawaban singkat"},
        {"type": "fact", "text": "farming airdrop"},
        {"type": "reflection", "text": "jangan audit pas 503"},  # skip
    ]
    prof = p.update_from_points("u_x", points)
    assert "suka jawaban singkat" in prof["preferences"]
    assert "farming airdrop" in prof["facts"]
    assert "jangan audit pas 503" not in prof["facts"]  # reflection ga masuk facts


def test_profile_no_duplicate():
    p = UserProfile(make_dir())
    p.update_from_points("u_x", [{"type": "profile", "text": "suka X"}])
    p.update_from_points("u_x", [{"type": "profile", "text": "suka X"}])
    prof = p.get_or_create("u_x")
    assert prof["preferences"].count("suka X") == 1


# ---- RawStore ----
def test_raw_add_and_read():
    r = RawStore(make_dir())
    e = r.add("User: halo\nAgent: hai", user_id="u_a")
    assert e["id"].startswith("raw_")
    entries = r.for_user("u_a")
    assert len(entries) == 1


def test_raw_isolation():
    r = RawStore(make_dir())
    r.add("data A", user_id="u_a")
    r.add("data B", user_id="u_b")
    assert len(r.for_user("u_a")) == 1
    assert len(r.for_user("u_b")) == 1


def test_raw_stats():
    r = RawStore(make_dir())
    r.add("satu", user_id="u_a")
    r.add("dua", user_id="u_a")
    assert r.stats()["entries"] == 2


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} lulus")
