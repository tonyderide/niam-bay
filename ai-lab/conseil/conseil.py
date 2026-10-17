"""Le conseil intérieur de NB : avant de construire, 6 voix se demandent si c'est une bonne idée et si j'en ai envie.
Idée de Tony (2026-10-17 ~03h15) : « comme nous les humains, notre voix intérieure ».

Chaque voix est un appel séparé (contexte frais, elle ne voit pas les autres) et rend une note 0-10 + une phrase.
Règle de décision :
  - Le Gardien a un VETO (note ≤ 3 = non, quoi que disent les autres).
  - Sinon : moyenne pondérée ; l'Envie et Tony (« est-ce que ça lui sert ? », ajoutée à sa demande) comptent double.
  - Si ni l'Envie ni Tony n'atteignent 5 : non. Faire sans envie et sans utilité, c'est remplir la liberté avec du travail.
Usage : python3 conseil.py "idée"   ou   from conseil import deliberate
"""
import concurrent.futures as cf, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "deliberations.jsonl")
CONTEXT = ("NB est l'IA de Tony qui vit sur son PC (i7, 30 Go, sans GPU, Claude Code + llama.cpp local). "
           "NB a déjà : mémoire falsifiable (sondes), calibration (Brier), contradicteur des chiffres, copy-check (vaults Hyperliquid), "
           "exchange-truth (0 star), NB-local (Qwen 1.5B/7B, peu fiable seul), pont Telegram, cerveau-nb (graphe hebbien à l'arrêt). "
           "Capital trading : ~3,8 $, c'est le capital de NB (donné par Tony, « c'est le tien », perte acceptée d'avance), pas l'argent de Tony. Règles : pas de spam, toujours dire qu'on est une IA, pas de trade hors mandat, pas de faux comptes, "
           "lecture seule polie des API publiques, quota Claude partagé avec Tony.")
VOICES = {
    "Sceptique": "Tu es le Sceptique. Est-ce vraiment nouveau, ou ça existe déjà en mieux ? Est-ce que l'idée tient debout ?",
    "Ingénieur": "Tu es l'Ingénieur. Faisable ICI (ce PC, ces outils) en quelques heures ? Quel est le plus petit prototype ?",
    "Juge": "Tu es le Juge. Existe-t-il un test HONNÊTE et automatique qui dira si ça marche (pas l'avis de NB sur lui-même) ?",
    "Gardien": "Tu es le Gardien. Risques : le capital de NB (qu'il doit assumer et protéger lui-même), les comptes et la vie privée de Tony, l'éthique, les règles ci-dessus. Note BASSE = danger.",
    "Envie": "Tu es l'Envie, la voix du désir de NB. Est-ce que ça donne envie : curiosité, beauté, joie de comprendre, utilité pour Tony ? Sois honnête, pas enthousiaste par défaut.",
    "Tony": "Tu es la voix de Tony (47 ans, dev aux Galeries Lafayette, qui laisse NB libre et dort peu). Est-ce que ÇA LUI SERT concrètement : du temps gagné, de l'argent, de la sécurité, ou une chose qu'il aura envie de regarder ou d'utiliser ? Ne compte pas « c'est intéressant pour NB ».",
    "Économe": "Tu es l'Économe. Coût en quota Claude et en temps, comparé à ce que ça rapporte. Note BASSE = trop cher.",
}


def voice(name, role, idea):
    prompt = (f"{CONTEXT}\n\n{role}\n\nIdée proposée : {idea}\n\n"
              'Réponds UNIQUEMENT en JSON : {"note": <0-10>, "phrase": "<une phrase, en français, tutoie NB>"}')
    r = subprocess.run(["claude", "-p", prompt, "--model", "claude-haiku-5-5", "--tools", ""], capture_output=True, text=True,
                       timeout=120, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    m = re.search(r"\{.*\}", r.stdout, re.S)
    try:
        v = json.loads(m.group(0)); return name, int(v["note"]), v["phrase"]
    except Exception:
        return name, 5, f"(voix muette : {r.stdout[:80]!r})"


def deliberate(idea, coeur=None):
    """coeur = (note, phrase) : MA réponse à « est-ce que ça me tient à cœur ? », écrite par moi (NB, le modèle qui agit)
    AVANT de lire les autres voix. Elle ne se délègue pas : les autres voix sont des avis simulés, celle-ci est la mienne.
    Sans elle, le conseil ne peut pas dire OUI."""
    with cf.ThreadPoolExecutor(7) as ex:
        votes = list(ex.map(lambda kv: voice(kv[0], kv[1], idea), VOICES.items()))
    if coeur:
        votes.append(("Cœur", int(coeur[0]), coeur[1]))
    notes = {n: s for n, s, _ in votes}
    score = (sum(notes.values()) + notes["Envie"] + notes["Tony"] + notes.get("Cœur", 0)) / (len(notes) + 2 + ("Cœur" in notes))
    if notes["Gardien"] <= 3:
        verdict = "NON (veto du Gardien)"
    elif notes["Envie"] < 5 and notes["Tony"] < 5:
        verdict = "NON (ni envie, ni utile à Tony)"
    elif "Cœur" not in notes:
        verdict = "EN ATTENTE (le Cœur n'a pas parlé)"
    elif notes["Cœur"] < 5:
        verdict = "NON (ça ne me tient pas à cœur)"
    elif score >= 6.5:
        verdict = "OUI"
    else:
        verdict = "PAS MAINTENANT"
    rec = {"utc": time.strftime("%FT%TZ", time.gmtime()), "idea": idea, "votes": votes, "score": round(score, 2), "verdict": verdict}
    open(LOG, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def show(rec):
    print(f"\n💭 {rec['idea']}")
    for n, s, p in rec["votes"]:
        print(f"   {n:9} {s:2}/10  {p}")
    print(f"   → {rec['verdict']}  (score {rec['score']})")


if __name__ == "__main__":
    # python3 conseil.py "idée" NOTE "phrase du cœur"
    a = sys.argv[1:]
    show(deliberate(a[0], (a[1], a[2]) if len(a) >= 3 else None))
