# Cruzl Labs — Blueprint v0.2

AI-native memory layer untuk agent — dibangun dari nol, ringan, self-host.
> "Memory = belajar, bukan cuma nyimpen."

## DNA — Pendekatan Desain

```
Cruzl Labs =
  Operasi cerdas (ADD/UPDATE/DELETE/NOOP) + multi-scope
  Entity resolution + retain/recall/reflect      ← PEMBEDA UTAMA
  User modeling + dialectic cold/warm prompt
  Knowledge graph + temporal (versi RINGAN/JSON)
```

**Filosofi: "Semua kekuatan, tanpa beratnya"** — simple JSONL, fitur cerdas yang mumpuni.

## Arsitektur (1 store + type field)

Satu JSONL store, tiap entry punya `type` — bukan 4 file terpisah (efisien, tetap terbedakan).

```
storage/memories.jsonl   ← SATU file
  type: fact | profile | reflection | relation
  confidence: 0.0-1.0
  ttl: expiry (opsional)
  user_id: untuk multi-user isolation
```

## Komponen Lengkap (v0.2 target)

### 1. Storage ✅
- [x] JSONL append-only, 1 store + type
- [x] tag, scope, source
- [ ] `confidence` field
- [ ] `ttl` / expiry
- [ ] `user_id` (multi-user isolation)

### 2. Operations (PRIORITAS 1 — dedup & conflict)
- [x] CRUD dasar
- [ ] **Dedup otomatis** — cek duplikat sebelum add (semantic + exact)
- [ ] **Conflict resolution** — memory baru menang (update, bukan duplikat)
- [ ] **Recency weighting** — yang baru diutamakan saat retrieval

### 3. Search
- [x] Keyword search (0 RAM)
- [ ] Semantic search via API embedding (Ollama/OpenAI — 0 RAM lokal)
- [ ] **Hybrid ranking** — keyword + semantic + recency + confidence

### 4. Auth & Multi-user
- [x] API key (hash-only, crypto-secure, revoke)
- [ ] Per-user isolation (`user_id` di tiap entry, key → user mapping)

### 5. API (FastAPI — "user lain bisa pake")
- [ ] CRUD endpoints (`POST /memories`, `GET /search`, dll)
- [ ] Auth middleware (Bearer key)
- [ ] `/context` endpoint — assembly: pilih + ranking + susun context prompt

### 6. Export
- [ ] Obsidian/Markdown export
- [ ] Backup JSON

## Entry Schema (final)

```json
{
  "id": "mem_abc123",
  "user_id": "user_xxx",          // multi-user
  "type": "fact",                  // fact | profile | reflection | relation
  "text": "User suka horror movies",
  "confidence": 0.9,               // 0.0-1.0
  "scope": "user",                 // user | session | agent
  "tags": ["hobby", "film"],
  "source": "cli" | "api" | "chat",
  "ttl": null,                     // ISO timestamp expiry, null = forever
  "created_at": "2026-08-11T...",
  "updated_at": "2026-08-11T...",
  "embedding": [0.1, 0.2, ...],    // di file terpisah (embeddings.jsonl)
  "entities": [],                  // fase 2
  "insights": []                   // fase 3
}
```

## Retrieval Pipeline (yang bikin jadi "memory system" bukan "search tool")

```
query → 1. keyword search
      → 2. semantic search (API embedding, kalau perlu)
      → 3. ranking: recency × confidence × type-priority
      → 4. filter: expired, revoked, wrong user
      → 5. assemble: pilih top-K → susun context (token budget)
      → 6. inject ke prompt agent
```

## RAM Budget

| Komponen | RAM |
|----------|-----|
| Core (storage + CLI) | ~15-30 MB |
| + API server | ~40-80 MB |
| Embedding | 0 MB (via API) |
| **Total** | **~55-110 MB** — aman di VPS 2GB |

## Roadmap Build (urutan)

- [x] Fase 1: Storage + CLI CRUD + tag/scope
- [x] API key system (hash-only, revoke)
- [x] Fase 2a: Dedup + conflict resolution
- [x] Fase 2b: Multi-user isolation (user_id)
- [x] Fase 2c: API server (FastAPI + auth)
- [ ] **Fase 3a: POINT EXTRACTION** — ambil poin penting dari chat (LLM)
- [ ] **Fase 3b: USER MODELING** — profil user berkembang dari chat
- [ ] **Fase 3c: KNOWLEDGE GRAPH** — entitas + relasi (JSON ringan)
- [ ] **Fase 3d: CHAT ENDPOINT** — user bisa chat sama agent + memory otomatis
- [ ] Fase 4: Semantic search (embedding API) + hybrid ranking
- [ ] Fase 5: Entity resolution lanjutan
- [ ] Fase 6: Export Obsidian + backup

## Fase 3 — Chat-Driven Memory (detail)

### 3a. Point Extraction
```
POST /chat  (isi: pesan user + balasan agent)
  → LLM ekstrak poin penting:
     {"type": "fact", "text": "user suka horror", "confidence": 0.9}
     {"type": "update", "existing": "...", "new": "..."}
  → simpan via storage.add (dedup otomatis!)
```

### 3b. User Modeling
```
Dari poin yang terkumpul → bangun profil:
  {"id": "profile_u_xxx", "user_id": "u_xxx",
   "preferences": [...], "style": "...", "facts": [...],
   "updated_at": "..."}
  Profile = ringkasan terkini — di-refresh tiap chat
```

### 3c. Knowledge Graph (JSON ringan)
```
storage/relations.json:
  {"entities": {"u_alpha": {"label": "user", "props": {}},
                "horror": {"label": "genre", "props": {}}},
   "edges": [{"from": "u_alpha", "to": "horror", "rel": "likes"}]}
  → query: "apa yang user suka?" → ikut edges
```

### 3d. Chat Endpoint
```
POST /chat {"message": "gw suka film horror"}
  → balas dari agent (LLM)
  → ekstrak memory dari percakapan
  → update profile + graph
  → return {"reply": "...", "memory_saved": [...], "profile": {...}}
```

## Kenapa Ini Bikin Cruzl Labs BEDA

| Fitur | Pendekatan umum | Cruzl Labs |
|-------|-----------------|------------|
| Chat-driven memory | Managed service / cloud | **Self-host + JSONL** |
| Knowledge graph | Database graph berat | **JSON ringan** |
| User modeling | Cloud-based | **File lokal transparan** |
| Point extraction | Hanya retrieval | **Dedup + conflict otomatis** |

## Kenapa Beda dari Sistem Lain

| Mereka | Kita |
|--------|------|
| SaaS / DB berat (Chroma, Postgres) | JSONL ringan, self-host |
| Satu store campur aduk | Type field + confidence + TTL |
| Search tool biasa | **Retrieval pipeline + context assembly** |
| Mahal | Gratis, 0 RAM embedding |
