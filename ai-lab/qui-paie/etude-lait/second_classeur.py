"""Contrôle d'information (pas le verdict pré-enregistré) : refait le classement à l'aveugle avec un second modèle (sonnet)."""
import json, re, subprocess, sys
import etude as E

def claude2(texte):
    r = subprocess.run(["claude", "-p", "--model", "claude-sonnet-5-5", "--tools", "", "--output-format", "json",
                        "--no-session-persistence", "--strict-mcp-config", "--setting-sources", ""],
                       input=texte, capture_output=True, text=True, timeout=240, cwd="/tmp")
    return json.loads(re.search(r"\{.*\}", json.loads(r.stdout)["result"], re.S).group(0))["classe"]

A = json.load(open("corpus2.json"))
for a in A:
    if a.get("classe_sonnet"):
        continue
    try:
        a["classe_sonnet"] = claude2(E.CONSIGNE.replace("{titre}", a["titre"]).replace("{resume}", a["resume"][:6000]))
    except Exception as e:
        a["classe_sonnet"] = None; print("erreur", a["pmid"], e, flush=True)
    json.dump(A, open("corpus2.json", "w"), ensure_ascii=False, indent=1); print(a["pmid"], a["classe"], a["classe_sonnet"], flush=True)
