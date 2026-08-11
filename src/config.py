"""Cruzl Labs — Konfigurasi (dual-mode: server & local).

Semua bisa di-override via env var:
  CRUZL_STORAGE_DIR  → lokasi data (default: ./storage)
  CRUZL_HOST         → host API (default: 127.0.0.1)
  CRUZL_PORT         → port API (default: 8131)
  CRUZL_API_KEY_FILE → lokasi file key (default: <storage>/api_keys.json)
"""

from __future__ import annotations

import os
from pathlib import Path

# Default: relative ke project (bisa jalan dari mana aja)
_DEFAULT_STORAGE = str(Path(__file__).resolve().parent.parent / "storage")


def storage_dir() -> str:
    """Lokasi data. Default ./storage — override via CRUZL_STORAGE_DIR."""
    return os.environ.get("CRUZL_STORAGE_DIR", _DEFAULT_STORAGE)


def api_host() -> str:
    """Host API. 127.0.0.1 buat local, 0.0.0.0 kalau mau expose."""
    return os.environ.get("CRUZL_HOST", "127.0.0.1")


def api_port() -> int:
    return int(os.environ.get("CRUZL_PORT", "8131"))


def api_key_file() -> str:
    """File API key — default di dalam storage dir."""
    return os.environ.get("CRUZL_API_KEY_FILE", str(Path(storage_dir()) / "api_keys.json"))


def banner() -> str:
    return (
        "🧪 Cruzl Labs\n"
        f"  Storage: {storage_dir()}\n"
        f"  API:     http://{api_host()}:{api_port()}\n"
        f"  Mode:    {'SERVER (exposed)' if api_host() == '0.0.0.0' else 'LOCAL'}"
    )
