"""Tras integ3724 --write: quita las preguntas que las guardas de tests/content rechazan y
ordena cada fichero por hash del id (el orden por slot heredaba la rotación 0-1-2-3 de la clave)."""
import glob, hashlib, json, sys
WT = sys.argv[1]
DROP = {"q110205_r010": "voz_de_asistente (falso positivo: «como modelo de lenguaje»)",
        "q110202_r001": "final de relleno en una opción incorrecta (EN)"}
for f in sorted(glob.glob(f"{WT}/content/questions/*/reservadas_*.json")):
    d = json.load(open(f)); n = len(d["questions"])
    d["questions"] = sorted((q for q in d["questions"] if q["id"] not in DROP), key=lambda q: hashlib.sha256(q["id"].encode()).hexdigest())
    open(f, "w").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    if n != len(d["questions"]): print("quitadas", n - len(d["questions"]), f.split("/")[-1])
