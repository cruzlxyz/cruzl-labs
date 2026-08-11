# 🤝 Cruzl Labs — Integrasi dengan Agent Mana Pun

Cruzl Labs itu **framework-agnostic** — API HTTP standar + API key.
Agent mana pun bisa pake: Hermes, Claude Code, Codex, OpenClaw, Cursor, custom agent.

---

## 🧠 Konsep: Memory DI LUAR Session

```
AGENT (session sementara)
   │  pindah session / restart / ganti platform
   ▼
CRUZL LABS (permanen, per-user)
   └── inget terus: fakta, preferensi, pelajaran, relasi
```

**2 momen penting:**
1. **Session MULAI** → `GET /context` → inject ke system prompt ("ini user-nya")
2. **Selama chat** → `POST /chat` → memory otomatis di-extract & disimpan

---

## 🔌 Integrasi per Agent

### 1. Hermes (plugin)
```python
# plugins/cruzl-labs/__init__.py (ringkas)
from src.client import Client

def register(ctx):
    c = Client(api_key=os.environ["CRUZL_API_KEY"])

    @ctx.on_session_start
    def inject(**kw):
        ctx.inject_context(c.context()["context"])

    @ctx.post_tool_call
    def remember(**kw):
        c.chat(message=kw.get("user_message", ""), agent_reply=kw.get("reply", ""))
```

### 2. Claude Code (CLAUDE.md)
```markdown
<!-- CLAUDE.md — auto-load tiap session -->
Sebelum mulai, ambil konteks user:
  curl -H "Authorization: Bearer cl_xxx" http://127.0.0.1:8131/context
Simpan memory penting:
  curl -X POST -H "Authorization: Bearer cl_xxx" \
    -H "Content-Type: application/json" \
    -d '{"message":"<pesan>"}' http://127.0.0.1:8131/chat
```

### 3. Codex (AGENTS.md)
```markdown
# AGENTS.md
Konteks user tersedia di: GET /context (Bearer cl_xxx)
Setelah menyelesaikan tugas, kirim ringkasan ke POST /chat
```

### 4. OpenClaw / Cursor / dll
```bash
# Cukup butuh HTTP — pakai curl atau SDK:
# Python: pip install git+https://github.com/cruzlxyz/cruzl-labs
from cruzl import Client
c = Client(api_key="cl_xxx")
ctx = c.context()
```

---

## 🧪 Contoh Alur Lengkap (Hermes)

```
User: "gw suka horror bang"           (session baru)
  → Hermes inject: [Memory] PREFERENCES: ...; KNOWN FACTS: ...
  → Hermes: "Oh iya, lu suka horror ya! Kemarin kita bahas The Wailing..."
  → POST /chat {"message": "gw suka horror"} 
  → Cruzl: extract → simpan fact + update profile + graph
```

**Hasilnya:** obrolan harmonis — agent "inget" user walau ganti session,
ganti platform, atau restart. 🔥

---

## 📦 SDK (Python)

```python
from cruzl import Client
c = Client(api_key="cl_xxx")          # default base_url 127.0.0.1:8131

# inject ke system prompt
ctx = c.context()
system_prompt += f"\n[Memory]\n{ctx['context']}"

# simpen memory dari percakapan
c.chat(message="gw pindah ke Bandung", agent_reply="oke noted!")

# cari memory
results = c.search("bandung")

# lihat profil & graph
c.profile()
c.graph()
```

---

## ⚙️ Satu Key, Semua Agent

```
cl_xxx (user_id: u_cruzl)
  ├── Hermes memakai key ini
  ├── Claude Code memakai key ini
  └── Codex memakai key ini
      └── SEMUA ngeliat memory yang SAMA (user yang sama)
```

Mau pisah? Bikin key baru → user_id baru → memory terpisah.
**1 key = 1 user, fleksibel.**

---

## 🚀 Setup Cepat

```bash
# 1. Jalanin server
python3 api.py          # → http://127.0.0.1:8131

# 2. Bikin key
python3 cli.py key create --label "hermes"

# 3. Test
curl -H "Authorization: Bearer cl_xxx" http://127.0.0.1:8131/context
```
