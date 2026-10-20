"""/banc sur Telegram : une stratégie en français -> spec JSON montrée à Tony -> /banc ok -> figée (commit) -> verdict.
Le moteur, c'est ai-lab/banc-honnete/banc.py. La traduction est faite par Claude, puis vérifiée par un essai à sec du moteur."""
import json, os, re, subprocess, sys, threading, time

REPO = os.path.expanduser("~/projets/tonyderide/niam-bay")
BANC = os.path.join(REPO, "ai-lab/banc-honnete")
PENDING = os.path.expanduser("~/.local/state/nb/banc_pending.json")
sys.path.insert(0, BANC)
import banc  # noqa: E402

PROMPT = """Traduis cette stratégie de trading en spec JSON pour le moteur ci-dessous. Réponds UNIQUEMENT par le JSON.
Si une partie n'est pas exprimable, choisis l'équivalent le plus fidèle et explique-le dans "notes" (une phrase, en français).
Champs : "nom" (court), "tf" (un de 5m 15m 30m 1h 4h 12h 1d ; 1h si non précisé), "long" (expression ou null),
"short" (expression ou null), "sortie" (objet : sl, tp en fraction, max_bougies, inverse), "notes".
Documentation du moteur :
{doc}
Stratégie de Tony : {texte}"""


def _claude(prompt):
    r = subprocess.run(["claude", "-p", prompt, "--model", "claude-sonnet-5-5", "--tools", ""], capture_output=True, text=True,
                       timeout=180, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    m = re.search(r"\{.*\}", r.stdout, re.S)
    return json.loads(m.group(0))


def _essai_a_sec(spec):
    """Évalue les expressions sur 300 fausses bougies : attrape les fautes avant de figer."""
    if spec.get("tf") not in banc.STEP: raise ValueError(f"unité de temps inconnue : {spec.get('tf')}")
    if not (spec.get("long") or spec.get("short")): raise ValueError("ni long ni short")
    T = [1700000000 + 3600 * i for i in range(300)]
    C = [(100 + i % 7, 103 + i % 7, 98 + i % 7, 101 + (i * 3) % 5, 10.0) for i in range(300)]
    ns = banc.namespace(T, C)
    for k in ("long", "short"):
        if spec.get(k): eval(spec[k], {"__builtins__": {}}, ns)


def lisible(spec):
    so = spec.get("sortie", {}); s = []
    if so.get("sl"): s.append(f"SL {so['sl'] * 100:g} %")
    if so.get("tp"): s.append(f"TP {so['tp'] * 100:g} %")
    if so.get("max_bougies"): s.append(f"max {so['max_bougies']} bougies")
    if so.get("inverse") or not s: s.append("sortie sur signal opposé")
    return (f"🧪 {spec['nom']} — bougies {spec['tf']}\n"
            f"Long : {spec.get('long') or '—'}\nShort : {spec.get('short') or '—'}\nSortie : {', '.join(s)}\n"
            + (f"Note : {spec['notes']}\n" if spec.get("notes") else "")
            + "\nC'est bien ça ? Réponds /banc ok pour figer et lancer (≈ 2 à 10 min), ou renvoie /banc avec une correction.")


def proposer(texte):
    if not texte.strip():
        return "Écris ta stratégie après /banc, par ex. : /banc long quand le RSI 14 passe sous 30 et que le prix est au-dessus de l'EMA200, SL 1 %, TP 2 %"
    try:
        spec = _claude(PROMPT.format(doc=banc.__doc__, texte=texte)); _essai_a_sec(spec)
    except Exception as e:
        return f"Je n'ai pas réussi à traduire proprement ({str(e)[:120]}). Reformule plus simplement ?"
    spec["texte_tony"] = texte
    os.makedirs(os.path.dirname(PENDING), exist_ok=True); json.dump(spec, open(PENDING, "w"), ensure_ascii=False, indent=1)
    return lisible(spec)


def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, timeout=120)


def lancer(send):
    if not os.path.exists(PENDING): return "Rien en attente : envoie d'abord /banc <ta stratégie>."
    spec = json.load(open(PENDING)); os.remove(PENDING)
    slug = time.strftime("%Y%m%d-%H%M") + "-" + re.sub(r"[^a-z0-9]+", "-", spec["nom"].lower()).strip("-")[:40]
    f = os.path.join(BANC, "specs", slug + ".json"); json.dump(spec, open(f, "w"), ensure_ascii=False, indent=1)
    _git("add", f); c = _git("commit", "-qm", f"banc: spec figée {slug} (avant calcul)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    _git("push", "-q")
    figé = "figées dans un commit" if c.returncode == 0 else "⚠️ commit raté, test lancé quand même"

    def job():
        try:
            out = banc.banc(spec)
        except Exception as e:
            out = f"Le moteur a planté : {str(e)[:200]}"
        open(f.replace(".json", ".resultat.txt"), "w").write(out + "\n")
        _git("add", f.replace(".json", ".resultat.txt")); _git("commit", "-qm", f"banc: résultat {slug}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"); _git("push", "-q")
        send("🧾 Verdict du banc\n" + out.replace(" || ", "\n   ").replace(" | ", "\n   "))
    threading.Thread(target=job, daemon=True).start()
    return f"🔒 Règles {figé} ({slug}). Je teste sur 2024-2025 puis 2026, frais et hasard compris ; je reviens avec le verdict."
