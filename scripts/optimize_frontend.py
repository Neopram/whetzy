#!/usr/bin/env python3
"""
Whetzy Frontend Optimizer & Free-Tier Minimizer
Automates dead-code detection, bundle optimization rules, and API request throttling.
"""

import os
import re
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
SRC_DIR = FRONTEND_DIR / "src"

def analyze_bundle_hazards():
    print("=== 1. Checking Heavy Bundle Hazards (Free-Tier & Latency) ===")
    hazards = {
        "monaco-editor": [],
        "pyodide": [],
        "@lottiefiles/react-lottie-player": [],
        "sql.js": []
    }
    
    for path in SRC_DIR.rglob("*.tsx"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        for lib in hazards.keys():
            if re.search(rf'from\s+[\'"]{re.escape(lib)}[\'"]', content):
                hazards[lib].append(str(path.relative_to(SRC_DIR)))
                
    for lib, files in hazards.items():
        if files:
            print(f"[!] {lib} directly imported in {len(files)} files:")
            for f in files:
                print(f"    - {f}")
            print("    -> Recommendation: Replace with dynamic import() / React.lazy() to save initial payload.\n")
        else:
            print(f"[OK] {lib} is lazy-loaded or not imported statically.")

def detect_orphan_components():
    print("\n=== 2. Dead Code & Orphan Components Detection ===")
    all_tsx = list(SRC_DIR.rglob("*.tsx"))
    all_ts = list(SRC_DIR.rglob("*.ts"))
    all_files = all_tsx + all_ts
    
    components = list((SRC_DIR / "components").rglob("*.tsx"))
    used_components = set()
    
    for f in all_files:
        content = f.read_text(encoding="utf-8", errors="ignore")
        for comp in components:
            comp_name = comp.stem
            if re.search(rf'\b{comp_name}\b', content) and f != comp:
                used_components.add(comp)
                
    orphans = [c for c in components if c not in used_components]
    print(f"Total components scanned: {len(components)}")
    if orphans:
        print(f"Potential unreferenced components ({len(orphans)}):")
        for o in orphans:
            print(f"    - {o.relative_to(SRC_DIR)}")
    else:
        print("[OK] No unreferenced components found.")

def audit_api_caching():
    print("\n=== 3. Railway API Request Throttling (Free-Tier Saver) ===")
    query_files = []
    for path in SRC_DIR.rglob("*.tsx"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "useQuery" in content:
            if "staleTime" not in content:
                query_files.append(str(path.relative_to(SRC_DIR)))
                
    if query_files:
        print(f"[!] {len(query_files)} queries found without explicit 'staleTime' (causes repeated Railway API calls):")
        for q in query_files:
            print(f"    - {q}")
        print("    -> Set staleTime: 1000 * 60 * 5 (5 minutes) to cut Railway egress.")
    else:
        print("[OK] All active queries have cached staleTime.")

if __name__ == "__main__":
    analyze_bundle_hazards()
    detect_orphan_components()
    audit_api_caching()
