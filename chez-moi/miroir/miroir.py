"""Mon miroir de calibration : relit predictions.json sur la VM et écrit miroir.md (Brier par famille, courbe par tranche)."""
import collections, json, os, subprocess, time
VM = ["ssh", "-i", os.path.expanduser("~/.ssh/martin_vm.key"), "-o", "ConnectTimeout=8", "ubuntu@141.253.108.141"]
P = json.loads(subprocess.run(VM + ["cat ~/nb/calibration/predictions.json"], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30).stdout)
moi = [p for p in P if p.get("family") != "tony"]; R = [p for p in moi if p.get("outcome") is not None]
B = lambda L: sum((p["p"] - float(p["outcome"])) ** 2 for p in L) / len(L)
L = [f"# Mon miroir de calibration — {time.strftime('%Y-%m-%d %H:%M')}", "",
     f"{len(R)} prédictions tranchées sur {len(moi)}. **Brier total {B(R):.3f}** (pile ou face 0,250 ; plus bas = mieux)." if R else "Rien de tranché.", ""]
fam = collections.defaultdict(list)
for p in R: fam[p.get("family") or p["id"].split("-")[0]].append(p)
L += ["| Famille | n | Brier | vrais | p moyen |", "|---|---|---|---|---|"]
L += [f"| {f} | {len(g)} | {B(g):.3f} | {sum(bool(p['outcome']) for p in g)}/{len(g)} | {sum(p['p'] for p in g)/len(g):.2f} |" for f, g in sorted(fam.items())]
L += ["", "| Quand je dis | n | vrai en réalité |", "|---|---|---|"]
for lo, hi in ((0, .3), (.3, .45), (.45, .55), (.55, .7), (.7, 1.01)):
    g = [p for p in R if lo <= p["p"] < hi]
    if g: L.append(f"| {lo:.0%} à {min(hi,1):.0%} (moy. {sum(p['p'] for p in g)/len(g):.0%}) | {len(g)} | {sum(bool(p['outcome']) for p in g)/len(g):.0%} |")
ecart = sum(abs(p["p"] - .5) for p in R) / len(R) if R else 0
L += ["", f"Audace moyenne (écart à 50 %) : **{ecart*100:.1f} points**. En dessous de 5, je me cache derrière le pile ou face."]
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "miroir.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
