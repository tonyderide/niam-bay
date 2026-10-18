#!/usr/bin/env python3
"""Affirmations avec reçu (conseil 1019, 7.18). Sur la VM.
Un reçu = (n°, identifiant de commande de la LISTE BLANCHE, heure, sortie figée au moment de l'affirmation).
/preuve N montre la sortie figée ET une relecture maintenant : on voit si le fait a changé depuis, sans confondre le temps qui passe avec un mensonge.
Jamais de commande libre. Les secrets sont masqués dans les sorties."""
import json, os, re, subprocess, time
os.environ["TZ"] = "Europe/Paris"; time.tzset()
NB = os.path.expanduser("~/nb"); R = os.path.join(NB, "receipts.jsonl")
WHITELIST = {
    "compte": "tail -12 ~/et/et.log",
    "paris": "cd ~/nb/calibration && python3 -c \"import json;P=json.load(open('predictions.json'));d=[x for x in P if x['outcome'] is not None];print(len(d),'tranchés,',len(P)-len(d),'en attente');print('Brier',round(sum((x['p']-x['outcome'])**2 for x in d)/len(d),4) if d else '-')\"",
    "duel": "cd ~/nb/duel && python3 duel.py board",
    "services": "pgrep -fa '[n]b_vm_bot|[s]uiveurs/collector' | cut -c1-60; crontab -l | grep -c nb/",
}
SECRET = re.compile(r"\d{8,}:[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9_-]{20,}|[A-Fa-f0-9]{40,}")


def run(cid):
    out = subprocess.run(WHITELIST[cid], shell=True, capture_output=True, text=True, timeout=60).stdout.strip()
    return SECRET.sub("«masqué»", out)[-1500:]


def issue(cid):
    rows = [json.loads(l) for l in open(R)] if os.path.exists(R) else []
    n = len(rows) + 1
    rec = {"n": n, "cmd": cid, "t": time.strftime("%F %H:%M:%S"), "out": run(cid)}
    open(R, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
    return n, rec["out"]


def proof(n):
    rows = {json.loads(l)["n"]: json.loads(l) for l in open(R)} if os.path.exists(R) else {}
    if n not in rows:
        return f"reçu n°{n} introuvable"
    r = rows[n]; now = run(r["cmd"])
    same = "identique" if now == r["out"] else "DIFFÉRENTE (le monde a bougé depuis, ou l'affirmation était fausse)"
    return (f"🧾 reçu n°{n} : commande « {r['cmd']} » (liste blanche)\n— sortie figée le {r['t']} :\n{r['out']}\n\n"
            f"— relue maintenant ({time.strftime('%H:%M:%S')}), {same} :\n{now}")


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "issue": print(json.dumps(issue(sys.argv[2])))
    else: print(proof(int(sys.argv[2])))
