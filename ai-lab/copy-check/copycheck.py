"""copy-check: avant de copier un trader/vault Hyperliquid, regarde comment il gagne.

Lecture seule, API publique. Usage: python3 copycheck.py 0xADRESSE [...]
Le ROI dit combien il a gagné. Ceci dit à quel point c'était fragile.
"""
import json, random, statistics as st, sys, time, urllib.request

API = "https://api.hyperliquid.xyz/info"


def info(body):
    r = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=30))


def profile(fills):
    pnl = [float(x["closedPnl"]) - float(x.get("fee", 0)) for x in fills if float(x["closedPnl"]) != 0]
    if len(pnl) < 20:
        return None
    wins = [p for p in pnl if p > 0]; losses = [p for p in pnl if p <= 0]
    opens = [x for x in fills if x["dir"].startswith("Open")]
    longs = sum(1 for x in opens if "Long" in x["dir"])
    total = sum(pnl)
    best = sorted(pnl, reverse=True)
    # part du profit qui vient des 5 meilleurs trades
    top5 = sum(best[:5]) / total if total > 0 else None
    # combien de gains médians efface la pire perte
    erase = abs(min(pnl)) / st.median(wins) if wins and min(pnl) < 0 else 0
    # bootstrap: on rejoue les mêmes trades dans un ordre aléatoire, pire creux médian
    rnd = random.Random(0); dds = []
    for _ in range(300):
        s = pnl[:]; rnd.shuffle(s); eq = peak = dd = 0
        for p in s:
            eq += p; peak = max(peak, eq); dd = min(dd, eq - peak)
        dds.append(dd)
    days = (max(x["time"] for x in fills) - min(x["time"] for x in fills)) / 86.4e6
    return dict(days=round(days, 1), trades=len(pnl), win_rate=round(len(wins) / len(pnl), 2),
                payoff=round(st.mean(wins) / abs(st.mean(losses)), 2) if wins and losses else None,
                net=round(total), top5_share=round(top5, 2) if top5 is not None else None,
                worst_loss_erases_median_wins=round(erase), long_share=round(longs / len(opens), 2) if opens else None,
                maker_share=round(sum(1 for x in fills if not x["crossed"]) / len(fills), 2),
                drawdown_p50=round(st.median(dds)), drawdown_p90=round(sorted(dds)[30]))


def verdict(p):
    flags = []
    if p["net"] <= 0: flags.append(f"perdant sur ses {p['days']} derniers jours de trades clos (net de frais), quel que soit l'APR affiché")
    if p["top5_share"] and p["top5_share"] > 0.8: flags.append(f"{int(p['top5_share']*100)} % du profit vient de 5 trades : chance ou queue épaisse")
    if p["worst_loss_erases_median_wins"] >= 50: flags.append(f"une seule perte efface {p['worst_loss_erases_median_wins']} gains typiques")
    if p["long_share"] is not None and p["long_share"] > 0.9: flags.append("long only : dépend du marché haussier")
    if p["maker_share"] > 0.7: flags.append("surtout des ordres limite (maker) : difficile à copier au même prix")
    return flags or ["rien de flagrant (ce qui ne prouve pas qu'il continuera)"]


if __name__ == "__main__":
    for a in sys.argv[1:]:
        f = info({"type": "userFills", "user": a}); time.sleep(1.5)
        p = profile(f)
        cs = info({"type": "clearinghouseState", "user": a}); time.sleep(1.5)
        upnl = sum(float(x["position"]["unrealizedPnl"]) for x in cs["assetPositions"])
        value = float(cs["marginSummary"]["accountValue"])
        print(f"\n{a}  valeur={value:.0f}  pnl latent ouvert={upnl:.0f}")
        if value > 0 and upnl < -0.3 * value:
            print(f"  - perte latente ouverte = {int(-upnl / value * 100)} % de la valeur : elle n'apparaît dans aucun win rate")
        if not p:
            print("  pas assez de trades clos"); continue
        print("  " + "  ".join(f"{k}={v}" for k, v in p.items()))
        for v in verdict(p): print("  -", v)
