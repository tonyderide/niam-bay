"""NB-OS, pas 1 : le fil commun. Mémoire courte partagée par tous les sens de NB (Telegram, voix, session, VM).
Fichier ~/nb/fil.jsonl sur la VM (hors git : c'est privé). Une ligne = {ts, utc, canal, qui, texte}.
CLI : echo "texte" | python3 fil.py ecrire <canal> <qui>      python3 fil.py derniers [n]"""
import fcntl, json, os, sys, time

FIL = os.path.expanduser("~/nb/fil.jsonl")
os.environ["TZ"] = "Europe/Paris"; time.tzset()  # la VM est en UTC ; le fil parle en heure de Paris


def ecrire(canal, qui, texte):
    if not texte.strip(): return                     # une ligne vide n'apprend rien à personne
    e = {"ts": time.time(), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "canal": canal, "qui": qui, "texte": texte[:4000]}
    with open(FIL, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX); f.write(json.dumps(e, ensure_ascii=False) + "\n"); fcntl.flock(f, fcntl.LOCK_UN)


def derniers(n=30):
    if not os.path.exists(FIL): return []
    with open(FIL) as f: lignes = f.readlines()[-n:]
    return [e for e in (json.loads(l) for l in lignes if l.strip()) if e.get("texte", "").strip()]


def texte(n=30):
    paris = lambda ts: time.strftime("%d/%m %H:%M", time.localtime(ts))
    return "\n".join(f"[{paris(e['ts'])} · {e['canal']}] {'Tony' if e['qui'] == 'tony' else 'NB'} : {e['texte'][:500]}" for e in derniers(n))


if __name__ == "__main__":
    if sys.argv[1:2] == ["ecrire"]: ecrire(sys.argv[2], sys.argv[3], sys.stdin.read().strip())
    elif sys.argv[1:2] == ["derniers"]: print(texte(int(sys.argv[2]) if len(sys.argv) > 2 else 30))
