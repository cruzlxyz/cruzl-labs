"""Cruzl Labs — Semantic Search (Fase 4).

Embedding via API (0 RAM lokal!) + cosine similarity + hybrid ranking.
Provider: Nvidia NIM (default) / OpenAI-compatible.

Embedding di-cache ke file (embeddings.jsonl) biar ga re-embed tiap kali.

Env:
  CRUZL_EMBED_PROVIDER = nvidia | openai
  CRUZL_EMBED_MODEL    = (default nvidia/llama-nemotron-embed-1b-v2)
  NVIDIA_API_KEY / OPENAI_API_KEY
"""

from __future__ import annotations

import json
import math
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity antara 2 vector."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class EmbeddingClient:
    def __init__(
        self,
        storage_dir: str = "storage",
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.storage_dir = storage_dir
        self.provider = (provider or os.environ.get("CRUZL_EMBED_PROVIDER", "nvidia")).lower()
        self.model = model or os.environ.get(
            "CRUZL_EMBED_MODEL", "nvidia/llama-nemotron-embed-1b-v2"
        )
        self.cache_path = Path(storage_dir) / "embeddings.jsonl"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def embed_texts(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        """Embed list teks. Return list vector."""
        if not texts:
            return []
        if self.provider == "openai":
            return self._embed_openai(texts)
        return self._embed_nvidia(texts, input_type)

    def _embed_nvidia(self, texts: List[str], input_type: str) -> List[List[float]]:
        key = os.environ.get("NVIDIA_API_KEY", "")
        base = os.environ.get("CRUZL_EMBED_BASE_URL", "https://integrate.api.nvidia.com/v1")
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": input_type,  # required untuk asymmetric model
            "truncate": "END",
        }
        req = urllib.request.Request(
            f"{base}/embeddings",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return [item["embedding"] for item in data["data"]]

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        key = os.environ.get("OPENAI_API_KEY", "")
        base = os.environ.get("CRUZL_EMBED_BASE_URL", "https://api.openai.com/v1")
        payload = {"model": self.model or "text-embedding-3-small", "input": texts}
        req = urllib.request.Request(
            f"{base}/embeddings",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return [item["embedding"] for item in data["data"]]

    # ------------------------------------------------------------------
    # Cache ke file
    # ------------------------------------------------------------------

    def _cache(self) -> Dict[str, List[float]]:
        """Baca cache embedding (text → vector)."""
        out = {}
        if not self.cache_path.exists():
            return out
        for line in self.cache_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                out[e["text"]] = e["embedding"]
            except json.JSONDecodeError:
                continue
        return out

    def _save_embedding(self, text: str, vector: List[float]) -> None:
        with open(self.cache_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"text": text, "embedding": vector}, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    def search(self, query: str, memories: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Cari memory paling relevan secara semantic (cosine similarity).

        memories = list entry memory (dari storage), tiap punya 'text'.
        """
        if not memories:
            return []
        # embed query
        q_vec = self.embed_texts([query], input_type="query")[0]

        # cari text memory yang belum di-embed
        cache = self._cache()
        to_embed = []
        for m in memories:
            text = m.get("text", "")
            if text and text not in cache:
                to_embed.append(text)
        if to_embed:
            try:
                vecs = self.embed_texts(to_embed, input_type="passage")
                for text, vec in zip(to_embed, vecs):
                    cache[text] = vec
                    self._save_embedding(text, vec)
            except Exception:
                # kalau embed gagal, fallback kosong
                return []

        # hitung similarity
        scored = []
        for m in memories:
            text = m.get("text", "")
            vec = cache.get(text)
            if vec:
                sim = cosine_similarity(q_vec, vec)
                scored.append({**m, "score": round(sim, 4)})
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]
