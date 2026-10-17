"""Calibration de NB : je fais des prédictions chiffrées, le monde les tranche, le score de Brier dit si on peut me croire.

predictions.json : {id, claim, p (ma probabilité que ce soit VRAI), resolve_at, cmd, test (expression Python sur `out`)}.
`python3 resolve.py` tranche celles dont l'échéance est passée et écrit docs/calibration.md.
Règle : je n'efface jamais une prédiction ratée, et je ne change pas p après coup.
"""
import json, os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "../../docs/calibration.md")


def main():
    path = os.path.join(HERE, "predictions.json")
    P = json.load(open(path))
    now = time.strftime("%Y-%m-%dT%H:%M")
    for x in P:
        if x["outcome"] is None and x["resolve_at"] <= now:
            out = subprocess.run(x["cmd"], shell=True, cwd=HERE, capture_output=True, text=True, timeout=60).stdout.strip()
            try:
                x["outcome"] = bool(eval(x["test"], {}, {"out": out}))
                x["observed"] = out[-200:]; x["resolved"] = now
            except Exception as e:
                x["error"] = f"{type(e).__name__}: {e} (out={out[-100:]!r})"
    json.dump(P, open(path, "w"), indent=1, ensure_ascii=False)
    done = [x for x in P if x["outcome"] is not None]
    lines = [f"# Calibration de NB ({now})", ""]
    if done:
        brier = sum((x["p"] - x["outcome"]) ** 2 for x in done) / len(done)
        lines += [f"**Brier = {brier:.3f}** sur {len(done)} prédictions tranchées (0 = parfait, 0.25 = pile ou face toujours à 50 %).", ""]
    else:
        lines += ["Aucune prédiction tranchée pour l'instant.", ""]
    fam = [x for x in done if x.get("family") == "dir24h"]
    if fam:
        b = lambda k: sum((x["baselines"][k] - x["outcome"]) ** 2 for x in fam) / len(fam)
        mine = sum((x["p"] - x["outcome"]) ** 2 for x in fam) / len(fam)
        lines += [f"**dir24h** ({len(fam)}/70) : moi {mine:.3f} | témoin p=0,5 {b('p05'):.3f} | témoin momentum {b('momentum'):.3f} (critère : PREREG-24H.md)", ""]
    for x in P:
        mark = "⏳" if x["outcome"] is None else ("✅ vrai" if x["outcome"] else "❌ faux")
        lines.append(f"- {mark} p={x['p']:.2f} `{x['id']}` : {x['claim']} (échéance {x['resolve_at']})" + (f" ⚠️ {x['error']}" if x.get("error") else ""))
    open(REPORT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
