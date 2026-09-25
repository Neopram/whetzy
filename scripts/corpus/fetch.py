"""Descarga una fuente al corpus: `git` (clon superficial) o `http` (un fichero).

Torrents: solo cuando sean el canal oficial de un corpus legal (ADR-42). No se
implementan aquí hasta que haga falta uno; `fetch.py` rechaza `kind=torrent`
con ese motivo en vez de fingir que lo soporta.

    python -m scripts.corpus.fetch --name thealgorithms-python --kind git \
        --url https://github.com/TheAlgorithms/Python
    python -m scripts.corpus.fetch --name gutenberg-1661 --kind http \
        --url https://www.gutenberg.org/cache/epub/1661/pg1661.txt
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from scripts.corpus.common import CORPUS, now_iso, source_dir, write_meta


def fetch_git(url: str, dest: Path, sparse: list[str] | None = None) -> str:
    if dest.exists():
        shutil.rmtree(dest)
    cmd = ["git", "clone", "--depth", "1", "--quiet"]
    if sparse:
        cmd += ["--filter=blob:none", "--sparse"]
    subprocess.run([*cmd, url, str(dest)], check=True)
    if sparse:
        # Los ficheros de licencia de la raíz siempre entran, aunque el
        # sparse-checkout pida solo una carpeta.
        subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", "--no-cone", *sparse,
                        "/LICENSE*", "/COPYING*", "/NOTICE*"], check=True)
    sha = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    return sha


def fetch_http(url: str, dest: Path) -> str:
    import hashlib

    dest.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "whetzy-corpus/1.0 (+https://whetzy.com)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    name = url.rstrip("/").rsplit("/", 1)[-1] or "index.html"
    (dest / name).write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--kind", required=True, choices=["git", "http", "torrent"])
    ap.add_argument("--url", required=True)
    ap.add_argument("--sparse", nargs="*", help="carpetas para sparse-checkout (git)")
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    a = ap.parse_args(argv)
    if a.kind == "torrent":
        print("[fetch] torrent: sin implementar; solo se admitirá como canal oficial de un corpus legal (ADR-42)")
        return 2
    dest = source_dir(a.name, a.corpus)
    content = dest / "raw"
    ident = fetch_git(a.url, content, a.sparse) if a.kind == "git" else fetch_http(a.url, content)
    write_meta(dest, name=a.name, kind=a.kind, url=a.url, fetched_at=now_iso(), sha=ident)
    print(f"[fetch] {a.name}: {a.kind} {a.url} → {content} ({ident[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
