# Applique PREREG-08 (tournoi principal + avenant scalp).
import json, sys, math, banc
M21 = ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","DOT","LTC","BCH","UNI","ATOM","NEAR","FIL","AAVE","APT","OP","TRX","XLM","ETC"]
def mk(p): return {**p, "marches": M21 if p["tf"] == "1d" else ["BTC","ETH","SOL"]}
def mesure(spec, a, b):
    n = tot = 0
    for m in spec["marches"]:
        T, C = banc.candles(banc.SYM[m], spec["tf"]); tr = banc.tester(spec, C, T, a, b)[0]; n += len(tr); tot += sum(r for r, _ in tr)
    return n, tot
def juger(spec, per):
    banc.PERIODES = per; o = banc.banc(spec).split("\n")
    return [(l.split(" : ")[0], l.split("|| ")[-1]) for l in o[1:-1]], o[-1]
mode = sys.argv[1]
if mode == "principal":
    P = [mk(p) for p in json.load(open("specs/08-propositions.json"))]; res = []
    a, b = banc.ts("2024-01-01"), banc.ts("2026-01-01")
    for p in P:
        try: n, tot = mesure(p, a, b)
        except Exception as e: print(f"  ÉLIMINÉE {p['nom']} : {type(e).__name__} {e}"); continue
        res.append((tot, n, p)); print(f"  {p['expert']:10} {p['nom']:40} {p['tf']:4} trades {n:5}  somme 24-25 {tot*100:+8.1f} %", flush=True)
    res = sorted([r for r in res if r[1] >= 100], key=lambda r: -r[0])
    for rang, (tot, n, p) in enumerate(res[:3], 1):
        tag = "JUGEMENT" if rang == 1 else "info"
        lignes, v = juger(p, ((f"2026 ({tag})", banc.ts("2026-01-01"), banc.ts("2026-10-17")), ("jan-juin 2026", banc.ts("2026-01-01"), banc.ts("2026-07-01")), ("juil-oct 2026, après cutoff", banc.ts("2026-07-01"), banc.ts("2026-10-17"))))
        print(f"\n#{rang} {p['nom']} ({p['expert']}, {p['tf']}) — sélection {tot*100:+.1f} % sur {n} trades")
        for per, t in lignes: print(f"   {per:28} → {t}")
        if rang == 1: print("   VERDICT DU TOURNOI (2026 entier) :", "voir ligne 2026 : OK = GAGNE, NON = ÉCHEC")
else:
    P = [{**p, "marches": ["BTC","ETH","SOL"]} for p in json.load(open("specs/08-scalp.json"))]; res = []
    a, b = banc.ts("2026-01-01"), banc.ts("2026-07-01"); jours = (b - a) / 86400
    for p in P:
        try: n, tot = mesure(p, a, b)
        except Exception as e: print(f"  ÉLIMINÉE {p['nom']} : {e}"); continue
        parjour = n / 3 / jours; print(f"  {p['nom']:34} trades {n:6} ({parjour:.1f}/jour/marché)  somme jan-juin {tot*100:+9.1f} %", flush=True)
        if parjour >= 30: res.append((tot, n, p))
    if not res: print("AUCUNE stratégie admise (≥ 30 trades/jour/marché)"); sys.exit()
    tot, n, p = max(res, key=lambda r: r[0]); print(f"\nSÉLECTION : {p['nom']}")
    lignes, v = juger(p, (("juil-oct 2026 (JUGEMENT, taker)", banc.ts("2026-07-01"), banc.ts("2026-10-17")),))
    for per, t in lignes: print(f"   {per} → {t}")
    banc.FEE = 0.0002; lignes, v = juger(p, (("juil-oct 2026 (info, maker 0,02 %)", banc.ts("2026-07-01"), banc.ts("2026-10-17")),))
    for per, t in lignes: print(f"   {per} → {t}")
