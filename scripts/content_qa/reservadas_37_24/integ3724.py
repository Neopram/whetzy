"""37.24: integra las reservadas de simulacro (pool "simulacro") desde los resultados del Workflow.

final = corregida si hubo corrector (descartada => fuera); la original si la revisión salió limpia.
Comprueba a máquina, contra chunk/<bloque>.json y frag/<id>.txt:
  slot del bloque, fragment_id y correct_index iguales a los asignados; cita literal dentro
  del fragmento; 4 + 4 opciones; ningún campo publicado copia > 8 palabras seguidas del
  fragmento; correcta no estrictamente la más larga (aviso, con lista).
Escribe content/questions/<dir del track>/reservadas_<módulo>.json.
Uso: python3 integ3724.py <worktree> <salida_wf.json> [<salida_wf.json> ...] [--write]
"""
import collections, glob, json, os, re, sys

RES = os.path.dirname(os.path.abspath(__file__))
WT = sys.argv[1]; WRITE = "--write" in sys.argv; SKIP_LONGEST = "--skip-longest" in sys.argv
outs = [a for a in sys.argv[2:] if not a.startswith("--")]
OVR = json.load(open(f"{RES}/overrides3724.json")) if os.path.exists(f"{RES}/overrides3724.json") else {}

T = json.load(open(f"{WT}/content/curriculum/tracks.json")); T = T if isinstance(T, list) else T.get("tracks", T)
T = list(T.values()) if isinstance(T, dict) else T
mod_of = {s["id"]: m["id"] for t in T for m in t.get("modules", []) for s in m["skills"]}
chunks = {c["id"]: c for c in json.load(open(f"{RES}/chunks.json"))}
by_sk = collections.defaultdict(list)
for c in chunks.values(): by_sk[c["sk"]].append(c)

norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[*_`#>¶]", "", s or "")).strip().lower()
def toks(s): return re.findall(r"[a-záéíóúñü0-9]+", (s or "").lower())
def copy8(field, grams):
    w = toks(field)
    return any(" ".join(w[i:i + 9]) in grams for i in range(len(w) - 8))
def frag(fid):
    p = f"{RES}/frag/{fid}.txt"
    if not os.path.exists(p): return None
    raw = open(p).read(); hdr, _, body = raw.partition("\ntext:\n")
    h = dict(l.split(": ", 1) for l in hdr.strip().split("\n") if ": " in l)
    return {**h, "text": body}
def source(fr):
    u, t = fr["url"], fr["title"]
    if "docs.aws.amazon.com" in u: return f"AWS — {t} ({u})"
    if "docs.python.org" in u: return f"Python documentation — {t} ({u}) — PSF-2.0"
    if "nist.gov" in u: return f"NIST {t}, {fr.get('heading', '')} ({u}) — obra del Gobierno de EE. UU., dominio público"
    if "rfc-editor.org" in u: return f"IETF — {t} ({u})"
    if "isc2.org" in u: return f"ISC2 — Code of Ethics ({u})"
    raise SystemExit(f"fuente sin formato: {u}")

results = [r for o in outs for r in json.load(open(o))["result"]]
finals, problems, longest = [], [], []
seen = set()
for r in results:
    sk, q = r["sk"], r["q"]
    co = r.get("corrected"); rv = r.get("review")
    if co:
        if co.get("discard"): problems.append(("descartada", sk, q["slot"], co.get("reason", "")[:90])); continue
        fin = co["question"]
    elif rv is not None and not rv.get("defects"): fin = q
    else: problems.append(("sin final", sk, q["slot"])); continue
    # ¿qué bloque y slot? el fragment_id asignado identifica el bloque
    cand = [c for c in by_sk[sk] for s in c["slots"] if s["slot"] == fin["slot"] and s["fragment_id"] == fin["fragment_id"]]
    if len(cand) != 1: problems.append(("slot/fragmento no asignado", sk, fin["slot"], fin["fragment_id"])); continue
    c = cand[0]; slot = next(s for s in c["slots"] if s["slot"] == fin["slot"])
    key = f"{sk}|{fin['slot']}"
    if key in seen: problems.append(("slot repetido", key)); continue
    seen.add(key)
    ov = OVR.get(key, {})
    if ov:
        fin = json.loads(json.dumps(fin))
        for k, v in ov.items():
            m = re.match(r"(options_(?:es|en))\[(\d)\]$", k)
            if m: fin[m.group(1)][int(m.group(2))] = v
            else: fin[k] = v
    if fin["correct_index"] != slot["correct_index"]: problems.append(("índice cambiado", key)); continue
    fr = frag(fin["fragment_id"])
    if not fr: problems.append(("fragmento inexistente", key)); continue
    src = norm(fr["text"])
    sents = [s for s in re.split(r"(?<=[.!?])\s+", norm(fin["fragment"])) if len(s) > 25]
    miss = [s for s in sents if s.rstrip(".") not in src]
    if not sents or miss: problems.append(("cita no literal", key, (miss or [fin["fragment"]])[0][:90])); continue
    ci = fin["correct_index"]
    if not (len(fin["options_es"]) == len(fin["options_en"]) == 4 and 0 <= ci < 4): problems.append(("opciones/índice", key)); continue
    st = toks(fr["text"]); grams = {" ".join(st[i:i + 9]) for i in range(len(st) - 8)}
    bad = [k for k in ("question_es", "question_en", "explanation_es", "explanation_en") if copy8(fin[k], grams)]
    bad += [f"options_{l}" for l in ("es", "en") if any(copy8(o, grams) for o in fin[f"options_{l}"])]
    if bad: problems.append(("copia > 8 palabras", key, bad)); continue
    for lang in ("es", "en"):
        L = [len(o) for o in fin[f"options_{lang}"]]
        if L[ci] > max(l for i, l in enumerate(L) if i != ci): longest.append((key, lang, L, ci))
    if SKIP_LONGEST and longest and longest[-1][0] == key:
        problems.append(("correcta más larga (fuera)", key)); continue
    finals.append((c["track"], sk, fin, fr))

per = collections.Counter(t for t, *_ in finals)
print("finales:", sum(per.values()), dict(sorted(per.items())), "| problemas:", len(problems), "| correcta más larga:", len(longest))
for p in problems: print("  ", p)
for l in longest: print("   LARGA", l)
print("posición correcta:", dict(collections.Counter(f["correct_index"] for _, _, f, _ in finals)))
if not WRITE: sys.exit(1 if (problems or longest) else 0)
if longest and not SKIP_LONGEST: sys.exit("no escribo con correctas más largas: arréglalas en overrides3724.json")

def qs_of(d): return d if isinstance(d, list) else d.get("questions", [])
def track_dir(t, sk):
    best, n = None, -1
    for d in glob.glob(f"{WT}/content/questions/{t}_*"):
        k = sum(1 for f in glob.glob(f"{d}/*.json") for q in qs_of(json.load(open(f))) if q["skill_id"] == sk)
        if k > n: best, n = d, k
    return best
files, nxt = {}, collections.Counter()
for t, sk, fin, fr in sorted(finals, key=lambda x: (x[1], x[2]["slot"])):
    path = f"{track_dir(t, sk)}/reservadas_{mod_of[sk]}.json"
    files.setdefault(path, {"questions": []})
    nxt[sk] += 1
    files[path]["questions"].append({
        "id": f"q{sk[2:]}_r{nxt[sk]:03d}", "skill_id": sk, "type": "multiple_choice", "pool": "simulacro",
        "question_es": fin["question_es"], "question_en": fin["question_en"],
        "options_es": fin["options_es"], "options_en": fin["options_en"],
        "correct_index": fin["correct_index"],
        "explanation_es": fin["explanation_es"], "explanation_en": fin["explanation_en"],
        "source": source(fr)})
for f, x in files.items():
    if os.path.exists(f): raise SystemExit(f"ya existe {f}")
    open(f, "w").write(json.dumps(x, ensure_ascii=False, indent=2) + "\n")
print("escritos:", len(files), "ficheros")
