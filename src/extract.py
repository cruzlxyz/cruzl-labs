"""Cruzl Labs — Point Extraction (Fase 3a).

Ambil poin penting dari percakapan user↔agent memakai LLM.
Provider fleksibel: Ollama (default, gratis) / OpenAI / custom.

Env:
  CRUZL_LLM_PROVIDER = ollama | openai
  CRUZL_LLM_BASE_URL = (default http://localhost:11434 untuk ollama)
  CRUZL_LLM_MODEL    = (default llama3.2 / gpt-4o-mini)
  OPENAI_API_KEY     = buat provider openai
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional


EXTRACT_PROMPT = """Kamu adalah memory extractor untuk AI agent. Dari percakapan berikut, ambil poin-poin penting yang layak diingat jangka panjang.

Aturan:
- Hanya ambil fakta/pengalaman yang berguna buat sesi berikutnya
- Jangan ambil basa-basi, salam, atau hal sepele
- Kategorikan: "fact" (fakta user), "profile" (preferensi/gaya), "reflection" (pelajaran)
- Confidence 0.0-1.0: seberapa yakin fakta ini benar & stabil

Balas HANYA JSON array, format:
[{"type": "fact|profile|reflection", "text": "...", "confidence": 0.9, "tags": ["..."]}]

Percakapan:
{conversation}
"""


class PointExtractor:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or os.environ.get("CRUZL_LLM_PROVIDER", "ollama")).lower()
        self.model = model or os.environ.get("CRUZL_LLM_MODEL", "llama3.2")

    def extract(self, conversation: str) -> List[Dict[str, Any]]:
        """Ekstrak poin penting dari percakapan. Return list memory candidates."""
        # pakai replace, bukan format (prompt mengandung {} JSON contoh)
        prompt = EXTRACT_PROMPT.replace("{conversation}", conversation[:3000])
        try:
            if self.provider == "openai":
                raw = self._call_openai(prompt)
            elif self.provider == "nvidia":
                raw = self._call_nvidia(prompt)
            else:
                raw = self._call_ollama(prompt)
            return self._parse(raw)
        except Exception:
            # LLM ga available → return kosong (API akan fallback ke
            # simpan pesan user sebagai fact, bukan pesan error)
            return []

    # ------------------------------------------------------------------

    def _call_ollama(self, prompt: str) -> str:
        base = os.environ.get("CRUZL_LLM_BASE_URL", "http://localhost:11434")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",  # Ollama support structured output
        }
        req = urllib.request.Request(
            f"{base}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return data.get("message", {}).get("content", "[]")

    def _call_openai(self, prompt: str) -> str:
        key = os.environ.get("OPENAI_API_KEY", "")
        base = os.environ.get("CRUZL_LLM_BASE_URL", "https://api.openai.com/v1")
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]

    def _call_nvidia(self, prompt: str) -> str:
        """Nvidia NIM API (OpenAI-compatible). Nemotron 3 Ultra dll."""
        key = os.environ.get("NVIDIA_API_KEY", "")
        base = os.environ.get("CRUZL_LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        payload = {
            "model": self.model or "nvidia/nemotron-3-ultra-550b-a55b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
        }
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]

    # ------------------------------------------------------------------

    @staticmethod
    def _parse(raw: str) -> List[Dict[str, Any]]:
        """Parse LLM output (toleran: bisa ada markdown fence / teks ekstra)."""
        raw = raw.strip()
        # buang markdown fence kalau ada
        if raw.startswith("```"):
            raw = raw.split("```")[1] if "```" in raw[3:] else raw
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "points" in data:
                return data["points"]
        except json.JSONDecodeError:
            # coba cari array [ ... ] di dalam teks
            start = raw.find("[")
            end = raw.rfind("]")
            if start >= 0 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    pass
        return []
