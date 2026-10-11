"""Reparte cada skill en bloques de fragmentos disjuntos (≤ 6 preguntas por bloque); índice correcto rotado."""
import json, glob, collections
A = json.load(open("alloc.json")); chunks = []
for t, info in A.items():
    for k, (sk, v) in enumerate(info["skills"].items()):
        p = json.load(open(f"pack/{sk}.json")); F = len(p["fragments"]); n = v["n"]
        slots = [{"slot": i + 1, "fragment_id": p["fragments"][i % F]["id"], "correct_index": (i + k) % 4} for i in range(n)]
        byf = collections.OrderedDict()
        for s in slots: byf.setdefault(s["fragment_id"], []).append(s)
        cur = []
        for fid, ss in byf.items():
            if cur and len(cur) + len(ss) > 6: chunks.append(cur); cur = []
            cur += ss
        if cur: chunks.append(cur)
        for c in chunks:
            if isinstance(c, list): pass
        # anota metadatos en los bloques nuevos de esta skill
        for j in range(len(chunks)):
            if isinstance(chunks[j], list):
                chunks[j] = {"id": f"{sk}-b{j}", "sk": sk, "track": t, "code": info["code"], "name_en": v["name_en"], "slots": chunks[j]}
json.dump(chunks, open("chunks.json", "w"), ensure_ascii=False)
c = collections.Counter(x["track"] for x in chunks)
print("bloques", len(chunks), dict(c), "preguntas", sum(len(x["slots"]) for x in chunks), "max/bloque", max(len(x["slots"]) for x in chunks))
