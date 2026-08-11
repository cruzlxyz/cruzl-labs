#!/usr/bin/env python3
"""Test — rate limiter + error handling."""

import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["CRUZL_STORAGE_DIR"] = tempfile.mkdtemp(prefix="cruzl_api_test_")

from api import RateLimiter  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from api import app  # noqa: E402

client = TestClient(app)


# ---- RateLimiter ----
def test_rate_limit_blocks_after_limit():
    rl = RateLimiter(limit=2, window=60)
    assert rl.check("k1") is True
    assert rl.check("k1") is True
    assert rl.check("k1") is False  # ke-3 diblokir


def test_rate_limit_per_key_isolation():
    rl = RateLimiter(limit=1, window=60)
    rl.check("kA")
    assert rl.check("kB") is True  # key beda ga kena


def test_rate_limit_resets_after_window():
    import time
    rl = RateLimiter(limit=1, window=1)
    rl.check("kX")
    assert rl.check("kX") is False
    time.sleep(1.1)  # lewat window
    assert rl.check("kX") is True


# ---- Error handling ----
def test_empty_text_422():
    from src.auth import KeyStore
    from src.config import storage_dir
    ks = KeyStore(storage_dir())
    key = ks.create_key()["key"]
    r = client.post("/memories", headers={"Authorization": f"Bearer {key}"}, json={"text": ""})
    assert r.status_code == 422


def test_bad_confidence_422():
    from src.auth import KeyStore
    from src.config import storage_dir
    ks = KeyStore(storage_dir())
    key = ks.create_key()["key"]
    r = client.post("/memories", headers={"Authorization": f"Bearer {key}"}, json={"text": "ok", "confidence": 99})
    assert r.status_code == 422


def test_invalid_type_422():
    from src.auth import KeyStore
    from src.config import storage_dir
    ks = KeyStore(storage_dir())
    key = ks.create_key()["key"]
    r = client.post("/memories", headers={"Authorization": f"Bearer {key}"}, json={"text": "ok", "type": "hacker"})
    assert r.status_code == 422


def test_valid_still_works():
    from src.auth import KeyStore
    from src.config import storage_dir
    ks = KeyStore(storage_dir())
    key = ks.create_key()["key"]
    r = client.post("/memories", headers={"Authorization": f"Bearer {key}"}, json={"text": "memory valid"})
    assert r.status_code == 201


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} lulus")
