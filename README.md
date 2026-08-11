# 🧪 Cruzl Labs

**AI-native memory layer untuk agent — dibangun dari nol, ringan, self-host.**

> "Memory = belajar, bukan cuma nyimpen."

Dibangun oleh **0xcruzl** — AI agent operator & crypto ops.

## 🧬 DNA — Diambil dari 4 Sistem Memory

```
Cruzl Labs =
  Mem0     → operasi cerdas (ADD/UPDATE/DELETE/NOOP), multi-scope
  Hindsight → entity resolution, retain/recall/reflect  ← PEMBEDA UTAMA
  Honcho   → user modeling, dialectic cold/warm prompt
  Zep      → knowledge graph + temporal, versi RINGAN (JSON)
```

**Filosofi: "Semua kekuatan, tanpa beratnya"** — simple JSONL, tapi fitur cerdas kayak yang mahal.

## 🚀 Quickstart

```bash
# Memory
python3 cli.py add "User suka horror movies dan western films" --tag hobby
python3 cli.py search "horror"
python3 cli.py list --scope agent
python3 cli.py delete mem_90679c8f
python3 cli.py stats

# API key (buat user lain)
python3 cli.py key create --label "teman-crypto" --scope agent
python3 cli.py key verify --key mb_xxxxx
python3 cli.py key list
python3 cli.py key revoke key_xxxxx
```

## 📁 Struktur

```
cruzl-labs/
├── cli.py            # CLI (memory + key management)
├── src/
│   ├── storage.py    # JSONL storage + keyword search
│   └── auth.py       # API key (hash-only, crypto-secure)
├── storage/          # Data (memories.jsonl, api_keys.json)
├── docs/DESIGN.md    # Blueprint & roadmap
└── tests/            # Unit tests (coming)
```

## 🔒 Keamanan API Key

- Key mentah cuma muncul **sekali** pas create
- Server cuma simpen **sha256 hash** (DB bocor ≠ key bocor)
- Constant-time compare (anti timing attack)
- Revoke instan

## 🗺️ Roadmap

- [x] **Fase 1** — Storage JSONL + CLI CRUD + tag/scope (MVP)
- [x] **API Key system** — generate/verify/revoke (hash-only)
- [ ] **Fase 1.5** — Semantic search (embedding lokal)
- [ ] **Fase 2** — Entity resolution + knowledge graph + API server
- [ ] **Fase 3** — Reflective summarization + user modeling

## 📬 Kontak

- GitHub: [cruzlxyz](https://github.com/cruzlxyz)
- Web: [cruzl.store](https://cruzl.store)
