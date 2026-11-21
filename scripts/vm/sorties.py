#!/usr/bin/env python3
"""Signale chaque sortie des martingales (×4 et DOGE), même quand la position est rouverte dans la minute.
Comble l'angle mort de controle.py (qui ne voit une fermeture que si la paire est vide à son passage, toutes les 5 min).
LECTURE SEULE : lit ~/martin/garde/martingale*.json (liste `trades`), écrit à NB dans ~/nb/controle-boite.jsonl.
Premier passage : mémorise l'existant sans rien écrire. SORTIES_ESSAI=1 : affiche au lieu d'écrire.
PRÉPARÉ le 21/11/2026, PAS ENCORE EN CRON (à installer au retour de Tony : */5 * * * * python3 ~/martin/scripts/sorties.py)."""
import glob, json, os, time
G = os.path.expanduser("~/martin/garde"); ETAT = os.path.join(G, "sorties.json")
BOITE = os.path.expanduser("~/nb/controle-boite.jsonl"); ESSAI = os.environ.get("SORTIES_ESSAI") == "1"
vu = json.load(open(ETAT)) if os.path.exists(ETAT) else None
neuf, msgs = {}, []
for f in sorted(glob.glob(os.path.join(G, "martingale*.json"))):
    nom = os.path.basename(f)[:-5]; paire = nom.split("-")[1] if "-" in nom else "DOGE"
    try: d = json.load(open(f))
    except Exception: continue
    tr = d.get("trades", []); neuf[nom] = len(tr)
    if vu is None or nom not in vu: continue
    for t in tr[vu[nom]:]:
        s = "long" if t["sens"] > 0 else "short"
        msgs.append(f"{'🟢' if t['res'] > 0 else '🔴'} martingale {paire} {s} {t['taille']} sortie : {t['entree']} → {t['sortie']} = {t['res'] * 100:+.2f} c (estimation du script, frais compris). "
                    f"Cumul {d.get('cumul', 0) * 100:+.1f} c ; rouvert {'long' if d.get('sens', 0) > 0 else 'short'} niveau {d.get('niveau')}.")
for m in msgs:
    if ESSAI: print(m)
    else:
        with open(BOITE, "a") as f: f.write(json.dumps({"from": "sorties", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "text": m, "status": "pending"}, ensure_ascii=False) + "\n")
if not ESSAI: json.dump(neuf, open(ETAT, "w"))
elif vu is None: print("premier passage (essai) : mémoriserait", neuf)
