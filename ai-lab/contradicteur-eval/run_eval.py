"""Banc d'examen du contradicteur (idée prise à l'équipe Claude Code : les incidents passés deviennent des cas de test,
et un changement de prompt ou de modèle n'est gardé que si le score monte).
Score = cas justes / total ; on compte à part les faux blocages (gêne) et les erreurs laissées passer (danger)."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scripts/hooks"))
from fact_check_stop import judge

D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.json")))
ok = fp = fn = 0
for c in D["cases"]:
    v = judge(c["reply"], D["state"])
    got = "ok" if v.get("ok") else "block"
    ok += got == c["expected"]; fp += got == "block" and c["expected"] == "ok"; fn += got == "ok" and c["expected"] == "block"
    print(f"{'✅' if got == c['expected'] else '❌'} {c['id']:22} attendu={c['expected']:5} obtenu={got:5} {v.get('issue', '')[:90]}")
line = f"{time.strftime('%F %H:%M')} score {ok}/{len(D['cases'])} | faux blocages {fp} | erreurs laissées passer {fn}"
print(line)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.log"), "a").write(line + "\n")
