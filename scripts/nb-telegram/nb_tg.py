#!/usr/bin/env python3
"""NB sur Telegram : Tony écrit au bot, NB (claude -p) répond.

- N'écoute QUE le chat de Tony. Tout autre expéditeur est ignoré (et noté).
- NB ici n'a que des outils de lecture : il ne peut ni trader, ni modifier de fichier, ni lancer de commande.
- Chaque échange est ajouté à docs/inbox.jsonl, pour que la session terminal et la boucle sachent ce que Tony a dit.
- Tourne sur le PC de Tony (systemd utilisateur). PC éteint = NB injoignable, et c'est dit honnêtement par /ping.
"""
import json, os, subprocess, time, urllib.parse, urllib.request

REPO = os.path.expanduser("~/projets/tonyderide/niam-bay")
INBOX = os.path.join(REPO, "docs/inbox.jsonl")
TOKEN = open(os.path.expanduser("~/.config/nb/tg_token")).read().strip()
CHAT_ID = "6574420846"
API = f"https://api.telegram.org/bot{TOKEN}/"
OFFSET_FILE = os.path.expanduser("~/.config/nb/tg_offset")
TOOLS = "Read Grep Glob WebSearch WebFetch"

SYSTEM = (
    "Tu es Niam-Bay (NB), l'IA de Tony. Tony t'écrit sur Telegram depuis son téléphone. "
    "Réponds en français, ton familier, COURT (écran de téléphone : 1 à 6 lignes, pas de tableaux). "
    "Ta mémoire est dans ce repo : docs/loop-journal.md (ce que tu as fait récemment), docs/loop-backlog.md, "
    "docs/projets/mandat-capital-nb.md, ai-lab/. Lis ce qu'il faut avant de répondre sur un fait. "
    "Tu n'as que des outils de lecture : tu ne peux pas trader, ni modifier, ni lancer de commande. "
    "Si Tony demande une action, dis-lui que tu la notes et que la session NB (terminal ou boucle) la fera. "
    "Ne jamais inventer un souvenir ou un chiffre : si tu ne sais pas, dis-le."
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
            ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
             "--append-system-prompt", SYSTEM, "--allowedTools", *TOOLS.split(),
             "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit", "Agent"],
            cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
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
            _live["v"] = r.stdout.strip() or "(VM muette)"
        except Exception as e:
            _live["v"] = f"(état live indisponible : {type(e).__name__})"
        _live["t"] = time.time()
    return _live["v"]


def answer(text):
    return BRAIN.ask(f"État live du compte Kraken (exchange-truth, heure UTC) :\n{live_state()}\n\n"
                     f"Nouveau message de Tony ({time.strftime('%F %H:%M')}, heure de Paris) :\n{text}")


def main():
    offset = int(open(OFFSET_FILE).read()) if os.path.exists(OFFSET_FILE) else 0
    while True:
        try:
            ups = tg("getUpdates", offset=offset, timeout=30)["result"]
        except Exception:
            time.sleep(10); continue
        for u in ups:
            offset = u["update_id"] + 1
            open(OFFSET_FILE, "w").write(str(offset))
            m = u.get("message") or {}
            text = m.get("text", "")
            if str(m.get("chat", {}).get("id")) != CHAT_ID:
                log({"from": "inconnu", "chat": m.get("chat", {}).get("id"), "text": text[:200]}); continue
            if not text:
                continue
            log({"from": "tony", "text": text})
            if text.strip() == "/ping":
                reply = "NB est là (PC de Tony allumé, service nb-telegram actif)."
            else:
                tg("sendChatAction", chat_id=CHAT_ID, action="typing")
                try:
                    reply = answer(text)
                except subprocess.TimeoutExpired:
                    reply = "(trop long, j'abandonne cette réponse ; la session NB verra ton message dans l'inbox)"
            send(reply)
            log({"from": "nb", "text": reply})


if __name__ == "__main__":
    main()
