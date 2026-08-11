"""Cruzl Labs — Knowledge Graph (Fase 3c).

Graph ringan berbasis JSON (bukan Neo4j!) — konsisten dengan filosofi
"semua kekuatan tanpa beratnya". Query sederhana: entitas + relasi.

Format:
{
  "entities": {"u_alpha": {"label": "user", "props": {}}, "horror": {"label": "genre"}},
  "edges": [{"from": "u_alpha", "to": "horror", "rel": "likes", "weight": 1}]
}
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class KnowledgeGraph:
    def __init__(self, storage_dir: str = "storage"):
        self.path = Path(storage_dir) / "relations.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _ensure(self) -> None:
        if not self.path.exists():
            self._write({"entities": {}, "edges": []})

    def _read(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"entities": {}, "edges": []}

    def _write(self, data: Dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------

    def add_entity(self, entity_id: str, label: str = "", props: Optional[Dict] = None) -> None:
        """Tambah entitas (idempotent)."""
        data = self._read()
        if entity_id not in data["entities"]:
            data["entities"][entity_id] = {"label": label, "props": props or {}}
            self._write(data)

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        return self._read()["entities"].get(entity_id)

    # ------------------------------------------------------------------
    # Edges (relasi)
    # ------------------------------------------------------------------

    def add_edge(self, from_id: str, to_id: str, rel: str, weight: float = 1.0) -> None:
        """Tambah/update relasi. Kalau udah ada → naikin weight (recency)."""
        data = self._read()
        self.add_entity(from_id)
        self.add_entity(to_id)
        # cari edge yang sama
        for e in data["edges"]:
            if e["from"] == from_id and e["to"] == to_id and e["rel"] == rel:
                e["weight"] = e.get("weight", 1.0) + weight
                e["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._write(data)
                return
        data["edges"].append({
            "from": from_id,
            "to": to_id,
            "rel": rel,
            "weight": weight,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self._write(data)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def neighbors(self, entity_id: str, rel: Optional[str] = None) -> List[Dict]:
        """Entitas yang terhubung ke entity_id (in + out)."""
        data = self._read()
        out = []
        for e in data["edges"]:
            if e["from"] == entity_id and (rel is None or e["rel"] == rel):
                out.append({"entity": e["to"], "rel": e["rel"], "direction": "out", "weight": e["weight"]})
            elif e["to"] == entity_id and (rel is None or e["rel"] == rel):
                out.append({"entity": e["from"], "rel": e["rel"], "direction": "in", "weight": e["weight"]})
        # sort by weight desc
        out.sort(key=lambda x: -x["weight"])
        return out

    def query(self, entity_id: str, rel: str) -> List[str]:
        """Simple query: entitas X yang rel-nya 'likes' dari entity_id."""
        return [n["entity"] for n in self.neighbors(entity_id, rel) if n["direction"] == "out"]

    def stats(self) -> Dict[str, Any]:
        data = self._read()
        return {"entities": len(data["entities"]), "edges": len(data["edges"])}

    def to_text(self, user_id: Optional[str] = None) -> str:
        """Representasi teks buat prompt agent (compact).

        Kalau user_id dikasih → cuma edges yang terhubung ke user itu.
        """
        data = self._read()
        lines = []
        for e in data["edges"]:
            if user_id and e["from"] != user_id:
                continue
            lines.append(f"{e['from']} -[{e['rel']}]-> {e['to']}")
        return "\n".join(lines) if lines else "(graph kosong)"
