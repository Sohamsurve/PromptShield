"""Repo secret scan and production CSP check. Prints counts, never secret values."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"),
]
SKIP = {".env", ".git"}


def _tracked() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line for line in out.splitlines() if line and not line.endswith(".env")]


def main() -> int:
    hits = 0
    for rel in _tracked():
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in PATTERNS:
            if pat.search(text):
                hits += 1
                print(f"secret-pattern {rel}")
                break
    cfg = (ROOT / "apps/web/next.config.ts").read_text(encoding="utf-8")
    if "NODE_ENV" not in cfg or "nosniff" not in cfg or "frame-ancestors" not in cfg:
        print("csp headers missing")
        hits += 1
    print(f"security_scan hits={hits}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
