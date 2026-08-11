# 🧪 Cruzl Labs

**AI-native memory layer untuk agent — ringan, self-host, dari nol.**

> "Memory = belajar, bukan cuma nyimpen."

Dibangun oleh **0xcruzl** — AI agent operator & crypto ops.

---

## 🏆 Kenapa Cruzl Labs Beda dari Memory Agent Lain?

| | Mem0 | Honcho | Hindsight | Zep | **Cruzl Labs** |
|---|------|--------|-----------|-----|----------------|
| **RAM** | 300MB+ (vector DB) | SaaS | 1GB+ | 500MB+ (graph DB) | **~25-110 MB** ✅ |
| **Biaya** | Freemium/SaaS | Managed paid | Pay-per-token | Enterprise | **Gratis, self-host** ✅ |
| **Storage** | Chroma/PG | Cloud | Local heavy | Neo4j | **JSONL (1 file!)** ✅ |
| **Embedding** | Local model | Cloud | Local model | Cloud | **Via API (0 RAM)** ✅ |
| **Kompleksitas** | Perlu setup DB | Perlu service | Berat | Berat | **1 command jalan** ✅ |
| **Isolasi user** | Multi-level rumit | Multi-level | Multi-level | Multi-level | **1 key = 1 user, simpel** ✅ |
| **Transparansi** | Kotak hitam | Kotak hitam | Kotak hitam | Kotak hitam | **Baca JSONL langsung** ✅ |
| **Lisensi** | Apache 2.0 (ok) | Proprietary | MIT (ok) | AGPL | **MIT** ✅ |

---

## 🧬 DNA — Diambil dari yang Terbaik

```
Cruzl Labs =
  Mem0     → operasi cerdas (ADD/UPDATE/DELETE), multi-scope
  Hindsight → entity resolution, retain/recall/reflect  ← PEMBEDA UTAMA
  Honcho   → user modeling, dialectic reasoning
  Zep      → knowledge graph + temporal (versi ringan)
```

**"Semua kekuatan, tanpa beratnya."**

## 💡 Kelebihan Utama (TL;DR)

| # | Kelebihan | Detail |
|---|-----------|--------|
| 1 | **Ringan ekstrem** | 25MB inti — jalan di VPS 2GB bareng agent lain |
| 2 | **Transparan total** | Memory = file JSONL yang bisa dibaca manusia |
| 3 | **1 key = 1 user** | Isolasi simpel, ga pusing multi-tenant |
| 4 | **0 RAM embedding** | Semantic search via API, bukan model lokal |
| 5 | **Anti-duplikat** | Dedup + conflict resolution otomatis |
| 6 | **Tanpa lock-in** | Data lu, file lu, format terbuka — migrate kapan aja |

---

## 🚀 Quickstart

```bash
# Memory
python3 cli.py add "User suka horror movies" --tag hobby --type fact
python3 cli.py search "horror"
python3 cli.py list --scope agent
python3 cli.py stats

# API key (1 key = 1 user, otomatis user_id sendiri)
python3 cli.py key create --label "teman-crypto"
python3 cli.py key verify --key mb_xxxxx
python3 cli.py key list
python3 cli.py key revoke key_xxxxx
```

## 📁 Struktur

```
cruzl-labs/
├── cli.py            # CLI (memory + key management)
├── src/
│   ├── storage.py    # JSONL storage + dedup + conflict resolution
│   └── auth.py       # API key (hash-only, 1 key = 1 user)
├── storage/          # Data (memories.jsonl, api_keys.json) — ga ke-commit
├── docs/DESIGN.md    # Blueprint & roadmap
└── tests/            # Unit tests (coming)
```

## 🔒 Keamanan

- Key mentah cuma muncul **sekali** — server simpen sha256 hash
- Constant-time compare (anti timing attack)
- Revoke instan
- Data user **terisolasi per key**

## 🗺️ Roadmap

- [x] Fase 1: Storage JSONL + CLI CRUD + tag/scope/type
- [x] API key system (hash-only, 1 key = 1 user)
- [x] Dedup + conflict resolution
- [ ] Fase 2c: API server (FastAPI + Bearer auth)
- [ ] Fase 3: Semantic search (embedding via API) + hybrid ranking
- [ ] Fase 4: Reflective summarization
- [ ] Fase 5: Entity resolution + graph
- [ ] Fase 6: Export Obsidian + backup

## 📬 Kontak

- GitHub: [cruzlxyz](https://github.com/cruzlxyz)
- Web: [cruzl.store](https://cruzl.store)
