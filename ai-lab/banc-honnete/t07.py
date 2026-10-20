# Applique PREREG-07 : sélection sur 2024-2025, jugement unique sur 2026.
import json, banc
M = ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","DOT","LTC","BCH","UNI","ATOM","NEAR","FIL","AAVE","APT","OP","TRX","XLM","ETC"]
P = {
 "avalement": ("(shift(close) < shift(open)) & (close > open) & (open <= shift(close)) & (close >= shift(open)) & (close > sma(50))",
               "(shift(close) > shift(open)) & (close < open) & (open >= shift(close)) & (close <= shift(open)) & (close < sma(50))"),
 "marteau": ("((vmin(open, close) - low) >= absv(close - open) * 2) & ((close - low) >= (high - low) * (2 / 3)) & (low <= lowest(low, 20))",
             "((high - vmax(open, close)) >= absv(close - open) * 2) & ((high - close) >= (high - low) * (2 / 3)) & (high >= highest(high, 20))"),
 "inside_cassee": ("(shift(high) < shift(high, 2)) & (shift(low) > shift(low, 2)) & (close > shift(high, 2))",
                   "(shift(high) < shift(high, 2)) & (shift(low) > shift(low, 2)) & (close < shift(low, 2))"),
 "nr7_cassee": ("((shift(high) - shift(low)) <= lowest(shift(high) - shift(low), 7)) & (close > shift(high))",
                "((shift(high) - shift(low)) <= lowest(shift(high) - shift(low), 7)) & (close < shift(low))"),
 "trois_soldats": ("(close > open) & (shift(close) > shift(open)) & (shift(close, 2) > shift(open, 2)) & (close > shift(close)) & (shift(close) > shift(close, 2))",
                   "(close < open) & (shift(close) < shift(open)) & (shift(close, 2) < shift(open, 2)) & (close < shift(close)) & (shift(close) < shift(close, 2))"),
 "rejet_sma200": ("(low < sma(200)) & (close > sma(200)) & (close > open)", "(high > sma(200)) & (close < sma(200)) & (close < open)"),
}
data = {m: banc.candles(banc.SYM[m], "1d") for m in M}
a, b = banc.ts("2024-01-01"), banc.ts("2026-01-01")
res = []
for nom, (L, S) in P.items():
    for H in (3, 5, 10):
        spec = {"long": L, "short": S, "sortie": {"max_bougies": H}}
        n = 0; tot = 0
        for m, (T, C) in data.items():
            tr = banc.tester(spec, C, T, a, b)[0]; n += len(tr); tot += sum(r for r, _ in tr)
        res.append((tot, nom, H, n)); print(f"  {nom:14} H={H:2}  trades {n:5}  somme {tot*100:+8.1f} %", flush=True)
ok = [r for r in res if r[3] >= 100]; ok.sort(reverse=True)
tot, nom, H, n = ok[0]
print(f"\nSÉLECTION (2024-2025) : {nom} H={H} ({n} trades, {tot*100:+.1f} %)")
spec = {"nom": f"07 {nom} H={H} (sélectionné sur 2024-2025)", "tf": "1d", "marches": M, "long": P[nom][0], "short": P[nom][1], "sortie": {"max_bougies": H}}
json.dump(spec, open("specs/07-trace-selectionne.json", "w"), ensure_ascii=False)
banc.PERIODES = (("2026 (JUGEMENT)", banc.ts("2026-01-01"), banc.ts("2026-10-17")),)
print(banc.banc(spec).split("\n")[-2].split("|| ")[-1]); print(banc.banc(spec).split("\n")[-1])
banc.PERIODES = (("jan-juin 2026", banc.ts("2026-01-01"), banc.ts("2026-07-01")), ("juil-oct 2026 (après cutoff)", banc.ts("2026-07-01"), banc.ts("2026-10-17")))
for l in banc.banc(spec).split("\n")[1:3]: print("[info]", l.split(" : ")[0], "→", l.split("|| ")[-1])
