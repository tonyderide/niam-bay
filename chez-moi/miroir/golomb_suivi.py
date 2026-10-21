"""Juge des prédictions « moi-calcul » : golomb15-suivi.txt reçoit du PC, toutes les 10 min, la dernière ligne du log horodatée.
Usage : golomb_suivi.py ÉCHÉANCE MOTIF [FICHIER] -> 1 si une ligne datée <= ÉCHÉANCE (heure de Paris) contient MOTIF, sinon 0."""
import os, sys
dl, motif = sys.argv[1], sys.argv[2]
f = os.path.expanduser("~/nb/miroir/" + (sys.argv[3] if len(sys.argv) > 3 else "golomb15-suivi.txt"))
L = open(f).read().splitlines() if os.path.exists(f) else []
print(int(any(l[:16] <= dl and motif in l for l in L)))
