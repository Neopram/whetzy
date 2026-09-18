#!/usr/bin/env python3
"""
i18n Parity Audit for Whetzy

Scans all i18n content (frontend, backend email templates, legal docs)
and generates a comprehensive audit report with:
  - Key parity between ES and EN translations
  - Hardcoded strings in frontend components
  - Backend email template parity
  - Legal document language variants
  - Missing translations by category

Usage:
  python scripts/audit_i18n.py [--output report.json]

Output:
  JSON report with category, file, missing keys, parity percentages
"""

import json
import sys
from pathlib import Path
from typing import Any
import re

def find_project_root() -> Path:
    """Locate project root (where .git exists)."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent


def audit_frontend_i18n(root: Path) -> dict[str, Any]:
    """Audit frontend i18n translation files."""
    i18n_dir = root / "frontend" / "src" / "i18n"
    result = {
        "category": "frontend-i18n",
        "files": {},
        "parity_pct": 0.0,
        "missing": [],
    }

    if not i18n_dir.exists():
        result["error"] = "i18n directory not found"
        return result

    en_file = i18n_dir / "en" / "common.json"
    es_file = i18n_dir / "es" / "common.json"

    if not en_file.exists() or not es_file.exists():
        result["error"] = f"Missing files: en={en_file.exists()}, es={es_file.exists()}"
        return result

    try:
        with open(en_file, encoding='utf-8') as f:
            en_data = json.load(f)
        with open(es_file, encoding='utf-8') as f:
            es_data = json.load(f)
    except json.JSONDecodeError as e:
        result["error"] = f"JSON parse error: {e}"
        return result

    # Flatten nested dicts to get all keys
    def flatten_keys(obj, prefix=""):
        keys = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.add(full_key)
                if isinstance(v, dict):
                    keys.update(flatten_keys(v, full_key))
        return keys

    en_keys = flatten_keys(en_data)
    es_keys = flatten_keys(es_data)

    missing_in_en = es_keys - en_keys
    missing_in_es = en_keys - es_keys
    all_keys = en_keys | es_keys

    if missing_in_en:
        result["missing"].append({
            "lang": "en",
            "keys": sorted(missing_in_en)
        })

    if missing_in_es:
        result["missing"].append({
            "lang": "es",
            "keys": sorted(missing_in_es)
        })

    result["files"] = {
        "en": str(en_file.relative_to(root)),
        "es": str(es_file.relative_to(root))
    }

    # Parity: both languages have same keys
    parity = 0.0
    if all_keys:
        parity = ((len(all_keys) - len(missing_in_en) - len(missing_in_es)) / len(all_keys)) * 100
    result["parity_pct"] = round(parity, 2)
    result["total_keys"] = len(all_keys)
    result["en_keys"] = len(en_keys)
    result["es_keys"] = len(es_keys)

    return result


def audit_backend_emails(root: Path) -> dict[str, Any]:
    """Audit backend email templates."""
    result = {
        "category": "backend-emails",
        "files": {},
        "parity_pct": 0.0,
        "missing": [],
    }

    email_service = root / "backend" / "app" / "services" / "email.py"

    if not email_service.exists():
        result["error"] = "Email service file not found"
        return result

    # Parse the Python file to extract templates
    with open(email_service, encoding='utf-8') as f:
        file_content = f.read()

    # Find all template names: "name": { "es": ... "en": ...}
    # We need to check if both es and en sections exist for each template
    es_templates = set()
    en_templates = set()

    # Look for template definitions. Pattern: "template_name": { ... "es": { ... }, ... "en": { ... }
    # Using a more flexible approach: extract all "es": and "en": between quotes
    template_names = re.findall(r'"([a-z_]+)"\s*:\s*{', file_content)
    
    for tname in template_names:
        # Find the section for this template
        # Pattern: "tname": { ... up to the next "word": {
        pattern = f'"{tname}"' + r'\s*:\s*{([^}]*(?:{[^}]*}[^}]*)*)}(?:\s*,)?'
        match = re.search(pattern, file_content, re.DOTALL)
        
        if match:
            section = match.group(1)
            has_es = '"es":' in section
            has_en = '"en":' in section
            
            if has_es:
                es_templates.add(tname)
            if has_en:
                en_templates.add(tname)

    all_templates = es_templates | en_templates
    missing_in_en = es_templates - en_templates
    missing_in_es = en_templates - es_templates

    if missing_in_en:
        result["missing"].append({
            "lang": "en",
            "templates": sorted(missing_in_en)
        })

    if missing_in_es:
        result["missing"].append({
            "lang": "es",
            "templates": sorted(missing_in_es)
        })

    result["files"] = {
        "file": str(email_service.relative_to(root))
    }

    parity = 0.0
    if all_templates:
        parity = ((len(all_templates) - len(missing_in_en) - len(missing_in_es)) / len(all_templates)) * 100
    result["parity_pct"] = round(parity, 2)
    result["total_templates"] = len(all_templates)
    result["es_templates"] = len(es_templates)
    result["en_templates"] = len(en_templates)

    return result


def audit_legal_docs(root: Path) -> dict[str, Any]:
    """Audit legal documents for ES/EN variants."""
    result = {
        "category": "legal-docs",
        "files": {},
        "parity_pct": 0.0,
        "missing": [],
    }

    legal_dir = root / "legal"

    if not legal_dir.exists():
        result["error"] = "Legal directory not found"
        return result

    # Look for .md files
    doc_files = {}
    for md_file in legal_dir.glob("*.md"):
        doc_files[md_file.stem] = md_file

    result["files"] = {
        doc: str(path.relative_to(root)) for doc, path in doc_files.items()
    }

    # Check which have both ES and EN variants
    es_docs = set()
    en_docs = set()

    for doc_name in doc_files:
        # Check if file has .es or .en suffix
        if doc_name.endswith(".es"):
            base = doc_name[:-3]
            es_docs.add(base)
        elif doc_name.endswith(".en"):
            base = doc_name[:-3]
            en_docs.add(base)
        else:
            # Assume English if no suffix
            en_docs.add(doc_name)

    all_docs = es_docs | en_docs
    missing_in_en = es_docs - en_docs
    missing_in_es = en_docs - es_docs

    if missing_in_en:
        result["missing"].append({
            "lang": "en",
            "docs": sorted(missing_in_en)
        })

    if missing_in_es:
        result["missing"].append({
            "lang": "es",
            "docs": sorted(missing_in_es)
        })

    parity = 0.0
    if all_docs:
        parity = ((len(all_docs) - len(missing_in_en) - len(missing_in_es)) / len(all_docs)) * 100
    result["parity_pct"] = round(parity, 2)
    result["total_docs"] = len(all_docs)
    result["es_docs"] = len(es_docs)
    result["en_docs"] = len(en_docs)

    return result


def audit_frontend_hardcoded(root: Path) -> dict[str, Any]:
    """Scan frontend components for obvious hardcoded strings."""
    result = {
        "category": "frontend-hardcoded",
        "files": [],
        "suspicious_strings": [],
        "warnings": 0,
    }

    src_dir = root / "frontend" / "src"
    if not src_dir.exists():
        result["error"] = "Frontend src not found"
        return result

    suspicious_count = 0
    for ts_file in src_dir.rglob("*.tsx"):
        if "test" in ts_file.name or ".spec." in ts_file.name:
            continue

        try:
            with open(ts_file, encoding='utf-8') as f:
                content = f.read()

            if re.search(r'return\s*\(\s*[^{]*"[A-Z][^"]{10,}"', content):
                suspicious_count += 1
                result["files"].append(str(ts_file.relative_to(root)))
        except Exception:
            pass

    result["warnings"] = suspicious_count
    if suspicious_count > 0:
        result["note"] = "Some components may have hardcoded strings. Manual review recommended."

    return result


def main():
    """Run all audits and generate report."""
    root = find_project_root()

    audits = [
        audit_frontend_i18n(root),
        audit_backend_emails(root),
        audit_legal_docs(root),
        audit_frontend_hardcoded(root),
    ]

    parity_values = [a.get("parity_pct", 0) for a in audits if "parity_pct" in a]
    overall_parity = sum(parity_values) / len(parity_values) if parity_values else 0

    report = {
        "overall_parity_pct": round(overall_parity, 2),
        "audits": audits,
        "summary": {
            "total_categories": len(audits),
            "categories_with_warnings": sum(1 for a in audits if a.get("missing")),
            "parity_threshold": 95.0,
            "status": "PASS" if overall_parity >= 95 else "WARN",
        }
    }

    return report


if __name__ == "__main__":
    report = main()
    print(json.dumps(report, indent=2))
    sys.exit(0)
