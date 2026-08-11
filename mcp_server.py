"""Cruzl Labs — MCP Server.

Expose Cruzl Labs memory sebagai MCP tools — bisa dipakai Hermes,
Claude Code, Cursor, dan semua client MCP-compatible.

Setup di config (stdio):
  mcp_servers:
    cruzl:
      command: "python3"
      args: ["/path/to/cruzl-labs/mcp_server.py"]
      env:
        CRUZL_API_KEY: "cl_xxx"

Atau jalankan langsung:
  python3 mcp_server.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from src.client import Client

# Config
API_KEY = os.environ.get("CRUZL_API_KEY", "")
BASE_URL = os.environ.get("CRUZL_BASE_URL", "http://127.0.0.1:8131")

mcp = FastMCP("cruzl-labs")


def _client() -> Client:
    if not API_KEY:
        raise RuntimeError("CRUZL_API_KEY belum di-set. Set via env di config MCP.")
    return Client(api_key=API_KEY, base_url=BASE_URL)


@mcp.tool()
def memory_add(text: str, mem_type: str = "fact", confidence: float = 0.8, tags: str = "") -> dict:
    """Tambah memory. text = isi memory, mem_type = fact|profile|reflection|relation, tags dipisah koma."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    c = _client()
    return c.add(text, mem_type=mem_type, confidence=confidence, tags=tag_list)


@mcp.tool()
def memory_search(query: str) -> list:
    """Cari memory (keyword)."""
    return _client().search(query)


@mcp.tool()
def memory_search_semantic(query: str, top_k: int = 5) -> list:
    """Cari memory berdasarkan makna (semantic)."""
    return _client().search_semantic(query, top_k=top_k)


@mcp.tool()
def memory_search_hybrid(query: str, top_k: int = 5) -> list:
    """Cari memory gabungan keyword + semantic."""
    return _client().search_hybrid(query, top_k=top_k)


@mcp.tool()
def memory_list(tag: str = "", mem_type: str = "") -> list:
    """List memory. Opsional filter by tag atau type."""
    return _client().list(tag=tag or None, mem_type=mem_type or None)


@mcp.tool()
def memory_delete(mem_id: str) -> dict:
    """Hapus memory by id."""
    return _client().delete(mem_id)


@mcp.tool()
def memory_tags() -> dict:
    """List semua tag + jumlah memory per tag."""
    return _client().tags()


@mcp.tool()
def context_get(query: str = "", top_facts: int = 3) -> str:
    """Ambil konteks user untuk di-inject ke system prompt. Opsional query → fakta relevan aja."""
    c = _client()
    ctx = c.context(query=query or None, top_facts=top_facts)
    return ctx.get("context", "")


@mcp.tool()
def chat_remember(message: str, agent_reply: str = "", auto_extract: bool = True) -> dict:
    """Kirim percakapan → memory di-simpan & di-extract otomatis."""
    return _client().chat(message, agent_reply=agent_reply, auto_extract=auto_extract)


@mcp.tool()
def profile_get() -> dict:
    """Lihat profil user (dari memory yang terkumpul)."""
    return _client().profile()


@mcp.tool()
def graph_get() -> dict:
    """Lihat knowledge graph user."""
    return _client().graph()


@mcp.tool()
def raw_get(days: int = 7) -> dict:
    """Lihat raw memory (detail mentah) N hari terakhir."""
    return _client().raw(days=days)


@mcp.tool()
def stats_get() -> dict:
    """Statistik memory user."""
    return _client().stats()


if __name__ == "__main__":
    mcp.run()
