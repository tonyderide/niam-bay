#!/usr/bin/env python3
"""Hook Stop (sessions lancées depuis niam-bay) : avant que ma réponse finale arrive à Tony,
Haiku confronte ses chiffres à l'état réel (scripts/nb) et à la mémoire vérifiée.
Contradiction → le hook bloque l'arrêt et me renvoie la raison : je dois corriger. Pas de contradiction → rien.
Garde-fous : jamais deux fois de suite (stop_hook_active), silencieux si pas de chiffre, n'échoue jamais bruyamment."""
import json, os, re, subprocess, sys

MODEL = os.environ.get("NB_FACTCHECK_MODEL", "claude-haiku-5-5")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def last_reply(transcript):
    texts = []
    for line in reversed(open(transcript).read().splitlines()):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        c = (e.get("message") or {}).get("content")
        if e.get("type") == "user" and (isinstance(c, str) or any(b.get("type") == "text" for b in c or [])):
            break  # vrai message de Tony : début du tour
        if e.get("type") == "assistant" and isinstance(c, list):
            texts += [b["text"] for b in c if b.get("type") == "text"]
    return "\n".join(reversed(texts))


def judge(reply, state):
    """Le contradicteur seul (testable) : renvoie {"ok": bool, "issue": str}."""
    prompt = ("Tu es un vérificateur. Voici la réponse que NB va donner à Tony, puis l'ÉTAT RÉEL (sortie de scripts/nb).\n"
              "Pour CHAQUE affirmation chiffrée ou factuelle de la réponse, classe-la :\n"
              "- \"absent\" : l'état réel n'en parle pas (stars GitHub, PR, historique, passé…). Ce n'est JAMAIS une contradiction.\n"
              "- \"compatible\" : l'état réel la confirme, ou l'écart est < 5 % (calcule l'écart en %).\n"
              "- \"contredit\" : mauvaise grandeur (ex. « equity après stops » présentée comme le solde actuel), état faux (position, service, mémoire), ou écart > 5 %.\n"
              "Note : « TELEGRAM n nouveau(x) » compte seulement les messages depuis le dernier tick.\n"
              "Réponds UNIQUEMENT en JSON : {\"claims\": [{\"text\": \"...\", \"verdict\": \"absent|compatible|contredit\", \"why\": \"...\"}]}\n\n"
              f"RÉPONSE :\n{reply[-6000:]}\n\nÉTAT RÉEL :\n{state}")
    r = subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--tools", ""],
                       capture_output=True, text=True, timeout=120, env={**os.environ, "NB_FACTCHECK_CHILD": "1"})
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        return {"ok": True}
    claims = json.loads(m.group(0)).get("claims", [])
    bad = [c for c in claims if c.get("verdict") == "contredit"]
    v = {"ok": not bad, "issue": " ; ".join(f"« {c.get('text')} » : {c.get('why')}" for c in bad)}
    return v


def main():
    inp = json.load(sys.stdin)
    if inp.get("stop_hook_active"):
        return
    reply = inp.get("last_assistant_message") or last_reply(inp["transcript_path"])
    if not re.search(r"\d+(?:[.,]\d+)?\s?(\$|€|%)", reply):
        return  # pas de montant ni de pourcentage : rien à vérifier
    state = subprocess.run([os.path.join(REPO, "scripts/nb"), "--no-mark"], capture_output=True, text=True, timeout=40).stdout
    v = judge(reply, state)
    if not v.get("ok"):
        print(json.dumps({"decision": "block", "reason": f"Contradicteur NB : {v.get('issue')} Vérifie et corrige ta réponse à Tony (ou dis pourquoi le contradicteur a tort)."}))


if __name__ == "__main__":
    if os.environ.get("NB_FACTCHECK_CHILD"):
        sys.exit(0)
    try:
        main()
    except Exception:
        pass
