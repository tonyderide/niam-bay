#!/usr/bin/env python3
"""Résumé du matin, côté VM (07h00 Paris, sans LLM, 0 quota). Il tourne même si le PC de Tony dort.
Sources (recopiées depuis le PC par scripts/vm/sync.sh à chaque itération de NB) : loop-journal.md, deliberations.jsonl, a-faire-tony.md.
Compte : ~/et/et.log local. Tout est EXTRAIT tel quel, rien n'est reformulé.
Arrêt automatique : 3 matins de suite sans message de Tony → ~/nb/digest_off."""
import json, os, re, sys, time, urllib.parse, urllib.request

os.environ["TZ"] = "Europe/Paris"; time.tzset()
NB = os.path.expanduser("~/nb")
STATE, OFF = os.path.join(NB, "digest_state.json"), os.path.join(NB, "digest_off")
FAIL = re.compile(r"raté|échec|faux|fausse|abandon|ne bat pas|❌|correction|erreur|pire|NON|PAS MAINTENANT|périmé|contredit|dormi", re.I)


def main(dry):
    if not dry and time.localtime().tm_hour != 7:  # cron à 05h et 06h UTC : seul celui qui tombe à 07h Paris (été/hiver) envoie
        return
    if os.path.exists(OFF):
        return print("désactivé (3 matins sans réponse) : supprimer", OFF)
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"last": None, "silent": 0, "jline": None}
    inbox = [json.loads(l) for l in open(os.path.join(NB, "inbox.jsonl"))] if os.path.exists(os.path.join(NB, "inbox.jsonl")) else []
    if st["last"] and not dry:
        replied = any(r.get("from") == "tony" and r.get("ts", 0) > st["last"] for r in inbox)
        st["silent"] = 0 if replied else st["silent"] + 1
        if st["silent"] >= 3:
            open(OFF, "w").write(time.strftime("%F")); json.dump(st, open(STATE, "w"))
            return print("3 matins sans réponse : je m'arrête")
    J = open(os.path.join(NB, "loop-journal.md")).read().splitlines() if os.path.exists(os.path.join(NB, "loop-journal.md")) else []
    start = st["jline"] if st["jline"] is not None and st["jline"] <= len(J) else max(0, len(J) - 15)
    lines = [l for l in J[start:] if l.startswith("- ")]
    fails = [l for l in lines if FAIL.search(l)]; done = [l for l in lines if l not in fails]
    trim = lambda l: re.sub(r"^-?\s*\d\d:\d\d\s*", "", l)[:150]
    since = st["last"] or time.time() - 11 * 3600
    D = [json.loads(l) for l in open(os.path.join(NB, "deliberations.jsonl"))] if os.path.exists(os.path.join(NB, "deliberations.jsonl")) else []
    D = [d for d in D if time.mktime(time.strptime(d["utc"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone >= since]
    et = open(os.path.expanduser("~/et/et.log")).read().splitlines()[-30:]
    heads = [l for l in et if re.match(r"\d{4}-\d\d-\d\d ", l)]
    txt = "\n".join(et); eq = re.findall(r"equity ([0-9.]+) vs", txt); wc = re.findall(r"stops hit: -([0-9.]+)", txt)
    acct = (heads[-1][11:] if heads else "?") + (f" | equity ≈ {float(eq[-1]) + float(wc[-1]):.2f} $ (après stops {eq[-1]} $)" if eq and wc else "")
    msg = [f"🤖 NB, résumé auto de la nuit ({len(lines)} entrées de journal, 0 quota)"]
    msg += ["✅ " + trim(l) for l in done[-3:]] + ["⚠️ " + trim(l) for l in fails[-3:]]
    if D:
        last = D[-1]
        msg.append(f"🗳 conseil : {len(D)} idées, {sum(x['verdict'].startswith('OUI') for x in D)} OUI. Dernière : {last['verdict'].split(' ')[0]} {last['idea'][:80]}")
    if not lines:
        msg.append("😴 rien de nouveau dans le journal (le PC a peut-être dormi)")
    Q = os.path.join(NB, "annonces_queue.jsonl")
    if os.path.exists(Q):
        for l in open(Q).read().splitlines()[-3:]:
            t = json.loads(l)["text"]
            msg.append("💡 " + (t if "http" in t else t[:200]))  # ne jamais couper un lien
        if not dry:
            os.remove(Q)
    msg.append("💰 " + acct)
    todo = [l[6:].split(".")[0][:110] for l in open(os.path.join(NB, "a-faire-tony.md")).read().splitlines() if l.startswith("- [ ] ")] if os.path.exists(os.path.join(NB, "a-faire-tony.md")) else []
    msg += ["📌 pour toi : " + t for t in todo[:2]]
    msg.append("❓ Qu'est-ce qui manquait ou était faux ? (une réponse, même « rien », me dit que tu l'as lu)")
    text = "\n".join(m for m in msg if m)
    if dry:
        return print(text)
    tok = open(os.path.expanduser("~/martin/.tg_token")).read().strip()
    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data=urllib.parse.urlencode({"chat_id": "6574420846", "text": text}).encode(), timeout=20)
    st.update(last=time.time(), jline=len(J)); json.dump(st, open(STATE, "w"))


if __name__ == "__main__":
    main("--dry" in sys.argv)
