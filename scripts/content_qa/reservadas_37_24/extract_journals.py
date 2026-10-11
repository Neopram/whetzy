#!/usr/bin/env python3
"""
Extrae preguntas completadas de los journals de workflow 37.24.
Uso:
  python3 extract_journals.py           # resumen
  python3 extract_journals.py --dump    # vuelca a extracted_questions.json
"""
import json, sys, re
from pathlib import Path
from collections import defaultdict

BASE = Path("/root/.claude/projects/-home-user-whetzy/f27deaa8-7d94-54bb-9529-68ae8cf55f6a/subagents/workflows")
RUNS = {"G1": "wf_cc7adabf-981", "G2": "wf_7463dc0c-7ad", "G3": "wf_9a87f0d1-c37"}
CERT_MAP = {"sk08": "CLF-C02","sk09":"PCEP-30-02","sk10":"SAA-C03","sk11":"AIF-C01",
            "sk40":"CC","sk41":"PCAP-31-03","sk42":"SY0-701","sk43":"MLA-C01"}

def as_json(v):
    if isinstance(v, dict): return v
    if isinstance(v, str):
        try: return json.loads(v)
        except: pass
    return None

def read_pairs(run_id):
    jpath = BASE / run_id / "journal.jsonl"
    if not jpath.exists():
        return {}
    pairs = {}
    with open(jpath) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            t = e.get("type","")
            if t == "started":
                pairs[e["key"]] = {"label": e.get("label",""), "phase": e.get("phase","")}
            elif t == "result":
                k = e["key"]
                if k in pairs:
                    pairs[k]["result"] = e.get("result")
    return pairs

def extract(pairs):
    """
    Labels:
      Escritor:  "escritor sk080101-b0"  → block sk080101-b0; questions have global slot numbers
      Revisor:   "revisor sk080101.1"    → skill sk080101, slot 1
      Corrector: "corrector sk080101.1"  → skill sk080101, slot 1
    Returns:
      write_q:  {(skill, slot): Q}
      review:   {(skill, slot): review_obj}
      corr:     {(skill, slot): corr_obj}
    """
    write_q = {}
    review  = {}
    corr    = {}

    for k, v in pairs.items():
        label = v.get("label", "")
        result = v.get("result")
        if result is None:
            continue
        obj = as_json(result)

        # Escritor: "escritor sk080101-b0"
        m = re.match(r'^escritor\s+((\w+)-b\d+)$', label)
        if m:
            bid = m.group(1)            # sk080101-b0
            skill = m.group(2)          # sk080101
            if obj and "questions" in obj:
                for q in obj["questions"]:
                    slot = q.get("slot")
                    if slot is not None:
                        write_q[(skill, slot)] = q
            continue

        # Revisor: "revisor sk080101.1"
        m = re.match(r'^revisor\s+(\w+)\.(\d+)$', label)
        if m:
            skill, slot = m.group(1), int(m.group(2))
            if obj:
                review[(skill, slot)] = obj
            continue

        # Corrector: "corrector sk080101.1"
        m = re.match(r'^corrector\s+(\w+)\.(\d+)$', label)
        if m:
            skill, slot = m.group(1), int(m.group(2))
            if obj:
                corr[(skill, slot)] = obj
            continue

    return write_q, review, corr

def final_questions(write_q, review, corr):
    out = []
    for (skill, slot), q in sorted(write_q.items()):
        c = corr.get((skill, slot))
        r = review.get((skill, slot))
        fq = None
        status = "unknown"

        if c is not None:
            if c.get("discard"):
                continue
            fq = c.get("question") or q
            status = "corrected"
        elif r is not None:
            defects = r.get("defects", [])
            blockers = [d for d in defects if d.get("severity") in ("blocker", "major")]
            fq = q
            status = "clean" if not blockers else "needs_correction"
        else:
            fq = q
            status = "needs_review"

        fq = dict(fq)
        fq["_skill"] = skill
        fq["_slot"] = slot
        fq["_status"] = status
        out.append(fq)
    return out

def cert_of(skill):
    return CERT_MAP.get(skill[:4], skill[:4])

def main():
    dump = "--dump" in sys.argv
    all_q = []

    for group, run_id in RUNS.items():
        jpath = BASE / run_id / "journal.jsonl"
        if not jpath.exists():
            print(f"{group}: no journal"); continue

        pairs = read_pairs(run_id)
        write_q, review, corr = extract(pairs)

        qs = final_questions(write_q, review, corr)
        by_status = defaultdict(int)
        by_cert = defaultdict(int)
        for q in qs:
            by_status[q["_status"]] += 1
            by_cert[cert_of(q["_skill"])] += 1

        n_started = len(pairs)
        n_done    = sum(1 for v in pairs.values() if v.get("result") is not None)
        print(f"{group} ({run_id}): {n_started} agentes, {n_done} con resultado")
        print(f"  write slots: {len(write_q)}  revisiones: {len(review)}  correcciones: {len(corr)}")
        print(f"  preguntas extraíbles: {len(qs)}")
        print(f"    clean={by_status['clean']}  corrected={by_status['corrected']}  needs_correction={by_status['needs_correction']}  needs_review={by_status['needs_review']}")
        print("  por cert:", dict(sorted(by_cert.items())))
        print()
        all_q.extend(qs)

    print(f"TOTAL: {len(all_q)} preguntas extraíbles")
    clean = sum(1 for q in all_q if q["_status"] in ("clean","corrected"))
    print(f"  listas (clean+corrected): {clean}  |  pendientes: {len(all_q)-clean}")
    needs_corr = sum(1 for q in all_q if q["_status"] == "needs_correction")
    needs_rev  = sum(1 for q in all_q if q["_status"] == "needs_review")
    print(f"  needs_correction: {needs_corr}  needs_review: {needs_rev}")

    if dump:
        out = Path("/tmp/claude-0/-home-user-whetzy/f27deaa8-7d94-54bb-9529-68ae8cf55f6a/scratchpad/res/extracted_questions.json")
        with open(out, "w") as f:
            json.dump(all_q, f, ensure_ascii=False, indent=2)
        print(f"\nVolcado a {out}")

if __name__ == "__main__":
    main()
