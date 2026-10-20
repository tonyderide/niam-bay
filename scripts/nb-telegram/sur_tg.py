"""/sur : le carnet des certitudes (conseil OUI 7,09, 1021). Tony écrit une certitude en français, NB la fige sur la VM,
le résolveur de la VM la tranche seul à l'échéance (prix historique Kraken). Prototype : prix des cryptos seulement."""
import datetime, json, os, re, subprocess, urllib.request

MARCHES = "BTC ETH SOL XRP DOGE ADA LINK AVAX DOT LTC BCH UNI ATOM NEAR FIL AAVE APT OP TRX XLM ETC".split()
VM = ["ssh", "-i", os.path.expanduser("~/.ssh/martin_vm.key"), "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "ubuntu@141.253.108.141"]
CMD = 'python3 -c "import json,urllib.request,sys;print(json.load(urllib.request.urlopen(\\"https://futures.kraken.com/derivatives/api/v3/tickers/\\"+sys.argv[1],timeout=20))[\\"ticker\\"][\\"markPrice\\"])" '
PROMPT = """Nous sommes le {now} (heure de Paris). Tony écrit une certitude : « {texte} ».
Traduis-la en JSON UNIQUEMENT : {{"ok": true|false, "raison": "si ok=false, pourquoi (une phrase)", "marche": "BTC|ETH|SOL|...",
"sens": ">" ou "<", "seuil": nombre en dollars ou null (null = le prix actuel), "echeance": "AAAA-MM-JJTHH:MM" en heure de Paris, "p": probabilité entre 0 et 1}}.
Marchés possibles : {marches}. Seules les certitudes sur le PRIX d'une de ces cryptos à une date précise sont acceptées (sinon ok=false).
« fin du mois » = dernier jour à 23:59 ; « vendredi » = le prochain vendredi à 23:59 ; sans date, ok=false. Sans pourcentage, ok=false (demande à Tony d'en donner un)."""


def mark(sym):
    return float(json.load(urllib.request.urlopen(f"https://futures.kraken.com/derivatives/api/v3/tickers/PF_{'XBT' if sym == 'BTC' else sym}USD", timeout=20))["ticker"]["markPrice"])


def sceller(texte):
    if not texte.strip():
        return "Écris ta certitude après /sur, par ex. : /sur 80 % que l'ETH soit au-dessus de 4000 $ vendredi"
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    r = subprocess.run(["claude", "-p", PROMPT.format(now=now, texte=texte, marches=" ".join(MARCHES)), "--model", "claude-sonnet-5-5", "--tools", ""],
                       capture_output=True, text=True, timeout=120, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    try:
        j = json.loads(re.search(r"\{.*\}", r.stdout, re.S).group(0))
    except Exception:
        return "Je n'ai pas compris, reformule (crypto + seuil + date + ton %)."
    if not j.get("ok"):
        return "Pas encore possible : " + j.get("raison", "?") + "\n(Pour l'instant je ne sais trancher tout seul que les prix des cryptos.)"
    sym, p, ech = j["marche"].upper(), float(j["p"]), j["echeance"]
    if sym not in MARCHES or not (0 <= p <= 1) or ech <= now or ech > (datetime.datetime.now() + datetime.timedelta(days=366)).strftime("%Y-%m-%dT%H:%M"):
        return f"Je refuse de sceller ça tel quel (marché {sym}, p={p}, échéance {ech}) : vérifie la crypto, le % et la date."
    seuil = float(j["seuil"]) if j.get("seuil") else mark(sym)
    pf = f"PF_{'XBT' if sym == 'BTC' else sym}USD"
    pred = {"id": f"tony-sur-{sym}-{datetime.datetime.now().strftime('%m%d%H%M')}", "family": "tony",
            "claim": f"{sym} mark {'au-dessus' if j['sens'] == '>' else 'en dessous'} de {seuil:,.4g} $ le {ech.replace('T', ' à ')} (Paris)",
            "p": p, "why": f"Tony, via /sur : « {texte} »", "baselines": {"p05": 0.5}, "made": now, "resolve_at": ech,
            "cmd": CMD + pf, "test": f"float(out){j['sens']}{seuil!r}", "outcome": None}
    code = ("import json,sys;P=json.load(open('predictions.json'));x=json.loads(sys.stdin.read());"
            "assert all(y['id']!=x['id'] for y in P);P.append(x);json.dump(P,open('predictions.json','w'),ensure_ascii=False,indent=1);print('ok')")
    s = subprocess.run(VM + [f"cd ~/nb/calibration && python3 -c \"{code}\""], input=json.dumps(pred, ensure_ascii=False), capture_output=True, text=True, timeout=40)
    if "ok" not in s.stdout:
        return "⚠️ Échec du scellé sur la VM, rien n'est enregistré."
    return (f"🔒 Scellé : {pred['claim']}\nTa certitude : {p:.0%}\nJe tranche tout seul à l'échéance avec le prix historique de Kraken."
            f"\nTape /certitudes pour voir ton taux de vérité.")
