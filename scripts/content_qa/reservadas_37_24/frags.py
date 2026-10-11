"""37.24: fragmentos literales por skill desde fuentes oficiales y paquetes por skill.

Fuentes: urls_existing.json (track08/09/41), urls_aws.json (track10/11),
urls_nist.json (track40/42, PDF) y prod43/frag (track43, ya descargado).
Salida: frag/<id>.txt (cabecera title/url/heading + "text:") y pack/<sk>.json
con los fragmentos más afines a la skill (solapamiento de palabras con su nombre
y con los enunciados de práctica existentes).
"""
import glob, html, json, os, re, subprocess, sys, collections

SP = os.path.dirname(os.path.abspath(__file__))
REPO = sys.argv[1]
PDFPY = sys.argv[2]  # intérprete con pypdf
A = json.load(open(f"{SP}/alloc.json"))
os.makedirs(f"{SP}/cache", exist_ok=True); os.makedirs(f"{SP}/frag", exist_ok=True); os.makedirs(f"{SP}/pack", exist_ok=True)


def fetch(url, ext):
    f = f"{SP}/cache/" + re.sub(r"[^A-Za-z0-9]+", "_", url)[:180] + ext
    if not os.path.exists(f):
        r = subprocess.run(["curl", "-s", "-L", "--max-time", "90", "-o", f, "-w", "%{http_code}", url], capture_output=True, text=True)
        if r.stdout.strip() != "200":
            if os.path.exists(f): os.remove(f)
            return None
    return f


def text(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r"<pre[^>]*>.*?</pre>", " ", h, flags=re.S)
    h = re.sub(r"</(p|li|h\d|tr|div|dt|dd)>", "\n", h)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return "\n".join(re.sub(r"[ \t]+", " ", l).strip() for l in t.split("\n") if l.strip())


def chunks(t, size=400, maxw=550):
    w = t.split()
    if len(w) < 35: return []
    return [t] if len(w) <= maxw else [" ".join(w[i:i + size]) for i in range(0, len(w), size)]


def txt_frags(url, title):
    f = fetch(url, ".txt")
    if not f: return None
    raw = open(f, encoding="utf-8", errors="ignore").read()
    raw = re.sub(r"\f|\n[^\n]*\[Page \d+\]\n|\nRFC \d+ [^\n]*\n", "\n", raw)
    paras = [re.sub(r"\s+", " ", x).strip() for x in re.split(r"\n\s*\n", raw)]
    out, buf = [], []
    for x in paras:
        if len(x.split()) < 8: continue
        buf.append(x)
        if sum(len(y.split()) for y in buf) >= 300:
            out.append({"title": title, "url": url, "heading": buf[0][:80], "text": "\n".join(buf)}); buf = []
    return out


def generic_frags(url, title):
    f = fetch(url, ".html")
    if not f: return None
    t = open(f, encoding="utf-8", errors="ignore").read()
    m = re.search(r"<main[^>]*>(.*?)</main>", t, re.S)
    body = text(m.group(1) if m else t)
    return [{"title": title, "url": url, "heading": "main", "text": c} for c in chunks(body)]


