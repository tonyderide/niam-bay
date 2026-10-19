"""Écart de funding Hyperliquid / Kraken Futures sur 30 jours (API publiques, lecture seule). Étape 2 de la charte du CTO, mesure seule."""
import json, time, urllib.request, statistics as st
H = 3600; now = int(time.time()); t0 = now - 30 * 86400
def hl(coin):
    r = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps({"type": "fundingHistory", "coin": coin, "startTime": t0 * 1000}).encode(), headers={"Content-Type": "application/json"})
    out = {}; d = json.load(urllib.request.urlopen(r, timeout=30))
    for x in d: out[int(x["time"]) // 1000 // H * H] = float(x["fundingRate"])  # par heure
    return out
def kr(sym):
    d = json.load(urllib.request.urlopen(f"https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol={sym}", timeout=30))["rates"]
    out = {}
    for x in d:
        t = int(time.mktime(time.strptime(x["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))) - time.timezone
        if t >= t0: out[t // H * H] = float(x["relativeFundingRate"])  # par heure (Kraken PF : funding horaire)
    return out
FEES = 4 * 0.0005  # 4 jambes (entrée et sortie des deux côtés), taker 0,05 %
for coin, sym in (("BTC", "PF_XBTUSD"), ("ETH", "PF_ETHUSD"), ("SOL", "PF_SOLUSD")):
    a, b = hl(coin), kr(sym); time.sleep(1)
    common = sorted(set(a) & set(b))
    if len(common) < 24: print(coin, "pas assez d'heures communes", len(a), len(b)); continue
    diff = [a[t] - b[t] for t in common]  # >0 : Hyperliquid paie plus → short HL / long Kraken encaisse diff
    m = st.mean(diff); same = sum(1 for x in diff if (x > 0) == (m > 0)) / len(diff)
    gross30 = abs(m) * 24 * 30
    print(f"{coin}: {len(common)} h | écart moyen {m*100:+.5f} %/h ({m*24*365*100:+.1f} %/an) | même signe {same:.0%} des heures | "
          f"30 j couverts : brut {gross30*100:+.3f} % − frais {FEES*100:.2f} % = net {(gross30-FEES)*100:+.3f} % | sur 3,8 $ : {(gross30-FEES)*3.8:+.4f} $")
