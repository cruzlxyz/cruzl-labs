# 🧪 Cruzl Labs

**Memory infrastructure untuk AI agents — ringan, self-host, transparan.**

> "Memory = belajar, bukan cuma nyimpen."

Dibangun oleh **0xcruzl** — AI agent operator & crypto ops.

---

## 📦 What is Cruzl Labs?

Cruzl Labs adalah **memory layer** untuk AI agents. Ia memberi agents memori persisten lintas sesi — sehingga agent **tidak lupa** siapa penggunanya, apa yang mereka sukai, dan apa yang sudah terjadi, walau session berpindah, restart, atau ganti platform.

```
AGENT (session sementara, mudah hilang)
   └── Cruzl Labs (permanen, per-user) ── ingat terus
```

**Model:** 1 API key = 1 user. Memory terisolasi per user.

## 🎯 Why Cruzl Labs?

| Capability | Apa artinya |
|-----------|-------------|
| **Ringan ekstrem** | ~25MB inti — jalan di VPS 2GB bareng agent lain |
| **Transparan total** | Memory = file JSONL yang bisa dibaca & diedit manusia |
| **1 key = 1 user** | Isolasi simpel, tanpa kerumitan multi-tenant |
| **0 RAM embedding** | Semantic search via API, bukan model lokal |
| **Anti-duplikat** | Dedup + conflict resolution otomatis |
| **Tanpa lock-in** | Data = file terbuka. Migrasi kapan pun mudah |
| **Universal** | Bisa dipakai agent mana pun via API/SDK |

## 🔍 Fitur

| Fitur | Keterangan |
|-------|-----------|
| **Memory CRUD** | add / search / list / delete, dengan type + confidence |
| **Dedup otomatis** | Memory yang mirip di-update, bukan diduplikasi |
| **Raw + compressed** | Detail mentah tersimpan permanen, inti untuk baca cepat |
| **LLM extraction** | Chat → memory otomatis (fakta, preferensi, pelajaran) |
| **Knowledge graph** | Relasi antar entitas, queryable |
| **User profiling** | Model pengguna yang berkembang dari interaksi |
| **Semantic search** | Cari berdasarkan makna, bukan sekadar keyword |
| **Hybrid search** | Keyword + semantic, ranking gabungan |
| **Relevant-facts** | Ambil top-N fakta relevan — hemat token |
| **Tag filtering** | Filter memory by metadata |
| **Cross-session** | `GET /context` → inject memory ke agent mana pun |

## 🚀 Quickstart

```bash
# Clone & jalankan
git clone https://github.com/cruzlxyz/cruzl-labs.git
cd cruzl-labs

# Tambah & cari memory
python3 cli.py add "User suka horror movies" --tag hobby --type fact
python3 cli.py search "horror"

# Jalankan API server
python3 api.py
# → http://127.0.0.1:8131  (docs: /docs)

# Buat API key (1 key = 1 user)
python3 cli.py key create --label "my-agent"
# → cl_xxxxx  (simpan! cuma muncul sekali)
```

**Atau install via pip:**
```bash
pip install git+https://github.com/cruzlxyz/cruzl-labs.git
cruzl add "memory pertama" --tag test
cruzl-api
```

## 🔌 Integrasi dengan Agent Mana Pun

Cruzl Labs framework-agnostic — API HTTP + API key standar.

```python
from cruzl import Client
c = Client(api_key="cl_xxx")

# Inject ke system prompt saat session mulai
ctx = c.context(query="preferensi pengguna")
system_prompt += f"\n[Memory]\n{ctx['context']}"

# Simpan memory dari percakapan (otomatis di-extract LLM)
c.chat(message="gw suka film horror", agent_reply="oke")

# Semantic search
c.search_semantic("film")
```

Lihat [docs/INTEGRATION.md](docs/INTEGRATION.md) untuk integrasi Hermes, Claude Code, Codex, dan lainnya.

## 🏗️ Arsitektur

```
cruzl-labs/
├── cli.py            # CLI: memory + key management
├── api.py            # FastAPI server (14+ endpoint)
├── src/
│   ├── storage.py    # JSONL storage + dedup + conflict
│   ├── raw_store.py  # Raw memory (mentah, permanen)
│   ├── extract.py    # LLM point extraction
│   ├── embed.py      # Semantic search (embedding via API)
│   ├── graph.py      # Knowledge graph (JSON ringan)
│   ├── profile.py    # User modeling
│   ├── auth.py       # API key (hash-only, 1 key = 1 user)
│   ├── client.py     # Universal SDK
│   └── config.py     # Konfigurasi + .env loading
├── storage/          # Data — file transparan, tanpa lock-in
├── docs/             # Design, install, integration guides
└── pyproject.toml    # pip installable
```

## 🔒 Keamanan

- Key mentah cuma muncul **sekali** — server simpan SHA-256 hash
- Constant-time compare (anti timing attack)
- Revoke instan
- Data user **terisolasi per key**
- Data pribadi **tidak pernah di-commit** ke repo

## 📈 Roadmap

- [x] Storage JSONL + CLI + type/confidence
- [x] API key system (1 key = 1 user)
- [x] Dedup + conflict resolution
- [x] API server (FastAPI)
- [x] Raw + compressed memory
- [x] LLM extraction (chat-driven)
- [x] Knowledge graph + user profiling
- [x] Semantic + hybrid search
- [x] Relevant-facts + tag filtering
- [ ] Document retrieval (RAG)
- [ ] Memory versioning (rollback)
- [ ] Export/backup (Obsidian/Markdown)

## ⚖️ License

MIT

---

## 📬 Kontak

- GitHub: [cruzlxyz](https://github.com/cruzlxyz)
- Web: [cruzl.store](https://cruzl.store)