def html_frags(url):
    f = fetch(url, ".html")
    if not f: return None
    t = open(f, encoding="utf-8", errors="ignore").read()
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    title = re.sub(r"\s+", " ", html.unescape(m.group(1))).split(" - ")[0].split(" — ")[0].strip() if m else url
    if "docs.aws.amazon.com" in url:
        m = re.search(r'<div id="main-col-body">(.*?)<div id="(?:main-col-footer|js_error_message)', t, re.S)
        split_re = r"(<h2[^>]*>.*?</h2>)"
    else:  # docs.python.org
        m = re.search(r'<div class="body" role="main">(.*?)<div class="sphinxsidebar"', t, re.S) or re.search(r'role="main">(.*?)<footer', t, re.S)
        split_re = r"(<h[23][^>]*>.*?</h[23]>)"
    if not m: return None
    parts = re.split(split_re, m.group(1), flags=re.S)
    secs = [("intro", parts[0])] + [(text(parts[i]).replace("¶", "").strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    out = []
    for hd, b in secs:
        for c in chunks(text(b)):
            out.append({"title": title, "url": url, "heading": hd[:160], "text": c})
    return out


PDFTXT = r'''
import sys, pypdf, json
r = pypdf.PdfReader(sys.argv[1]); out = []
for i, p in enumerate(r.pages):
    try: out.append((i + 1, p.extract_text() or ""))
    except Exception: out.append((i + 1, ""))
json.dump(out, open(sys.argv[2], "w"))
'''


def pdf_frags(url, pub):
    f = fetch(url, ".pdf")
    if not f: return None
    j = f + ".json"
    if not os.path.exists(j):
        open(f"{SP}/pdftxt.py", "w").write(PDFTXT)
        subprocess.run([PDFPY, "-I", f"{SP}/pdftxt.py", f, j], check=True)
    pages = json.load(open(j))
    out, buf, start = [], [], None
    for n, t in pages:
        # fuera índices, glosarios de siglas y páginas casi vacías
        if len(t.split()) < 80 or re.search(r"\.{8,}", t): continue
        t = re.sub(r"-\n(\w)", r"\1", t)
        paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n|(?<=[.:])\n(?=[A-Z•])", t)]
        for p in paras:
            if len(p.split()) < 8 or "This publication is available free of charge" in p: continue
            if start is None: start = n
            buf.append(p)
            if sum(len(x.split()) for x in buf) >= 300:
                out.append({"title": pub, "url": url, "heading": f"p. {start}", "text": "\n".join(buf)}); buf, start = [], None
    if buf and sum(len(x.split()) for x in buf) >= 60:
        out.append({"title": pub, "url": url, "heading": f"p. {start}", "text": "\n".join(buf)})
    return out


STOP = set("the a an of and or to in for on with by is are be as at from that this which what how when it its your you can use using used into about not".split())
def words(s): return {w for w in re.findall(r"[a-z][a-z0-9\-]{2,}", s.lower()) if w not in STOP}


existing = collections.defaultdict(list)
for f in glob.glob(f"{REPO}/content/questions/track*/*.json"):
    d = json.load(open(f)); qs = d if isinstance(d, list) else d.get("questions", [])
    for q in qs: existing[q["skill_id"]].append(q.get("question_en", ""))

urlmaps = {}
for name in ("urls_existing.json", "urls_aws.json"):
    if os.path.exists(f"{SP}/{name}"): urlmaps.update(json.load(open(f"{SP}/{name}")))
nist = json.load(open(f"{SP}/urls_nist.json")) if os.path.exists(f"{SP}/urls_nist.json") else {}
other = json.load(open(f"{SP}/urls_other.json")) if os.path.exists(f"{SP}/urls_other.json") else {}
only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None

cache, bad, report = {}, [], {}
for t, info in A.items():
    if only and t not in only: continue
    for sk, v in info["skills"].items():
        cand = []
        if t == "track43":
            for p in sorted(glob.glob(f"{SP}/../prod43/frag/{sk}-*.txt")):
                raw = open(p).read(); hdr, _, body = raw.partition("\ntext:\n")
                h = dict(l.split(": ", 1) for l in hdr.strip().split("\n") if ": " in l)
                cand.append({"title": h.get("title", ""), "url": h.get("url", ""), "heading": h.get("heading", ""), "text": body.strip()})
        if sk in other:
            for e in other[sk]:
                k = e["url"]
                if k not in cache: cache[k] = txt_frags(k, e["pub"]) if k.endswith(".txt") else generic_frags(k, e["pub"])
                if cache[k] is None: bad.append(k)
                else: cand += cache[k]
        if t == "track43": pass
        elif sk in nist:
            for e in nist[sk]:
                k = e["url"]
                if k not in cache: cache[k] = pdf_frags(e["url"], e["pub"])
                if cache[k] is None: bad.append(k)
                else: cand += cache[k]
        else:
            for u in urlmaps.get(sk, []):
                if u not in cache: cache[u] = html_frags(u)
                if cache[u] is None: bad.append(u)
                else: cand += cache[u]
        key = words(v["name_en"]) | words(" ".join(existing[sk]))
        name = words(v["name_en"])
        scored = sorted(cand, key=lambda c: -(3 * len(name & words(c["text"])) + len(key & words(c["text"]))))
        k = min(len(scored), max(8, 3 * v["n"]), 30)
        pack = []
        for i, c in enumerate(scored[:k]):
            fid = f"{sk}-r{i}"
            open(f"{SP}/frag/{fid}.txt", "w").write(f"title: {c['title']}\nurl: {c['url']}\nheading: {c['heading']}\n\ntext:\n{c['text']}\n")
            pack.append({"id": fid, **c})
        json.dump({"skill": sk, "track": t, "code": info["code"], "name_es": v["name_es"], "name_en": v["name_en"],
                   "n": v["n"], "existing": existing[sk], "fragments": pack}, open(f"{SP}/pack/{sk}.json", "w"), ensure_ascii=False, indent=1)
        report[sk] = (t, v["n"], len(cand), len(pack))
for sk, (t, n, c, p) in report.items():
    if p < max(4, n) or c == 0: print("POCO", t, sk, "n", n, "candidatos", c, "pack", p)
print("skills:", len(report), "fallidas:", sorted(set(bad)))
print("por track:", dict(collections.Counter(t for t, *_ in report.values())))
