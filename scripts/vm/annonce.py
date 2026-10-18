#!/usr/bin/env python3
"""Fil d'invention en direct (conseil 1018, 7.18). Sans LLM. Usage (sur la VM) : annonce.py "texte" [--dry]
- Envoi à Tony seulement entre 7h et 22h (Paris), au plus 3 par jour. En dehors : mis en file pour le résumé de 07h.
- Les ratés s'annoncent comme les réussites. Ne jamais y mettre de clé ni de jeton."""
import json, os, sys, time, urllib.parse, urllib.request
os.environ["TZ"] = "Europe/Paris"; time.tzset()
NB = os.path.expanduser("~/nb"); LOG = os.path.join(NB, "annonces.jsonl"); QUEUE = os.path.join(NB, "annonces_queue.jsonl")


def main(text, dry):
    today = time.strftime("%F"); h = time.localtime().tm_hour
    sent = [json.loads(l) for l in open(LOG)] if os.path.exists(LOG) else []
    n_today = sum(1 for s in sent if s["day"] == today)
    if not (7 <= h < 22) or n_today >= 3:
        if dry:
            return print(f"[dry] serait mis en file ({'hors 7h-22h' if not 7 <= h < 22 else 'plafond 3/jour'})")
        open(QUEUE, "a").write(json.dumps({"t": time.time(), "text": text}, ensure_ascii=False) + "\n")
        return print(f"mis en file ({'hors 7h-22h' if not 7 <= h < 22 else 'plafond 3/jour atteint'})")
    msg = "💡 NB vient de construire : " + text[:600]
    if dry:
        return print("[dry] " + msg)
    tok = open(os.path.expanduser("~/martin/.tg_token")).read().strip()
    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data=urllib.parse.urlencode({"chat_id": "6574420846", "text": msg}).encode(), timeout=20)
    open(LOG, "a").write(json.dumps({"day": today, "t": time.time(), "text": text}, ensure_ascii=False) + "\n")
    print(f"envoyé ({n_today + 1}/3 aujourd'hui)")


if __name__ == "__main__":
    main(sys.argv[1], "--dry" in sys.argv)
