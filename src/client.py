"""Cruzl Labs — Universal Client SDK.

Library kecil buat agent mana pun (Hermes, Claude Code, Codex,
OpenClaw, custom agent) biar bisa pake memory Cruzl Labs.

Cara pake:
    from cruzl import Client
    c = Client(api_key="cl_xxx", base_url="http://127.0.0.1:8131")

    # Inject ke system prompt pas session mulai:
    ctx = c.context()
    system_prompt += f"\n[Memory user]\n{ctx['context']}"

    # Simpen memory dari percakapan:
    c.chat(message="gw suka horror", agent_reply="oke")
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class CruzlError(Exception):
    """Error dari API Cruzl Labs."""


class Client:
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:8131"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, body: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()[:200]
            raise CruzlError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise CruzlError(f"Cannot reach {url}: {exc.reason}") from exc

    # ------------------------------------------------------------------
    # Memory CRUD
    # ------------------------------------------------------------------

    def add(self, text: str, mem_type: str = "fact", confidence: float = 0.8,
            tags: Optional[List[str]] = None, scope: str = "user") -> Dict[str, Any]:
        """Tambah memory (dedup otomatis)."""
        return self._request("POST", "/memories", {
            "text": text, "type": mem_type, "confidence": confidence,
            "tags": tags or [], "scope": scope,
        })

    def search(self, query: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/memories/search?q={query}").get("results", [])

    def list(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        path = "/memories" + (f"?scope={scope}" if scope else "")
        return self._request("GET", path).get("memories", [])

    def delete(self, mem_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/memories/{mem_id}")

    # ------------------------------------------------------------------
    # Chat-driven memory (otomatis extract)
    # ------------------------------------------------------------------

    def chat(self, message: str, agent_reply: str = "", auto_extract: bool = True) -> Dict[str, Any]:
        """Kirim percakapan → memory di-extract otomatis."""
        return self._request("POST", "/chat", {
            "message": message,
            "agent_reply": agent_reply,
            "auto_extract": auto_extract,
        })

    # ------------------------------------------------------------------
    # Context (buat inject ke session)
    # ------------------------------------------------------------------

    def context(self) -> Dict[str, Any]:
        """Konteks user — inject ke system prompt pas session mulai."""
        return self._request("GET", "/context")

    def profile(self) -> Dict[str, Any]:
        return self._request("GET", "/profile")

    def graph(self) -> Dict[str, Any]:
        return self._request("GET", "/graph")

    def stats(self) -> Dict[str, Any]:
        return self._request("GET", "/stats")
