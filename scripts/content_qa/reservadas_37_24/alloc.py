"""37.24: reparte 2×L reservadas por dominio (peso del blueprint, mayor resto) y por skill dentro del dominio."""
import json, sys, collections
REPO = sys.argv[1]
T = json.load(open(f"{REPO}/content/curriculum/tracks.json"))
T = T if isinstance(T, list) else T.get("tracks", T)
T = list(T.values()) if isinstance(T, dict) else T
CERTS = ["track08","track09","track10","track11","track40","track41","track42","track43"]
def split(total, weights):
    exact = {k: total*w/sum(weights.values()) for k, w in weights.items()}
    a = {k: int(v) for k, v in exact.items()}
    for k in sorted(exact, key=lambda k: (-(exact[k]-int(exact[k])), k))[: total-sum(a.values())]: a[k] += 1
    return a
out = {}
for t in T:
    if t["id"] not in CERTS: continue
    L = t["certification"]["exam_question_count"]; total = 2*L
    dom_w, dom_sk, names = {}, collections.defaultdict(list), {}
    declared = t.get("exam_domains")
    if declared:
        for d in declared: dom_w[d["id"]] = d["weight_pct"]
    for m in t["modules"]:
        md = None
        if not declared and m.get("exam_domain") is not None:
            md = f"dom{m['id'][3:]}"; dom_w[md] = m["exam_weight_pct"]
        for s in m["skills"]:
            d = s.get("exam_domain") if declared else md
            if declared and "exam_domain" not in s and f"dom{m['id'][3:]}" in dom_w:
                d = f"dom{m['id'][3:]}"  # track42: módulo = dominio por nombre; el campo falta en tracks.json
            if d: dom_sk[d].append(s["id"]); names[s["id"]] = (s["name_es"], s["name_en"], m["id"])
    per_dom = split(total, dom_w)
    per_sk = {}
    for d, n in per_dom.items():
        sks = dom_sk[d]
        if not sks: sys.exit(f"{t['id']} {d} sin skills")
        per_sk.update(split(n, {s: 1 for s in sks}))
    out[t["id"]] = {"code": t["certification"]["code"], "L": L, "total": total, "per_domain": per_dom,
                    "skills": {s: {"n": n, "name_es": names[s][0], "name_en": names[s][1], "module": names[s][2],
                               "domain": next(d for d, l in dom_sk.items() if s in l)} for s, n in per_sk.items() if n}}
    print(t["id"], out[t["id"]]["code"], "total", total, "dominios", per_dom, "skills con hueco", len(out[t["id"]]["skills"]), "max/skill", max(per_sk.values()))
json.dump(out, open("alloc.json", "w"), ensure_ascii=False, indent=1)
print("TOTAL", sum(v["total"] for v in out.values()))
