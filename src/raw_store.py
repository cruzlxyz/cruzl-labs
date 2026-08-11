"""Cruzl Labs — Raw Memory Store (memory mentah, append-only, permanen).

RAW = detail verbatim dari percakapan. Ga pernah diubah, ga pernah
dihapus (sesuai keputusan desain: tanpa TTL, simpan selamanya).
Dipisah per-hari biar gampang di-archive & dibaca on-demand.

File: storage/raw/YYYY-MM-DD.jsonl
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.storage import FileLock


class RawStore:
    def __init__(self, storage_dir: str = "storage"):
        self.raw_dir = Path(storage_dir) / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _today_path(self) -> Path:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        return self.raw_dir / f"{today}.jsonl"

    def add(
        self,
        conversation: str,
        *,
        user_id: str = "default",
        source: str = "chat",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Simpan percakapan mentah (append-only, permanen)."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry = {
            "id": f"raw_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "text": conversation,
            "source": source,
            "meta": meta or {},
            "created_at": now,
        }
        path = self._today_path()
        with FileLock(path):
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def for_user(self, user_id: str, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Baca raw memory user (dari N hari terakhir, default semua)."""
        files = sorted(self.raw_dir.glob("*.jsonl"), reverse=True)
        if days:
            files = files[:days]
        out = []
        for path in files:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("user_id", "default") == user_id:
                        out.append(entry)
        return out

    def stats(self) -> Dict[str, Any]:
        total = 0
        files = list(self.raw_dir.glob("*.jsonl"))
        for path in files:
            total += sum(1 for _ in open(path, encoding="utf-8") if _.strip())
        return {"files": len(files), "entries": total}
