#!/usr/bin/env python3
"""Memory Bridge CLI — Fase 1 MVP.

Usage:
    memory add "text" [--tag t1 --tag t2] [--scope user|session|agent]
    memory search "query" [--scope user]
    memory list [--scope user]
    memory delete <id>
    memory stats
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.storage import MemoryStore  # noqa: E402


def cmd_add(args: argparse.Namespace, store: MemoryStore) -> int:
    if not args.text:
        print("❌ Error: text wajib diisi", file=sys.stderr)
        return 1
    entry = store.add(
        args.text,
        source="cli",
        scope=args.scope,
        tags=args.tags,
        mem_type=args.type,
        confidence=args.confidence,
    )
    if entry.get("_deduped"):
        print(f"🔄 Memory sudah ada — di-UPDATE: {entry['id']}")
    else:
        print(f"✅ Memory disimpan: {entry['id']}")
    print(f"   [{entry.get('type')}] {entry['text']}")
    return 0


def cmd_search(args: argparse.Namespace, store: MemoryStore) -> int:
    results = store.search(args.query, scope=args.scope)
    if not results:
        print("🔍 Tidak ada hasil.")
        return 0
    print(f"🔍 {len(results)} hasil untuk: \"{args.query}\"")
    print()
    for m in results:
        print(f"  [{m['id']}] ({m.get('scope')}) {m['text']}")
    return 0


def cmd_list(args: argparse.Namespace, store: MemoryStore) -> int:
    memories = store.all()
    if args.scope:
        memories = [m for m in memories if m.get("scope") == args.scope]
    if not memories:
        print("📭 Kosong.")
        return 0
    print(f"📚 {len(memories)} memory:")
    print()
    for m in memories:
        tags = f" [{', '.join(m.get('tags', []))}]" if m.get("tags") else ""
        print(f"  [{m['id']}] ({m.get('scope')}) {m['text']}{tags}")
    return 0


def cmd_delete(args: argparse.Namespace, store: MemoryStore) -> int:
    if store.delete(args.id):
        print(f"🗑️  Memory {args.id} dihapus.")
    else:
        print(f"❌ Memory {args.id} tidak ditemukan.", file=sys.stderr)
        return 1
    return 0


def cmd_stats(args: argparse.Namespace, store: MemoryStore) -> int:
    s = store.stats()
    print("📊 Statistik Memory")
    print(f"  Total: {s['total']}")
    print(f"  By scope: {s['by_scope']}")
    print(f"  File: {s['file_size_bytes']} bytes")
    return 0


def cmd_key(args: argparse.Namespace, store: MemoryStore) -> int:
    from src.auth import KeyStore

    ks = KeyStore(args.storage)
    if args.action == "create":
        res = ks.create_key(label=args.label, scope=args.scope)
        print(f"🔑 API key dibuat!")
        print(f"  Key ID: {res['key_id']}")
        print(f"  Key:    {res['key']}")
        print(f"  ⚠️  {res['warning']}")
        print(f"  Scope:  {args.scope}")
        print()
        print("  Contoh pake:")
        print(f"  curl -H 'Authorization: Bearer {res['key']}' ...")
    elif args.action == "list":
        keys = ks.list_keys()
        if not keys:
            print("📭 Belum ada key.")
            return 0
        print(f"🔑 {len(keys)} API key:")
        for kid, entry in keys.items():
            revoked = " [REVOKED]" if entry.get("revoked") else ""
            print(f"  {kid} | {entry.get('label','')} | {entry.get('scope')} | created: {entry.get('created_at','')[:10]}{revoked}")
    elif args.action == "revoke":
        if ks.revoke(args.id):
            print(f"🗑️  Key {args.id} di-revoke.")
        else:
            print(f"❌ Key {args.id} tidak ditemukan.", file=sys.stderr)
            return 1
    elif args.action == "verify":
        if not args.key:
            print("❌ Perlu --key buat verify", file=sys.stderr)
            return 1
        info = ks.verify(args.key)
        if info:
            print(f"✅ Key VALID: {info.get('id')} ({info.get('label','')}) scope={info.get('scope')}")
        else:
            print("❌ Key TIDAK valid / sudah di-revoke.")
            return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memory", description="Memory Bridge CLI")
    parser.add_argument("--storage", default="storage", help="Storage directory")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Tambah memory")
    p_add.add_argument("text")
    p_add.add_argument("--tag", dest="tags", action="append", default=[])
    p_add.add_argument("--scope", default="user", choices=["user", "session", "agent"])
    p_add.add_argument("--type", dest="type", default="fact", choices=["fact", "profile", "reflection", "relation"])
    p_add.add_argument("--confidence", dest="confidence", type=float, default=0.8)
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", help="Cari memory")
    p_search.add_argument("query")
    p_search.add_argument("--scope")
    p_search.set_defaults(func=cmd_search)

    p_list = sub.add_parser("list", help="List semua memory")
    p_list.add_argument("--scope")
    p_list.set_defaults(func=cmd_list)

    p_del = sub.add_parser("delete", help="Hapus memory")
    p_del.add_argument("id")
    p_del.set_defaults(func=cmd_delete)

    p_stats = sub.add_parser("stats", help="Statistik")
    p_stats.set_defaults(func=cmd_stats)

    p_key = sub.add_parser("key", help="Kelola API key")
    key_sub = p_key.add_subparsers(dest="action", required=True)

    k_create = key_sub.add_parser("create", help="Buat API key baru")
    k_create.add_argument("--label", default="")
    k_create.add_argument("--scope", default="user", choices=["user", "session", "agent"])
    k_create.set_defaults(func=cmd_key)

    k_list = key_sub.add_parser("list", help="List semua key")
    k_list.set_defaults(func=cmd_key)

    k_revoke = key_sub.add_parser("revoke", help="Revoke key")
    k_revoke.add_argument("id")
    k_revoke.set_defaults(func=cmd_key)

    k_verify = key_sub.add_parser("verify", help="Verifikasi key")
    k_verify.add_argument("--key", required=True)
    k_verify.set_defaults(func=cmd_key)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    store = MemoryStore(args.storage)
    return args.func(args, store)


if __name__ == "__main__":
    sys.exit(main())
