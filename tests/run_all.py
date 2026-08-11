#!/usr/bin/env python3
"""Runner semua test Cruzl Labs (tanpa pytest dependency)."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = Path(__file__).resolve().parent

tests = sorted(TEST_DIR.glob("test_*.py"))
print(f"🧪 Cruzl Labs — {len(tests)} test suite\n")

all_passed = True
total = 0
for t in tests:
    r = subprocess.run([sys.executable, str(t)], cwd=ROOT, capture_output=True, text=True)
    last = [l for l in r.stdout.strip().splitlines() if l.strip()][-1] if r.stdout.strip() else "?"
    ok = "lulus" in last
    all_passed = all_passed and ok
    print(f"  {'✅' if ok else '❌'} {t.name}: {last}")
    if not ok:
        print(r.stdout)
        print(r.stderr)

print(f"\n{'🎉 SEMUA LULUS' if all_passed else '⚠️ ADA YANG GAGAL'}")
sys.exit(0 if all_passed else 1)
