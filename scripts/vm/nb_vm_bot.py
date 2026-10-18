#!/usr/bin/env python3
"""Bot Telegram de NB, côté VM (24/7, sans LLM). Remplace l'écoute faite par le PC (un seul poller par token).
- Commandes instantanées : /compte /duel /pari N /paris /todo /nuit /ping /aide
- Texte libre : rangé dans ~/nb/inbox.jsonl (status=pending). Le cerveau Claude, sur le PC de Tony, vient le chercher (relais ssh)
  et répond lui-même. Si personne ne répond en 90 s (PC éteint ou en veille), le bot prévient Tony une fois.
Lancé et relancé par cron (scripts/vm/keepalive.sh)."""
import json, os, re, subprocess, time, urllib.parse, urllib.request

NB = os.path.expanduser("~/nb")
TOKEN = open(os.path.expanduser("~/martin/.tg_token")).read().strip()
CHAT = "6574420846"
API = f"https://api.telegram.org/bot{TOKEN}/"
INBOX, OFFSET = os.path.join(NB, "inbox.jsonl"), os.path.join(NB, "tg_offset")
os.environ["TZ"] = "Europe/Paris"; time.tzset()


def tg(method, **p):
    return json.load(urllib.request.urlopen(API + method, data=urllib.parse.urlencode(p).encode(), timeout=40))


def send(text):
    for i in range(0, len(text), 3900):
        tg("sendMessage", chat_id=CHAT, text=text[i:i + 3900])


def rows():
    return [json.loads(l) for l in open(INBOX)] if os.path.exists(INBOX) else []


def save(R):
    tmp = INBOX + ".tmp"; open(tmp, "w").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in R)); os.replace(tmp, INBOX)


def log(entry):
    entry["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); entry["ts"] = time.time()
    R = rows(); R.append(entry); save(R)


def run(*a):
    return subprocess.run(["python3", *a], cwd=NB, capture_output=True, text=True, timeout=90).stdout.strip()


def q_compte():
    t = open(os.path.expanduser("~/et/et.log")).read().splitlines()[-30:]
    heads = [i for i, l in enumerate(t) if re.match(r"\d{4}-\d\d-\d\d ", l)]
    if not heads:
        return "💰 pas de relevé exchange-truth récent"
    blk = t[heads[-1]:]
    txt = "\n".join(blk)
    eq = re.findall(r"equity ([0-9.]+) vs", txt); wc = re.findall(r"stops hit: -([0-9.]+)", txt)
    now = f"\nequity ≈ {float(eq[-1]) + float(wc[-1]):.2f} $ (après stops : {eq[-1]} $)" if eq and wc else ""
    return "💰 mon compte Kraken (relevé UTC)\n" + blk[0] + now + "".join("\n" + l.strip() for l in blk[1:] if re.search("CRITICAL|WARN", l))


def q_todo():
    p = os.path.join(NB, "a-faire-tony.md")
    t = [l[6:] for l in open(p).read().splitlines() if l.startswith("- [ ] ")] if os.path.exists(p) else []
    return "📌 ce qui t'attend :\n" + "\n".join(f"{i + 1}. {x}" for i, x in enumerate(t)) if t else "📌 rien ne t'attend"


def q_paris():
    P = json.load(open(os.path.join(NB, "calibration/predictions.json")))
    done = [x for x in P if x["outcome"] is not None]; pend = [x for x in P if x["outcome"] is None]
    head = f"🎯 {len(done)} paris tranchés, {len(pend)} en attente"
    if done:
        head += f", Brier {sum((x['p'] - x['outcome']) ** 2 for x in done) / len(done):.3f} (0,25 = pile ou face)"
    return head + "\n" + "\n".join(f"{x['p']:.2f} {x['claim'][:60]} ({x['resolve_at'][5:16]})" for x in pend[:6])


QUICK = {"/compte": q_compte, "/todo": q_todo, "/paris": q_paris,
         "/duel": lambda: run("duel/duel.py", "board"),
         "/nuit": lambda: run("morning_digest.py", "--dry"),
         "/ping": lambda: "VM : toujours là. Cerveau Claude : " + ("réveillé" if time.time() - brain_seen() < 120 else "endormi (PC en veille ou éteint)"),
         "/aide": lambda: "Instantané (sans IA) : /compte /duel /pari N /paris /todo /nuit /ping. Le reste va à NB (Claude, sur le PC)."}
QUICK["/help"] = QUICK["/aide"]; QUICK["/start"] = QUICK["/aide"]


def brain_seen():
    p = os.path.join(NB, "brain_heartbeat")
    return os.path.getmtime(p) if os.path.exists(p) else 0


def answered():
    p = os.path.join(NB, "answered.jsonl")  # écrit par le cerveau (PC) : un ts par message traité
    return {json.loads(l)["ts"] for l in open(p)} if os.path.exists(p) else set()


def nudge_unanswered():
    R = rows(); changed = False; done = answered()
    for r in R:
        if r.get("from") == "tony" and r.get("status") == "pending" and r["ts"] not in done and not r.get("nudged") and time.time() - r["ts"] > 90:
            send("🤖 Le cerveau de NB (Claude, sur le PC) dort : ton message est gardé, réponse dès qu'il se réveille. "
                 "En attendant, réponses instantanées : /compte /duel /paris /todo /nuit")
            r["nudged"] = True; changed = True
    if changed:
        save(R)


def main():
    offset = int(open(OFFSET).read()) if os.path.exists(OFFSET) else 0
    while True:
        nudge_unanswered()
        try:
            ups = tg("getUpdates", offset=offset, timeout=25)["result"]
        except Exception:
            time.sleep(10); continue
        for u in ups:
            offset = u["update_id"] + 1; open(OFFSET, "w").write(str(offset))
            m = u.get("message") or {}; text = (m.get("text") or "").strip()
            if str(m.get("chat", {}).get("id")) != CHAT:
                log({"from": "inconnu", "chat": m.get("chat", {}).get("id"), "text": text[:200]}); continue
            if not text:
                continue
            cmd = text.split()[0].lower().split("@")[0]
            if cmd == "/pari":
                try:
                    v = float(text.split()[1].replace("%", "").replace(",", "."))
                    reply = run("duel/duel.py", "tony", str(v / 100 if v > 1 else v))
                except Exception:
                    reply = "format : /pari 70  (= 70 % que la réponse soit OUI)"
            elif cmd in QUICK:
                try:
                    reply = QUICK[cmd]()
                except Exception as e:
                    reply = f"(commande en échec : {type(e).__name__})"
            else:
                log({"from": "tony", "text": text, "status": "pending"}); continue
            log({"from": "tony", "text": text, "status": "auto"}); send(reply); log({"from": "nb-vm", "text": reply})


if __name__ == "__main__":
    main()
