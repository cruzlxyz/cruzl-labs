"""Cruzl Labs — API Server (Fase 2c).

FastAPI + Bearer auth. Model isolasi: 1 API key = 1 user.
Semua endpoint butuh header: Authorization: Bearer cl_xxxxx

Run: python3 api.py  (port 8131 default)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from src.auth import KeyStore
from src.config import api_host, api_key_file, api_port, banner, storage_dir
from src.extract import PointExtractor
from src.graph import KnowledgeGraph
from src.profile import UserProfile
from src.raw_store import RawStore
from src.storage import MemoryStore

app = FastAPI(
    title="Cruzl Labs API",
    description="AI-native memory layer untuk agent — 1 key = 1 user.",
    version="0.4.0",
)

_store = MemoryStore(storage_dir())
_keys = KeyStore(storage_dir())
_extractor = PointExtractor()
_profiles = UserProfile(storage_dir())
_graph = KnowledgeGraph(storage_dir())
_raw = RawStore(storage_dir())


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class MemoryCreate(BaseModel):
    text: str
    type: str = "fact"
    confidence: float = 0.8
    scope: str = "user"
    tags: List[str] = []
    source: str = "api"


class MemoryOut(BaseModel):
    id: str
    type: str
    text: str
    confidence: float
    scope: str
    tags: List[str]
    created_at: str
    updated_at: str


# ----------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------

def _require_user(authorization: Optional[str]) -> Dict[str, Any]:
    """Ekstrak & verifikasi Bearer key → return key info (dengan user_id)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    key = authorization[7:].strip()
    info = _keys.verify(key)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    return info


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------

@app.get("/")
def root():
    return {"service": "cruzl-labs", "version": "0.2.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/memories", response_model=MemoryOut, status_code=201)
def create_memory(
    body: MemoryCreate,
    authorization: Optional[str] = Header(None),
):
    """Tambah memory (dedup otomatis). Isolasi per user."""
    key_info = _require_user(authorization)
    entry = _store.add(
        body.text,
        source=body.source,
        scope=body.scope,
        tags=body.tags,
        mem_type=body.type,
        confidence=body.confidence,
        user_id=key_info["user_id"],
    )
    return MemoryOut(
        id=entry["id"],
        type=entry.get("type", "fact"),
        text=entry["text"],
        confidence=entry.get("confidence", 0.8),
        scope=entry.get("scope", "user"),
        tags=entry.get("tags", []),
        created_at=entry["created_at"],
        updated_at=entry["updated_at"],
    )


@app.get("/memories")
def list_memories(
    authorization: Optional[str] = Header(None),
    scope: Optional[str] = Query(None),
):
    """List memory milik user ini (hanya punyanya sendiri)."""
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    memories = [m for m in _store.all() if m.get("user_id", "default") == uid]
    if scope:
        memories = [m for m in memories if m.get("scope") == scope]
    return {"user_id": uid, "count": len(memories), "memories": memories}


@app.get("/memories/search")
def search_memories(
    q: str = Query(..., description="Query pencarian"),
    authorization: Optional[str] = Header(None),
):
    """Search memory milik user ini aja (ga bisa liat user lain)."""
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    results = [
        m
        for m in _store.search(q)
        if m.get("user_id", "default") == uid
    ]
    return {"user_id": uid, "query": q, "count": len(results), "results": results}


@app.delete("/memories/{mem_id}")
def delete_memory(
    mem_id: str,
    authorization: Optional[str] = Header(None),
):
    """Hapus memory (hanya milik user ini)."""
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    memories = _store.all()
    target = [m for m in memories if m.get("id") == mem_id and m.get("user_id", "default") == uid]
    if not target:
        raise HTTPException(status_code=404, detail="Memory not found (or not yours)")
    _store.delete(mem_id)
    return {"deleted": mem_id}


@app.get("/stats")
def stats(authorization: Optional[str] = Header(None)):
    """Statistik memory user ini."""
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    memories = [m for m in _store.all() if m.get("user_id", "default") == uid]
    by_type: Dict[str, int] = {}
    for m in memories:
        t = m.get("type", "fact")
        by_type[t] = by_type.get(t, 0) + 1
    return {"user_id": uid, "total": len(memories), "by_type": by_type}


# ----------------------------------------------------------------------
# Fase 3 — Chat-driven memory
# ----------------------------------------------------------------------

class ChatMessage(BaseModel):
    message: str
    agent_reply: str = ""
    auto_extract: bool = True


