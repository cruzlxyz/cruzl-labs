"""Memory Bridge — API key generation & verification.

Keamanan:
- Key mentah cuma dikasih SEKALI ke user (ga bisa diliat lagi)
- Server cuma nyimpen HASH key (sha256), bukan key mentah
- Kalau DB bocor → key ga bisa dipake attacker
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from src.storage import FileLock

# Prefix biar key-nya kelihatan "branded" kayak sk-...
KEY_PREFIX = "cl_"  # Cruzl Labs


def generate_api_key() -> str:
    """Generate API key acak yang aman (32 byte crypto-random)."""
    raw = secrets.token_urlsafe(32)  # 43 karakter, crypto-secure
    return f"{KEY_PREFIX}{raw}"


def hash_key(key: str) -> str:
    """Hash key dengan sha256 (dipakai untuk simpan & verify)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class KeyStore:
    """Penyimpanan API key (hash-only) dalam JSON."""

    def __init__(self, storage_dir: str = "storage"):
        self.path = Path(storage_dir) / "api_keys.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _ensure(self) -> None:
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_key(self, *, label: str = "", scope: str = "user", user_id: str = "") -> Dict[str, str]:
        """Buat key baru. Return key mentah SEKALI (setelah ini ga bisa diliat).

        Model isolasi: 1 API key = 1 user. Setiap key otomatis dapet
        user_id sendiri (kalau ga dikasih), jadi memory tiap user
        terisolasi — ga ada sharing antar key.
        """
        key = generate_api_key()
        key_id = f"key_{uuid.uuid4().hex[:8]}"
        uid = user_id or f"u_{uuid.uuid4().hex[:8]}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with FileLock(self.path):
            data = self._read()
            data[key_id] = {
                "id": key_id,
                "label": label,
                "scope": scope,
                "user_id": uid,  # ← 1 key = 1 user
                "key_hash": hash_key(key),  # ← cuma hash yang disimpan
                "created_at": now,
                "last_used": None,
                "revoked": False,
            }
            self._write(data)
        return {
            "key_id": key_id,
            "key": key,
            "user_id": uid,
            "warning": "Simpan key ini! Tidak bisa dilihat lagi.",
        }

    def verify(self, key: str) -> Optional[Dict[str, Any]]:
        """Verifikasi key. Return info key kalau valid, None kalau ga."""
        h = hash_key(key)
        data = self._read()
        for entry in data.values():
            if hmac.compare_digest(entry.get("key_hash", ""), h):  # constant-time compare
                if entry.get("revoked"):
                    return None
                # update last_used
                entry["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._write(data)
                return entry
        return None

    def revoke(self, key_id: str) -> bool:
        """Cabut key (revoke)."""
        data = self._read()
        if key_id in data:
            data[key_id]["revoked"] = True
            self._write(data)
            return True
        return False

    def list_keys(self) -> Dict[str, Any]:
        """List semua key TANPA hash (buat admin)."""
        data = self._read()
        out = {}
        for kid, entry in data.items():
            out[kid] = {k: v for k, v in entry.items() if k != "key_hash"}
        return out
