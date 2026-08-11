"""Cruzl Labs — User Modeling (Fase 3b).

Profil user yang berkembang dari poin-poin memory.
Profile = ringkasan terkini per user (preferences, style, facts).

File: storage/profiles.json
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class UserProfile:
    def __init__(self, storage_dir: str = "storage"):
        self.path = Path(storage_dir) / "profiles.json"
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

    def get_or_create(self, user_id: str) -> Dict[str, Any]:
        data = self._read()
        if user_id not in data:
            data[user_id] = {
                "user_id": user_id,
                "preferences": [],
                "style": "",
                "facts": [],
                "goals": [],
                "first_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            self._write(data)
        return data[user_id]

    def update_from_points(self, user_id: str, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update profil dari poin hasil extraction.

        - type=profile → masuk preferences
        - type=fact → masuk facts (dedup via text)
        - type=reflection → skip (bukan profil)
        """
        profile = self.get_or_create(user_id)
        for p in points:
            ptype = p.get("type", "fact")
            text = p.get("text", "").strip()
            if not text:
                continue
            if ptype == "profile":
                if text not in profile["preferences"]:
                    profile["preferences"].append(text)
            elif ptype == "fact":
                if text not in profile["facts"]:
                    profile["facts"].append(text)
        profile["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        data = self._read()
        data[user_id] = profile
        self._write(data)
        return profile

    def summary(self, user_id: str) -> str:
        """Ringkasan teks profil — siap di-inject ke prompt agent."""
        p = self.get_or_create(user_id)
        parts = []
        if p["preferences"]:
            parts.append("Preferences: " + "; ".join(p["preferences"]))
        if p["facts"]:
            parts.append("Facts: " + "; ".join(p["facts"]))
        if p["style"]:
            parts.append(f"Style: {p['style']}")
        return "\n".join(parts) if parts else "(profil masih kosong)"
