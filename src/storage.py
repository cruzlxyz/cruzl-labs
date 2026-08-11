"""Memory Bridge — storage layer (Fase 1).

Append-only JSONL storage + keyword search.
Tanpa dependency eksternal (stdlib only).
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    """JSONL-based memory storage dengan pencarian keyword sederhana."""

    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memories_path = self.storage_dir / "memories.jsonl"
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.memories_path.exists():
            self.memories_path.touch()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        text: str,
        *,
        source: str = "manual",
        scope: str = "user",
        tags: Optional[List[str]] = None,
        mem_type: str = "fact",
        confidence: float = 0.8,
        user_id: str = "default",
    ) -> Dict[str, Any]:
        """Tambah memory dengan dedup & conflict resolution otomatis.

        - Kalau text sama persis (atau mirip banget) → UPDATE yang lama (bukan duplikat)
        - Kalau konflik (text beda, topik sama) → yang BARU menang
        """
        text = text.strip()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # ---- DEDUP: cek apakah text sudah ada (exact match) ----
        memories = self.all()
        for mem in memories:
            if mem.get("user_id", "default") != user_id:
                continue
            if self._is_duplicate(mem.get("text", ""), text):
                # UPDATE entry lama (conflict resolution: yang baru menang)
                mem["text"] = text
                mem["updated_at"] = now
                mem["confidence"] = max(mem.get("confidence", 0), confidence)
                if tags:
                    merged = list(dict.fromkeys(mem.get("tags", []) + tags))
                    mem["tags"] = merged
                self._rewrite(memories)
                mem["_deduped"] = True
                return mem

        # ---- BARU ----
        entry = {
            "id": f"mem_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "type": mem_type,
            "text": text,
            "confidence": max(0.0, min(1.0, confidence)),
            "scope": scope,
            "tags": tags or [],
            "source": source,
            "ttl": None,
            "created_at": now,
            "updated_at": now,
            "entities": [],
            "insights": [],
        }
        with open(self.memories_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    @staticmethod
    def _is_duplicate(a: str, b: str, threshold: float = 0.70) -> bool:
        """Cek kemiripan 2 teks — exact + token overlap (Jaccard sederhana).

        Threshold 0.70: menangkap duplikat dengan 1-2 kata tambahan,
        tanpa salah tangkap teks yang topiknya beda.
        """
        if a.strip().lower() == b.strip().lower():
            return True
        ta = set(re.findall(r"[a-z0-9]+", a.lower()))
        tb = set(re.findall(r"[a-z0-9]+", b.lower()))
        if not ta or not tb:
            return False
        jaccard = len(ta & tb) / len(ta | tb)
        return jaccard >= threshold

    def all(self) -> List[Dict[str, Any]]:
        """Baca semua memory (urutan simpan)."""
        out = []
        with open(self.memories_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out

    def search(self, query: str, *, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """Keyword search sederhana (case-insensitive, token match)."""
        q = query.lower()
        q_tokens = set(re.findall(r"[a-z0-9]+", q))
        results = []
        for mem in self.all():
            if scope and mem.get("scope") != scope:
                continue
            text = mem.get("text", "").lower()
            if q in text:
                results.append(mem)
                continue
            tokens = set(re.findall(r"[a-z0-9]+", text))
            if q_tokens & tokens:  # ada token yang cocok
                results.append(mem)
        return results

    def delete(self, mem_id: str) -> bool:
        """Hapus memory by id (rewrite file tanpa entry itu)."""
        memories = self.all()
        remaining = [m for m in memories if m.get("id") != mem_id]
        if len(remaining) == len(memories):
            return False
        self._rewrite(remaining)
        return True

    def _rewrite(self, memories: List[Dict[str, Any]]) -> None:
        tmp = self.memories_path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for m in memories:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
        tmp.replace(self.memories_path)

    def stats(self) -> Dict[str, Any]:
        memories = self.all()
        scopes: Dict[str, int] = {}
        for m in memories:
            s = m.get("scope", "unknown")
            scopes[s] = scopes.get(s, 0) + 1
        return {
            "total": len(memories),
            "by_scope": scopes,
            "file_size_bytes": self.memories_path.stat().st_size,
        }
