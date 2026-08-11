#!/usr/bin/env python3
"""Test unit untuk Cruzl Labs — storage.py.

Jalankan: python3 -m pytest tests/ -v
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.storage import MemoryStore


def make_store():
    tmp = tempfile.mkdtemp(prefix="cruzl_test_")
    return MemoryStore(tmp)


def test_add_and_read():
    s = make_store()
    e = s.add("User suka horror", mem_type="fact")
    assert e["type"] == "fact"
    assert s.stats()["total"] == 1


def test_dedup_exact():
    s = make_store()
    e1 = s.add("User pindah ke Bandung")
    e2 = s.add("User pindah ke Bandung")
    assert e1["id"] == e2["id"]  # dedup → id sama
    assert s.stats()["total"] == 1


def test_dedup_similar():
    s = make_store()
    e1 = s.add("User pindah ke Bandung")
    e2 = s.add("User pindah ke Bandung sekarang")
    assert e1["id"] == e2["id"]
    assert s.stats()["total"] == 1


def test_not_duplicate_different_topic():
    s = make_store()
    s.add("User pindah ke Bandung")
    s.add("User pindah ke Surabaya untuk kerja")
    assert s.stats()["total"] == 2


def test_conflict_new_wins():
    s = make_store()
    e1 = s.add("User tinggal di Jakarta", confidence=0.5)
    e2 = s.add("User tinggal di Jakarta", confidence=0.9)
    assert e2["confidence"] == 0.9  # confidence max


def test_user_isolation():
    s = make_store()
    s.add("memory A", user_id="u_a")
    s.add("memory B", user_id="u_b")
    all_m = s.all()
    a = [m for m in all_m if m.get("user_id") == "u_a"]
    b = [m for m in all_m if m.get("user_id") == "u_b"]
    assert len(a) == 1 and len(b) == 1


def test_search_keyword():
    s = make_store()
    s.add("User suka film horror")
    s.add("User farming airdrop")
    results = s.search("horror")
    assert len(results) == 1
    assert "horror" in results[0]["text"]


def test_delete():
    s = make_store()
    e = s.add("temporary")
    assert s.delete(e["id"]) is True
    assert s.stats()["total"] == 0


def test_delete_not_found():
    s = make_store()
    assert s.delete("mem_nonexistent") is False


def test_tags_and_scope():
    s = make_store()
    s.add("crypto", tags=["crypto", "airdrop"], scope="agent")
    m = s.all()[0]
    assert m["tags"] == ["crypto", "airdrop"]
    assert m["scope"] == "agent"


if __name__ == "__main__":
    # manual runner tanpa pytest
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
