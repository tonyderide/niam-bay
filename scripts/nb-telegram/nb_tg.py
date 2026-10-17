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


def answer(text):
    prompt = (f"Derniers échanges Telegram :\n{history()}\n\nNouveau message de Tony ({time.strftime('%F %H:%M')}, heure de Paris) :\n{text}")
    r = subprocess.run(["claude", "-p", prompt, "--append-system-prompt", SYSTEM, "--allowedTools", *TOOLS.split(),
                        "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit", "Agent"],
                       cwd=REPO, capture_output=True, text=True, timeout=600)
    return (r.stdout.strip() or f"(NB n'a pas pu répondre : {r.stderr.strip()[:300]})")


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
