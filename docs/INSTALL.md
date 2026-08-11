# 🧪 Cruzl Labs — Install & Run (untuk siapa aja)

Bisa jalan di **PC lu sendiri** atau **server** — 2 cara install.

---

## Cara 1: Clone & Jalankan Langsung (paling gampang)

```bash
# 1. Clone
git clone https://github.com/cruzlxyz/cruzl-labs.git
cd cruzl-labs

# 2. (Opsional) bikin virtualenv
python3 -m venv venv && source venv/bin/activate

# 3. Install dependency
pip install -r requirements-api.txt   # buat API server
# atau
pip install -r requirements.txt        # CLI doang (tanpa API)

# 4. Pakai CLI
python3 cli.py add "Halo, ini memory pertamaku" --tag test
python3 cli.py search "memory"
python3 cli.py stats

# 5. Jalanin API server (opsional)
python3 api.py
# → http://127.0.0.1:8131  (docs: http://127.0.0.1:8131/docs)
```

---

## Cara 2: pip install (buat pengguna Python)

```bash
# Langsung dari GitHub
pip install git+https://github.com/cruzlxyz/cruzl-labs.git

# Terus pake command:
cruzl add "memory pertama" --tag test
cruzl search "memory"
cruzl-api            # jalanin server
```

---

## ⚙️ Konfigurasi (env var)

| Env | Default | Fungsi |
|-----|---------|--------|
| `CRUZL_STORAGE_DIR` | `./storage` | Lokasi data (memory + keys) |
| `CRUZL_HOST` | `127.0.0.1` | Host API (`0.0.0.0` buat expose) |
| `CRUZL_PORT` | `8131` | Port API |

Contoh pindah data ke folder lain:
```bash
export CRUZL_STORAGE_DIR=/home/user/my-memory-data
python3 cli.py add "tersimpan di folder lain"
```

---

## 🔑 API Key (1 key = 1 user)

```bash
# Bikin key buat user lain
python3 cli.py key create --label "teman"
# → cl_xxxxx... (simpan! cuma muncul sekali)

# User lain pake API:
curl -X POST http://127.0.0.1:8131/memories \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"text":"memory rahasia saya","type":"fact"}'
```

Setiap key otomatis dapet `user_id` sendiri — memory tiap user terisolasi.

---

## 🖥️ Mode Server (biar bisa diakses orang lain)

```bash
# 1. Expose ke jaringan
export CRUZL_HOST=0.0.0.0
python3 api.py

# 2. (Rekomendasi) pasang reverse proxy + HTTPS (Caddy/Nginx)
# contoh Caddyfile:
# cruzl.yourdomain.com {
#     reverse_proxy localhost:8131
# }
```

⚠️ **Kalau expose ke publik — WAJIB pakai HTTPS + proteksi.** API key udah ada, tapi jangan biarkan port terbuka tanpa proxy.

---

## 🗂️ Struktur Data (transparan!)

```
storage/
├── memories.jsonl    ← semua memory (bisa dibaca manusia!)
└── api_keys.json     ← hash key (bukan key mentah)
```

Memory lu = file lu. Bisa dibackup, dibaca, dipindah kapan aja. **Tanpa lock-in.**
