"""
Validates source licensing:
1. content/sources/index.json exists with at least the verified entries
2. docs/CATALOGO_MAESTRO.md §2.2 has no remaining `verificar` marks in table rows
3. (optional, --check-urls) each URL in the index returns HTTP 2xx/3xx

Exit 0 if all checks pass, 1 if any fail.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
CATALOG = ROOT / "docs" / "CATALOGO_MAESTRO.md"
INDEX = ROOT / "content" / "sources" / "index.json"

REQUIRED_FIELDS = {"url", "name", "license", "mark", "verified_date"}
VALID_MARKS = {"reusar", "H.LIC", "cita"}


def check_index() -> list[str]:
    errors: list[str] = []
    if not INDEX.exists():
        return [f"content/sources/index.json not found at {INDEX}"]
    try:
        entries = json.loads(INDEX.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"content/sources/index.json is not valid JSON: {e}"]
    if not isinstance(entries, list) or len(entries) < 5:
        errors.append(f"index.json has only {len(entries)} entries — expected at least 5")
    for i, entry in enumerate(entries):
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            errors.append(f"entry[{i}] ({entry.get('name','?')}) missing fields: {missing}")
        mark = entry.get("mark", "")
        if mark not in VALID_MARKS:
            errors.append(f"entry[{i}] ({entry.get('name','?')}) has unknown mark: {mark!r}")
    return errors


def check_no_verificar() -> list[str]:
    """Check that §2.2 table rows in CATALOGO_MAESTRO.md have no 'verificar' marks."""
    errors: list[str] = []
    if not CATALOG.exists():
        return [f"CATALOGO_MAESTRO.md not found"]
    text = CATALOG.read_text(encoding="utf-8")
    # Find §2.2 section
    m = re.search(r"### 2\.2.*?(?=^##|\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        errors.append("§2.2 section not found in CATALOGO_MAESTRO.md")
        return errors
    section = m.group(0)
    # Only check table rows (lines starting with |)
    table_lines = [ln for ln in section.splitlines() if ln.strip().startswith("|")]
    bad = []
    for lineno_offset, line in enumerate(table_lines):
        if "verificar" in line.lower():
            bad.append(f"  row: {line[:120]}")
    if bad:
        errors.append(f"§2.2 table has {len(bad)} row(s) with 'verificar' mark:")
        errors.extend(bad)
    return errors


def check_urls(entries: list[dict]) -> list[str]:
    """Optional: verify each URL returns a non-error HTTP response."""
    errors: list[str] = []
    for entry in entries:
        url = entry.get("url", "")
        if not url or not url.startswith("http"):
            continue
        try:
            req = urllib.request.Request(url, method="HEAD",
                                          headers={"User-Agent": "Whetzy-source-checker/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except Exception as e:
            errors.append(f"URL error for {entry['name']}: {url} — {e}")
            continue
        if status >= 400:
            errors.append(f"URL {entry['name']} returned HTTP {status}: {url}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-urls", action="store_true",
                        help="Also verify each URL resolves (requires internet)")
    args = parser.parse_args()

    all_errors: list[str] = []

    idx_errors = check_index()
    if idx_errors:
        print("FAIL [index]")
        for e in idx_errors:
            print(f"  {e}")
        all_errors.extend(idx_errors)
    else:
        entries = json.loads(INDEX.read_text(encoding="utf-8"))
        print(f"OK   [index] {len(entries)} verified entries")

        if args.check_urls:
            url_errors = check_urls(entries)
            if url_errors:
                print("FAIL [urls]")
                for e in url_errors:
                    print(f"  {e}")
                all_errors.extend(url_errors)
            else:
                print(f"OK   [urls] all {len(entries)} URLs reachable")

    ver_errors = check_no_verificar()
    if ver_errors:
        print("FAIL [verificar]")
        for e in ver_errors:
            print(f"  {e}")
        all_errors.extend(ver_errors)
    else:
        print("OK   [verificar] no 'verificar' marks in §2.2 table")

    return 0 if not all_errors else 1


if __name__ == "__main__":
    sys.exit(main())
