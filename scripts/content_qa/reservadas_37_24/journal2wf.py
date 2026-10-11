"""Convierte journal.jsonl de un run de Workflow 37.24 al formato {"result":[{sk,q,review,corrected}]} de integ3724.py."""
import json, re, sys
sys.path.insert(0, ".")
from extract_journals import read_pairs, extract, RUNS
for g, run in RUNS.items():
    w, r, c = extract(read_pairs(run))
    out = [{"sk": sk, "q": q, "review": r.get((sk, s)), "corrected": c.get((sk, s))} for (sk, s), q in sorted(w.items())]
    json.dump({"result": out}, open(f"j_{g}.json", "w"), ensure_ascii=False)
    print(g, len(out))
