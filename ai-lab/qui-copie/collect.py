"""Collecte (protocole 6590136) : comptes robustes actifs, historique paginé jusqu'à 30 jours / 10 000 fills."""
import json, time, urllib.request, os, sys
sys.path.insert(0, "../turing-inverse"); import turing
rows = json.load(open("lb.json"))["leaderboardRows"]
w = lambda r, k: [float(dict(r["windowPerformances"])[k][x]) for x in ("pnl", "roi", "vlm")]
C = sorted([(w(r, "month")[1], r["ethAddress"]) for r in rows if float(r["accountValue"]) > 50000 and w(r, "allTime")[0] > 0 and w(r, "month")[0] > 0
            and w(r, "week")[0] > 0 and 0.05 < w(r, "month")[1] < 1.0 and w(r, "month")[2] / float(r["accountValue"]) > 50], reverse=True)
now = time.time() * 1000; active = []
for _, a in C:
    if len(active) >= 30: break
    try:
        f = turing.info({"type": "userFillsByTime", "user": a, "startTime": int(now - 6 * 3600e3), "endTime": int(now)}); time.sleep(2)
    except Exception:
        continue
    if len(f) >= 5: active.append(a)
print(len(active), "comptes actifs"); data = {}
for a in active:
    h = turing.history(a, max_fills=10000, max_days=30)
    data[a] = [{"t": x["time"], "coin": x["coin"], "dir": x["dir"]} for x in h if x["dir"].startswith("Open")]
    print(a[:10], len(h), "fills", len(data[a]), "ouvertures", flush=True)
json.dump(data, open("data.json", "w"))
