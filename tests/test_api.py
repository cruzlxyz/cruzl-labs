#!/usr/bin/env python3
"""Test integrasi API Cruzl Labs — jalankan server dulu, atau pakai TestClient.

Test ini butuh API server jalan di 127.0.0.1:8131 ATAU langsung ke app.
Pakai FastAPI TestClient (tanpa server terpisah).
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set storage ke temp biar ga ganggu data asli
os.environ["CRUZL_STORAGE_DIR"] = tempfile.mkdtemp(prefix="cruzl_api_test_")

from fastapi.testclient import TestClient  # noqa: E402
from src.auth import KeyStore  # noqa: E402
from src.config import storage_dir  # noqa: E402
from api import app  # noqa: E402

client = TestClient(app)


def get_valid_key():
    ks = KeyStore(storage_dir())
    return ks.create_key(label="test")["key"]


def auth_hdr(key):
    return {"Authorization": f"Bearer {key}"}


# ---- Auth ----
def test_no_auth_401():
    assert client.get("/memories").status_code == 401


def test_bad_key_401():
    assert client.get("/memories", headers=auth_hdr("cl_wrong")).status_code == 401


def test_health():
    assert client.get("/health").json()["ok"] is True


# ---- CRUD ----
def test_create_memory():
    key = get_valid_key()
    r = client.post("/memories", headers=auth_hdr(key), json={"text": "test memory", "type": "fact"})
    assert r.status_code == 201
    assert r.json()["text"] == "test memory"


def test_list_memories():
    key = get_valid_key()
    client.post("/memories", headers=auth_hdr(key), json={"text": "list test"})
    r = client.get("/memories", headers=auth_hdr(key))
    assert r.status_code == 200
    assert r.json()["count"] >= 1


# ---- Isolasi ----
def test_isolation_between_users():
    k1 = get_valid_key()
    k2 = get_valid_key()
    client.post("/memories", headers=auth_hdr(k1), json={"text": "rahasia user1"})
    # user2 ga boleh liat
    r2 = client.get("/memories/search?q=rahasia", headers=auth_hdr(k2))
    assert r2.json()["count"] == 0
    # user1 bisa
    r1 = client.get("/memories/search?q=rahasia", headers=auth_hdr(k1))
    assert r1.json()["count"] >= 1


# ---- Delete ----
def test_delete_own_memory():
    key = get_valid_key()
    r = client.post("/memories", headers=auth_hdr(key), json={"text": "to delete"})
    mid = r.json()["id"]
    assert client.delete(f"/memories/{mid}", headers=auth_hdr(key)).status_code == 200


def test_cannot_delete_other_user():
    k1 = get_valid_key()
    k2 = get_valid_key()
    r = client.post("/memories", headers=auth_hdr(k1), json={"text": "milik user1"})
    mid = r.json()["id"]
    # user2 ga boleh delete memory user1
    assert client.delete(f"/memories/{mid}", headers=auth_hdr(k2)).status_code == 404


# ---- Chat ----
def test_chat_auto_extract_fallback():
    key = get_valid_key()
    r = client.post("/chat", headers=auth_hdr(key), json={"message": "halo ini pesan", "auto_extract": False})
    assert r.status_code == 200
    assert "raw_id" in r.json()


# ---- Tags ----
def test_tags_endpoint():
    key = get_valid_key()
    client.post("/memories", headers=auth_hdr(key), json={"text": "bertag", "tags": ["crypto"]})
    r = client.get("/memories/tags", headers=auth_hdr(key))
    assert "crypto" in r.json()["tags"]


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
