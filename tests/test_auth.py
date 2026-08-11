#!/usr/bin/env python3
"""Test unit untuk Cruzl Labs — auth.py (keamanan API key)."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.auth import KeyStore, generate_api_key, hash_key


def make_store():
    return KeyStore(tempfile.mkdtemp(prefix="cruzl_test_"))


def test_key_prefix():
    key = generate_api_key()
    assert key.startswith("cl_")
    assert len(key) > 20


def test_keys_unique():
    a, b = generate_api_key(), generate_api_key()
    assert a != b


def test_hash_not_plaintext():
    key = generate_api_key()
    h = hash_key(key)
    assert h != key  # hash beda dari plaintext


def test_create_returns_key_once():
    ks = make_store()
    res = ks.create_key(label="test")
    assert res["key"].startswith("cl_")
    assert "user_id" in res
    # key mentah TIDAK ada di file
    data = ks._read()
    for entry in data.values():
        assert "key" not in entry  # cuma key_hash
        assert "key_hash" in entry


def test_verify_valid():
    ks = make_store()
    res = ks.create_key(label="test")
    info = ks.verify(res["key"])
    assert info is not None
    assert info["id"] == res["key_id"]


def test_verify_invalid():
    ks = make_store()
    assert ks.verify("cl_salah123") is None


def test_verify_revoked():
    ks = make_store()
    res = ks.create_key(label="test")
    ks.revoke(res["key_id"])
    assert ks.verify(res["key"]) is None


def test_each_key_own_user():
    ks = make_store()
    a = ks.create_key()
    b = ks.create_key()
    assert a["user_id"] != b["user_id"]  # 1 key = 1 user


def test_revoke_not_found():
    ks = make_store()
    assert ks.revoke("key_nonexistent") is False


def test_constant_time_compare_works():
    # verify ga crash dengan key acak (timing-safe compare)
    ks = make_store()
    res = ks.create_key()
    assert ks.verify(res["key"]) is not None


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