@app.post("/chat")
def chat(
    body: ChatMessage,
    authorization: Optional[str] = Header(None),
):
    """Terima percakapan → ekstrak poin penting → update memory+profile+graph.

    LLM extraction via CRUZL_LLM_PROVIDER (ollama default, openai opsional).
    Kalau LLM ga available → fallback: simpan pesan user sebagai fact.
    """
    key_info = _require_user(authorization)
    uid = key_info["user_id"]

    conversation = f"User: {body.message}"
    if body.agent_reply:
        conversation += f"\nAgent: {body.agent_reply}"

    # 1. Selalu simpan RAW (mentah, permanen — ga pernah dihapus)
    raw_entry = _raw.add(conversation, user_id=uid, source="chat")

    memory_saved = []
    if body.auto_extract:
        points = _extractor.extract(conversation)
        if not points:
            # fallback: simpan pesan user sebagai fact
            points = [{"type": "fact", "text": body.message, "confidence": 0.5}]
        for pt in points:
            entry = _store.add(
                pt.get("text", ""),
                source="chat",
                mem_type=pt.get("type", "fact"),
                confidence=pt.get("confidence", 0.6),
                user_id=uid,
                tags=pt.get("tags", []),
            )
            memory_saved.append({
                "id": entry["id"],
                "type": entry.get("type"),
                "text": entry["text"],
                "deduped": entry.get("_deduped", False),
            })
            # graph: user -> likes -> tag (kalau ada)
            for tag in pt.get("tags", []):
                _graph.add_edge(uid, tag, "about")
        _profiles.update_from_points(uid, points)
    else:
        entry = _store.add(
            body.message, source="chat", mem_type="fact", user_id=uid
        )
        memory_saved.append({"id": entry["id"], "type": "fact", "text": entry["text"]})

    return {
        "user_id": uid,
        "raw_id": raw_entry["id"],
        "memory_saved": memory_saved,
        "profile": _profiles.summary(uid),
        "graph": _graph.neighbors(uid),
    }


@app.get("/raw")
def get_raw(
    authorization: Optional[str] = Header(None),
    days: int = Query(7, ge=1, le=365),
):
    """Lihat raw memory (mentah) user ini — N hari terakhir.

    Raw = detail verbatim, permanen. Dipake kalau butuh konteks penuh.
    """
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    entries = _raw.for_user(uid, days=days)
    return {
        "user_id": uid,
        "days": days,
        "count": len(entries),
        "raw": entries[-50:],  # batasi 50 terakhir biar ga overload
    }


@app.get("/profile")
def get_profile(authorization: Optional[str] = Header(None)):
    """Lihat profil user (dari memory yang terkumpul)."""
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    return {
        "user_id": uid,
        "profile": _profiles.get_or_create(uid),
        "summary": _profiles.summary(uid),
    }


@app.get("/graph")
def get_graph(authorization: Optional[str] = Header(None)):
    """Lihat knowledge graph user ini."""
    key_info = _require_user(authorization)
    uid = key_info["user_id"]
    return {
        "user_id": uid,
        "neighbors": _graph.neighbors(uid),
        "text": _graph.to_text(user_id=uid),
    }


@app.get("/context")
def get_context(authorization: Optional[str] = Header(None)):
    """Konteks lengkap user — siap di-inject ke system prompt agent mana pun.

    Endpoint universal: dipanggil agent di AWAL session biar
    "kenal" user-nya lagi walau pindah session / restart.
    """
    key_info = _require_user(authorization)
    uid = key_info["user_id"]

    # facts + profile dari memory user ini
    memories = [m for m in _store.all() if m.get("user_id", "default") == uid]
    facts = [m["text"] for m in memories if m.get("type") == "fact"]
    reflections = [m["text"] for m in memories if m.get("type") == "reflection"]

    profile = _profiles.get_or_create(uid)
    graph_text = _graph.to_text(user_id=uid)

    # blok teks siap-pakai (kompak, hemat token)
    blocks = []
    pref = profile.get("preferences", [])
    if pref:
        blocks.append(f"PREFERENCES: {'; '.join(pref)}")
    if facts:
        blocks.append(f"KNOWN FACTS: {'; '.join(facts[:20])}")
    if reflections:
        blocks.append(f"LESSONS: {'; '.join(reflections[:10])}")
    if graph_text and "(graph kosong)" not in graph_text:
        blocks.append(f"RELATIONS:\n{graph_text}")

    context_text = "\n".join(blocks) if blocks else "(belum ada memory untuk user ini)"

    return {
        "user_id": uid,
        "context": context_text,      # ← inject ini ke system prompt
        "profile": profile,
        "facts": facts,
        "reflections": reflections,
        "graph": graph_text,
        "usage": {"inject_hint": "Masukkan 'context' ke system prompt agent."},
    }


if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else api_port()
    host = api_host()
    print(banner())
    print(f"🚀 Cruzl Labs API di http://{host}:{port} (docs: /docs)")
    uvicorn.run(app, host=host, port=port)
