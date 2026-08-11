# Cruzl Labs — Blueprint v0.2

AI-native memory layer untuk agent — dibangun dari nol, ringan, self-host.
> "Memory = belajar, bukan cuma nyimpen."

## DNA — Diambil dari 4 Sistem Memory

```
Cruzl Labs =
  Mem0     → operasi cerdas (ADD/UPDATE/DELETE/NOOP), multi-scope
  Hindsight → entity resolution, retain/recall/reflect  ← PEMBEDA UTAMA
  Honcho   → user modeling, dialectic cold/warm prompt
  Zep      → knowledge graph + temporal, versi RINGAN (JSON)
```

**Filosofi: "Semua kekuatan, tanpa beratnya"** — simple JSONL, fitur cerdas kayak yang mahal.

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
- [ ] **Fase 2a: Dedup + conflict resolution** ← SEKARANG
- [ ] Fase 2b: Multi-user isolation (user_id)
- [ ] Fase 2c: API server (FastAPI + auth)
- [ ] Fase 3: Semantic search (embedding API) + hybrid ranking
- [ ] Fase 4: Reflective summarization (LLM ringkas sesi)
- [ ] Fase 5: Entity resolution + graph
- [ ] Fase 6: Export Obsidian + backup

## Kenapa Beda dari Sistem Lain

| Mereka | Kita |
|--------|------|
| SaaS / DB berat (Chroma, Postgres) | JSONL ringan, self-host |
| Satu store campur aduk | Type field + confidence + TTL |
| Search tool biasa | **Retrieval pipeline + context assembly** |
| Mahal | Gratis, 0 RAM embedding |
