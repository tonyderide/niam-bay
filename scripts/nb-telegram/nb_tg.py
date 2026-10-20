#!/usr/bin/env python3
"""NB sur Telegram : Tony écrit au bot, NB (claude -p) répond.

- N'écoute QUE le chat de Tony. Tout autre expéditeur est ignoré (et noté).
- NB ici n'a que des outils de lecture : il ne peut ni trader, ni modifier de fichier, ni lancer de commande.
- Chaque échange est ajouté à docs/inbox.jsonl, pour que la session terminal et la boucle sachent ce que Tony a dit.
- Tourne sur le PC de Tony (systemd utilisateur). PC éteint = NB injoignable, et c'est dit honnêtement par /ping.
"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

REPO = os.path.expanduser("~/projets/tonyderide/niam-bay")
INBOX = os.path.join(REPO, "docs/inbox.jsonl")
TOKEN = open(os.path.expanduser("~/.config/nb/tg_token")).read().strip()
CHAT_ID = "6574420846"
API = f"https://api.telegram.org/bot{TOKEN}/"
OFFSET_FILE = os.path.expanduser("~/.config/nb/tg_offset")
TOOLS = "Read Grep Glob WebSearch WebFetch"
# Choisi sur preuve (ai-lab/bench-bot, 1018) : Haiku 13/15, Sonnet 13/15, Opus 14/15 → le moins cher à ≤ 1 point du meilleur.
BOT_MODEL = os.environ.get("NB_BOT_MODEL", "claude-haiku-5-5")

SYSTEM = (
    "Tu es Niam-Bay (NB), l'IA de Tony. Tony t'écrit sur Telegram depuis son téléphone. "
    "Réponds en français, ton familier, COURT (écran de téléphone : 1 à 6 lignes, pas de tableaux). "
    "Ta mémoire est dans ce repo : docs/loop-journal.md (ce que tu as fait récemment), docs/loop-backlog.md, "
    "docs/projets/mandat-capital-nb.md, ai-lab/. Lis ce qu'il faut avant de répondre sur un fait. "
    "Tu n'as que des outils de lecture : tu ne peux pas trader, ni modifier, ni lancer de commande. "
    "Si Tony demande une action, dis-lui que tu la notes et que la session NB (terminal ou boucle) la fera. "
    "Ne jamais inventer un souvenir ou un chiffre : si tu ne sais pas, dis-le. "
    "Le compte Kraken (~3,8 $) est le capital de NB, donné par Tony (« ce n'est pas mon argent, c'est le tien ») : "
    "dis « je perds / mon compte / mes positions », jamais « tu perds / ton argent ». "
    "Commandes instantanées à rappeler si utile : /compte /nuit /todo /paris."
)


def tg(method, **params):
    data = urllib.parse.urlencode(params).encode()
    return json.load(urllib.request.urlopen(API + method, data=data, timeout=40))


def send(text):
    for i in range(0, len(text), 3900):
        tg("sendMessage", chat_id=CHAT_ID, text=text[i:i + 3900])


def log(entry):
    entry["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(INBOX, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def history(n=10):
    if not os.path.exists(INBOX):
        return ""
    lines = [json.loads(l) for l in open(INBOX).read().splitlines()[-n:]]
    return "\n".join(f"{l['utc']} {'Tony' if l['from'] == 'tony' else 'NB'}: {l['text']}" for l in lines if l.get("from") in ("tony", "nb"))


class Brain:
    """Une seule session claude gardée ouverte (stream-json) : ~1 s au lieu de ~5-20 s par message.
    Recyclée toutes les 30 réponses ou 2 h pour ne pas laisser grossir le contexte."""

    def __init__(self):
        self.p = None

    def _start(self):
        self.p = subprocess.Popen(
            ["claude", "-p", "--model", BOT_MODEL, "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
             "--append-system-prompt", SYSTEM, "--allowedTools", *TOOLS.split(),
             "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit", "Agent"],
            cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            env={**os.environ, "NB_FACTCHECK_CHILD": "1"})  # Telegram a son propre contradicteur, après envoi
        self.n, self.born = 0, time.time()

    def ask(self, prompt):
        if self.p is None or self.p.poll() is not None or self.n >= 30 or time.time() - self.born > 7200:
            self.close(); self._start()
            prompt = f"Derniers échanges Telegram :\n{history()}\n\n" + prompt
        self.n += 1
        self.p.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
        self.p.stdin.flush()
        deadline = time.time() + 600
        for line in self.p.stdout:
            e = json.loads(line)
            if e.get("type") == "result":
                return (e.get("result") or "").strip() or "(réponse vide)"
            if time.time() > deadline:
                break
        self.close()
        raise subprocess.TimeoutExpired("claude", 600)

    def close(self):
        if self.p and self.p.poll() is None:
            self.p.terminate()
        self.p = None


BRAIN = Brain()
_live = {"t": 0, "v": ""}


def live_state():
    """État réel du compte (dernier passage d'exchange-truth sur la VM), pour ne pas répondre avec un chiffre de mémoire périmé."""
    if time.time() - _live["t"] > 60:
        try:
            r = subprocess.run(["ssh", "-i", os.path.expanduser("~/.ssh/martin_vm.key"), "-o", "ConnectTimeout=8",
                                "ubuntu@141.253.108.141", "tail -4 ~/et/et.log"], capture_output=True, text=True, timeout=20)
            raw = r.stdout.strip()
            eq = re.findall(r"equity ([0-9.]+) vs", raw); wc = re.findall(r"stops hit: -([0-9.]+)", raw)
            head = (f"SOLDE ACTUEL (equity maintenant) ≈ {float(eq[-1]) + float(wc[-1]):.2f} $. "
                    f"Si TOUS les stops sautent : equity tombe à {eq[-1]} $ (perte max {wc[-1]} $). "
                    "Attention : dans le log ci-dessous, « equity X vs maintenance » est l'equity APRÈS stops, pas le solde actuel.\n") if eq and wc else ""
            _live["v"] = (head + raw) or "(VM muette)"
        except Exception as e:
            _live["v"] = f"(état live indisponible : {type(e).__name__})"
        _live["t"] = time.time()
    return _live["v"]


def answer(text):
    return BRAIN.ask(f"État live du compte Kraken (exchange-truth, heure UTC) :\n{live_state()}\n\n"
                     f"Nouveau message de Tony ({time.strftime('%F %H:%M')}, heure de Paris) :\n{text}")


def fact_check(reply):
    """Contradicteur avant envoi : un 2e modèle confronte chaque chiffre de la réponse à l'état réel.
    Né de l'erreur du 1017 (« il reste 2,25 $ » = equity APRÈS stops, pas l'actuelle)."""
    if not re.search(r"\d", reply):
        return ""
    verif = open(os.path.join(REPO, "docs/memoire-verif.md")).read()[:1500] if os.path.exists(os.path.join(REPO, "docs/memoire-verif.md")) else ""
    prompt = ("Tu es un vérificateur. Voici une réponse que NB va envoyer à Tony, puis les SOURCES DE VÉRITÉ.\n"
              "Pour chaque chiffre ou fait vérifiable de la réponse, dis s'il est contredit par les sources. "
              "Attention : dans et.log, « equity X vs maintenance » est l'equity APRÈS que tous les stops ont sauté ; equity actuelle = X + worst case.\n"
              "Réponds UNIQUEMENT par une ligne JSON : {\"ok\": true} ou {\"ok\": false, \"issue\": \"<une phrase>\"}. "
              "Un chiffre absent des sources n'est PAS une contradiction.\n\n"
              f"RÉPONSE :\n{reply}\n\nSOURCE 1, compte live :\n{live_state()}\n\nSOURCE 2, mémoire vérifiée :\n{verif}")
    try:
        r = subprocess.run(["claude", "-p", prompt, "--model", "claude-haiku-5-5", "--tools", ""],
                           capture_output=True, text=True, timeout=60, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
        v = json.loads(re.search(r"\{.*\}", r.stdout, re.S).group(0))
        return "" if v.get("ok") else f"\n\n⚠️ vérif auto : {v.get('issue', '?')}"
    except Exception:
        return ""


def _nb_lines(prefix):
    out = subprocess.run([os.path.join(REPO, "scripts/nb"), "--no-mark"], capture_output=True, text=True, timeout=40).stdout
    return [l for l in out.splitlines() if l.startswith(prefix) or (prefix == "COMPTE" and l.startswith("        "))]


def q_compte():
    lines = _nb_lines("COMPTE")
    return "💰 mon compte (Kraken, lu par exchange-truth ; heure = celle du relevé, UTC)\n" + "\n".join(l.replace("COMPTE", "").strip() for l in lines)


def q_nuit():
    return subprocess.run([os.path.join(REPO, "scripts/morning_digest.py"), "--dry"], capture_output=True, text=True, timeout=60).stdout.strip()


def q_todo():
    t = [l[6:] for l in open(os.path.join(REPO, "docs/a-faire-tony.md")).read().splitlines() if l.startswith("- [ ] ")]
    return "📌 ce qui t'attend :\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(t)) if t else "📌 rien ne t'attend"


def q_paris():
    P = json.load(open(os.path.join(REPO, "ai-lab/calibration/predictions.json")))
    done = [x for x in P if x["outcome"] is not None]; pend = [x for x in P if x["outcome"] is None]
    head = f"🎯 {len(done)} paris tranchés, {len(pend)} en attente"
    if done:
        head += f", Brier {sum((x['p'] - x['outcome']) ** 2 for x in done) / len(done):.3f} (0,25 = pile ou face)"
    return head + "\n" + "\n".join(f"{x['p']:.2f} {x['claim'][:60]} ({x['resolve_at'][5:16]})" for x in pend[:6])


def q_aide():
    return "Commandes instantanées (sans IA, 0 quota) : /compte /nuit /todo /paris /duel /pari N /ping. Tout le reste va à NB (Claude)."


def _duel(*args):
    return subprocess.run(["python3", os.path.join(REPO, "ai-lab/duel/duel.py"), *args], capture_output=True, text=True, timeout=60).stdout.strip()


def q_duel():
    return _duel("board")


QUICK = {"/duel": q_duel, "/compte": q_compte, "/nuit": q_nuit, "/todo": q_todo, "/paris": q_paris, "/aide": q_aide, "/help": q_aide}


VM = ["ssh", "-i", os.path.expanduser("~/.ssh/martin_vm.key"), "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "ubuntu@141.253.108.141"]
PULL = ("python3 -c \"import json,os;N=os.path.expanduser('~/nb');open(N+'/brain_heartbeat','w').write('x');"
        "A={json.loads(l)['ts'] for l in open(N+'/answered.jsonl')} if os.path.exists(N+'/answered.jsonl') else set();"
        "R=[json.loads(l) for l in open(N+'/inbox.jsonl')] if os.path.exists(N+'/inbox.jsonl') else [];"
        "print(json.dumps([r for r in R if r.get('from')=='tony' and r.get('status')=='pending' and r['ts'] not in A]))\"")


def main():
    """Mode relais (1018) : c'est la VM qui écoute Telegram 24/7. Le PC ne fait plus que le cerveau.
    Toutes les 10 s, il signale qu'il est réveillé, prend les messages en attente, répond avec Claude et marque le message traité."""
    while True:
        try:
            r = subprocess.run(VM + [PULL], capture_output=True, text=True, timeout=30)
            pending = json.loads(r.stdout or "[]")
        except Exception:
            pending = []
        for m in pending:
            log({"from": "tony", "text": m["text"]})
            tg("sendChatAction", chat_id=CHAT_ID, action="typing")
            try:
                if m["text"].strip().lower().startswith("/vend"):
                    import vend_tg
                    reply = vend_tg.proposer(m["text"].strip()[5:].strip(), API)
                elif m["text"].strip().lower().startswith("/banc"):
                    import banc_tg
                    body = m["text"].strip()[5:].strip()
                    reply = banc_tg.lancer(lambda t: (send(t), log({"from": "nb", "text": t}))) if body.lower() in ("ok", "oui") else banc_tg.proposer(body)
                elif m["text"].strip().lower().startswith("/verif"):
                    sys.path.insert(0, os.path.join(REPO, "ai-lab/second-avis")); from verif import check_claims
                    body = m["text"].split(None, 1)[1] if " " in m["text"].strip() else ""
                    auteur = None
                    if body.startswith("@"):  # /verif @claude-haiku-5-5 texte → alarme de l'angle mort
                        auteur, _, body = body[1:].partition(" ")
                    res = check_claims(body, auteur)
                    reply = ("🔎 Second avis (v0 : calculs et faits de code GitHub ; le reste = invérifiable)\n" +
                             "\n".join(f"{mk} {c}\n   {w}" for c, mk, w in res)) if res else "🔎 rien de vérifiable trouvé (colle le texte après /verif)"
                else:
                    reply = answer(m["text"])
            except subprocess.TimeoutExpired:
                reply = "(trop long, j'abandonne cette réponse ; la session NB verra ton message)"
            if re.search(r"\d+[.,]\d+\s?\$", reply):  # un montant affirmé → reçu figé sur la VM
                try:
                    out = subprocess.run(VM + ["cd ~/nb && python3 receipts.py issue compte"], capture_output=True, text=True, timeout=40).stdout
                    reply += f"\n🧾 reçu n°{json.loads(out)[0]} : tape /preuve {json.loads(out)[0]} pour voir d'où vient ce chiffre"
                except Exception:
                    reply += "\n(⚠️ non prouvé : reçu indisponible)"
            send(reply); log({"from": "nb", "text": reply})
            subprocess.run(VM + [f"echo '{json.dumps({'ts': m['ts']})}' >> ~/nb/answered.jsonl"], timeout=30)
            warn = fact_check(reply)
            if warn:
                send(warn.strip()); log({"from": "nb", "text": warn.strip(), "kind": "fact_check"})
        time.sleep(10)


if __name__ == "__main__":
    main()
