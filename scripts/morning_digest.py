#!/usr/bin/env python3
"""Résumé du matin pour Tony : SANS LLM (0 quota), envoyé sur Telegram à 07h00. Les nuits sont interdites aux messages (22h-07h), sauf SL.
Approuvé par le conseil (score 6.82). Tout est EXTRAIT tel quel (journal, verdicts du conseil, compte) : rien n'est reformulé, donc rien n'est inventé.
Arrêt automatique : 3 matins de suite sans réponse de Tony dans l'inbox → le script se désactive lui-même (fichier ~/.config/nb/digest_off).
Usage : morning_digest.py [--dry]"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.expanduser("~/.config/nb")
STATE, OFF = os.path.join(CFG, "digest_state.json"), os.path.join(CFG, "digest_off")
FAIL = re.compile(r"raté|échec|faux|fausse|abandon|ne bat pas|❌|correction|erreur|pire|NON|PAS MAINTENANT|périmé|contredit", re.I)


def sh(cmd):
    return subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True, timeout=60).stdout


def night_lines(since):
    diff = sh(f"git log --since='{since}' --reverse -p --format= -- docs/loop-journal.md")
    return [l[1:].strip() for l in diff.splitlines() if l.startswith("+- ")]


def verdicts(since_ts):
    p = os.path.join(REPO, "ai-lab/conseil/deliberations.jsonl")
    out = []
    for l in open(p).read().splitlines() if os.path.exists(p) else []:
        r = json.loads(l)
        if time.mktime(time.strptime(r["utc"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone >= since_ts:
            out.append(f"{r['verdict'].split(' ')[0]} ({r['score']}) {r['idea'][:70]}")
    return out


def tony_replied_since(ts):
    p = os.path.join(REPO, "docs/inbox.jsonl")
    for l in open(p).read().splitlines() if os.path.exists(p) else []:
        e = json.loads(l)
        if e.get("from") == "tony" and time.mktime(time.strptime(e["utc"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone >= ts:
            return True
    return False


def main(dry):
    if os.path.exists(OFF):
        return print("désactivé (3 matins sans réponse) : supprimer", OFF, "pour réactiver")
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"last": None, "silent": 0}
    if st["last"] and not dry:
        st["silent"] = 0 if tony_replied_since(st["last"]) else st["silent"] + 1
        if st["silent"] >= 3:
            open(OFF, "w").write(time.strftime("%F"))
            json.dump(st, open(STATE, "w"))
            return print("3 matins sans réponse : je m'arrête")
    since = "yesterday 20:00"
    since_ts = time.mktime(time.strptime(time.strftime("%F", time.localtime(time.time() - 86400)) + " 20:00", "%Y-%m-%d %H:%M"))
    lines = night_lines(since)
    fails = [l for l in lines if FAIL.search(l)]
    done = [l for l in lines if l not in fails]
    acct = next((l for l in sh("scripts/nb --no-mark").splitlines() if l.startswith("COMPTE")), "COMPTE ?")
    acct = re.sub(r"\s+", " ", acct.replace("COMPTE", "").strip())
    v = verdicts(since_ts)
    trim = lambda l: re.sub(r"^-?\s*\d\d:\d\d\s*", "", l)[:150]
    msg = [f"🤖 NB, résumé auto de la nuit ({len(lines)} entrées de journal, 0 quota)"]
    msg += ["✅ " + trim(l) for l in done[-3:]]
    msg += ["⚠️ " + trim(l) for l in fails[-3:]]
    if v:
        oui = sum(x.startswith("OUI") for x in v)
        msg.append(f"🗳 conseil : {len(v)} idées, {oui} OUI. Dernière : {v[-1][:90]}")
    msg.append("💰 " + acct[:150])
    msg.append("❓ Qu'est-ce qui manquait ou était faux ? (une réponse, même « rien », me dit que tu l'as lu)")
    text = "\n".join(msg)
    if dry:
        return print(text)
    tok = open(os.path.join(CFG, "tg_token")).read().strip()
    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage",
                           data=urllib.parse.urlencode({"chat_id": "6574420846", "text": text}).encode(), timeout=20)
    st["last"] = time.time()
    json.dump(st, open(STATE, "w"))


if __name__ == "__main__":
    main("--dry" in sys.argv)
