"""
Bidirectional diff: API.md documented endpoints vs live OpenAPI spec.

Exit 0 if everything matches, 1 if there are discrepancies.
"""
import re
import sys

# ---------------------------------------------------------------------------
# 1. Parse API.md for documented endpoints
# ---------------------------------------------------------------------------

def parse_api_md(path: str) -> set[tuple[str, str]]:
    """Return a set of (METHOD, /path) tuples found in API.md code blocks."""
    methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    documented: set[tuple[str, str]] = set()

    with open(path, encoding="utf-8") as f:
        in_block = False
        for line in f:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_block = not in_block
                continue
            if not in_block:
                continue
            # Lines like: POST /auth/login   → ...
            # or:          GET  /health/live    → ...
            for m in methods:
                if stripped.startswith(m + " ") or stripped.startswith(m + "/"):
                    rest = stripped[len(m):].strip()
                    path_part = rest.split()[0].split("→")[0].strip()
                    if path_part.startswith("/"):
                        # Normalise: strip base /api/v1 if present
                        if path_part.startswith("/api/v1"):
                            path_part = path_part[len("/api/v1"):]
                        documented.add((m, path_part))
    return documented


# ---------------------------------------------------------------------------
# 2. Parse OpenAPI spec for actual endpoints
# ---------------------------------------------------------------------------

def get_openapi_endpoints() -> dict[str, set[str]]:
    """Return {METHOD: set_of_paths} from the live FastAPI app."""
    try:
        sys.path.insert(0, ".")
        from app.main import app  # type: ignore
        spec = app.openapi()
    except Exception as e:
        print(f"ERROR: cannot import FastAPI app: {e}", file=sys.stderr)
        sys.exit(1)

    skip_methods = {"parameters", "head", "options"}
    result: dict[str, set[str]] = {}
    for raw_path, methods_obj in spec["paths"].items():
        # Normalise: strip /api/v1 prefix from API routes; keep root paths as-is
        if raw_path.startswith("/api/v1"):
            path = raw_path[len("/api/v1"):]
        else:
            path = raw_path
        for method in methods_obj:
            if method.lower() in skip_methods:
                continue
            m = method.upper()
            result.setdefault(m, set()).add(path)
    return result


# ---------------------------------------------------------------------------
# 3. Compare
# ---------------------------------------------------------------------------

def main() -> int:
    import pathlib
    api_md = pathlib.Path(__file__).parent.parent / "docs" / "API.md"
    if not api_md.exists():
        print(f"ERROR: {api_md} not found", file=sys.stderr)
        return 1

    documented = parse_api_md(str(api_md))
    openapi_by_method = get_openapi_endpoints()

    # Flatten OpenAPI into the same set shape
    actual: set[tuple[str, str]] = set()
    for method, paths in openapi_by_method.items():
        for p in paths:
            actual.add((method, p))

    missing_from_docs = actual - documented
    extra_in_docs = documented - actual

    ok = True

    if missing_from_docs:
        ok = False
        print("FAIL — endpoints in OpenAPI but NOT documented in API.md:")
        for method, path in sorted(missing_from_docs):
            print(f"  {method:7s} {path}")
    else:
        print("OK   — all OpenAPI endpoints documented in API.md")

    if extra_in_docs:
        ok = False
        print("FAIL — endpoints documented in API.md but NOT in OpenAPI spec:")
        for method, path in sorted(extra_in_docs):
            print(f"  {method:7s} {path}")
    else:
        print("OK   — no phantom endpoints in API.md")

    total_openapi = len(actual)
    total_docs = len(documented)
    print(f"\nOpenAPI: {total_openapi} endpoints | API.md: {total_docs} endpoints documented")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
