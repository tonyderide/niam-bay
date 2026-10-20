#!/usr/bin/env python3
"""Bot Telegram de NB, côté VM (24/7, sans LLM). Remplace l'écoute faite par le PC (un seul poller par token).
- Commandes instantanées : /compte /duel /pari N /paris /todo /nuit /ping /aide
- Texte libre : rangé dans ~/nb/inbox.jsonl (status=pending). Le cerveau Claude, sur le PC de Tony, vient le chercher (relais ssh)
  et répond lui-même. Si personne ne répond en 90 s (PC éteint ou en veille), le bot prévient Tony une fois.
Lancé et relancé par cron (scripts/vm/keepalive.sh)."""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.expanduser("~/nb")); import receipts

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
         "/duel": lambda: run("duel/duel.py", "board"), "/certitudes": q_certitudes,
         "/nuit": lambda: run("morning_digest.py", "--dry"),
         "/ping": lambda: "VM : toujours là. Cerveau Claude : " + ("réveillé" if time.time() - brain_seen() < 120 else "endormi (PC en veille ou éteint)"),
         "/aide": lambda: "Instantané (sans IA) : /compte /duel /pari N /paris /todo /nuit /ping /preuve N. Avec NB (Claude, sur le PC) : /verif <texte d'une autre IA> pour un second avis, /banc <stratégie en français> pour la tester honnêtement (puis /banc ok), une photo d'objet (+ légende) pour une annonce de vente, /sur <ta certitude en %> (puis /certitudes, sans IA), et tout message libre."}
def q_certitudes():
    P = json.load(open(os.path.join(NB, "calibration", "predictions.json"))); T = [x for x in P if x.get("family") == "tony"]
    R = [x for x in T if x.get("outcome") is not None]; A = [x for x in T if x.get("outcome") is None]
    L = [f"🎯 Carnet des certitudes de Tony : {len(R)} tranchée(s), {len(A)} en attente"]
    if R:
        b = sum((x["p"] - float(x["outcome"])) ** 2 for x in R) / len(R); L.append(f"Score de Brier : {b:.3f} (0 = parfait, 0,25 = pile ou face)")
        for lo, hi, nom in ((0.9, 1.01, "≥ 90 %"), (0.6, 0.9, "60-90 %"), (0, 0.6, "< 60 %")):
            g = [x for x in R if lo <= x["p"] < hi]
            if g: L.append(f"Quand tu dis {nom} : vrai {sum(bool(x['outcome']) for x in g)}/{len(g)}")
    for x in A[:6]: L.append(f"⏳ {x['p']:.0%} · {x['claim'][:80]}")
    return "\n".join(L)


def with_receipt(f, cid):
    """La réponse porte un reçu : sortie figée maintenant, rejouable avec /preuve N."""
    def g():
        n, _ = receipts.issue(cid)
        return f() + f"\n🧾 reçu n°{n} : tape /preuve {n} pour voir la commande et la rejouer"
    return g


for _k, _cid in (("/compte", "compte"), ("/paris", "paris"), ("/duel", "duel")):
    QUICK[_k] = with_receipt(QUICK[_k], _cid)
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
            if not text and m.get("photo"):  # photo -> vide-grenier : /vend <légende> [photo:file_id]
                text = f"/vend {(m.get('caption') or '').strip()} [photo:{m['photo'][-1]['file_id']}]"
            if not text:
                continue
            cmd = text.split()[0].lower().split("@")[0]
            if cmd == "/preuve":
                try:
                    reply = receipts.proof(int(text.split()[1]))
                except Exception:
                    reply = "format : /preuve 7"
            elif cmd == "/pari":
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
