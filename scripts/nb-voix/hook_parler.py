"""Hook Stop de Claude Code : NB dit à voix haute (Piper, local) le texte de sa dernière réponse.
Interrupteur : ne parle QUE si ~/.local/share/nb-voix/voix.on existe (le hook est global, les autres sessions restent muettes).
Rend la main tout de suite : la parole tourne dans un processus détaché ; une nouvelle réponse coupe l'ancienne."""
import json, os, re, subprocess, sys

ICI = os.path.expanduser("~/.local/share/nb-voix")
INTER, PIDF = os.path.join(ICI, "voix.on"), os.path.join(ICI, "parle.pid")
MAX = 700  # caractères dits ; le reste est à l'écran


def dernier_texte(transcript):
    """Texte des messages assistant depuis le dernier vrai message de Tony."""
    morceaux = []
    for ligne in open(transcript, encoding="utf-8", errors="replace"):
        try: e = json.loads(ligne)
        except Exception: continue
        m = e.get("message") or {}
        if e.get("type") == "user" and isinstance(m.get("content"), str): morceaux = []          # nouveau message de Tony
        elif e.get("type") == "user" and any(c.get("type") == "text" for c in m.get("content", []) if isinstance(c, dict)): morceaux = []
        elif e.get("type") == "assistant":
            morceaux += [c["text"] for c in m.get("content", []) if isinstance(c, dict) and c.get("type") == "text"]
    return "\n".join(morceaux)


def tour_de_boucle(transcript):
    """Vrai si le dernier message « utilisateur » est un réveil /loop (pas Tony au clavier)."""
    dernier = ""
    try:
        for ligne in open(transcript, encoding="utf-8", errors="replace"):
            try: e = json.loads(ligne)
            except Exception: continue
            c = (e.get("message") or {}).get("content")
            if e.get("type") == "user" and isinstance(c, str): dernier = c
    except Exception: pass
    return "<command-name>/loop" in dernier


def oral(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)                       # blocs de code
    t = "\n".join(l for l in t.splitlines() if not l.strip().startswith("|"))  # tableaux
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)                      # liens markdown -> texte
    t = re.sub(r"https?://\S+|`[^`]*`", " ", t)                         # URL, code en ligne
    t = re.sub(r"[*_#>~]|^\s*[-•]\s*|^\s*\d+\.\s+", " ", t, flags=re.M)
    t = re.sub(r"[^\w\s,.;:!?'’«»()%€$/-]", " ", t)                     # emoji et symboles
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > MAX:
        coupe = t[:MAX]; fin = max(coupe.rfind(". "), coupe.rfind("! "), coupe.rfind("? "))
        t = (coupe[: fin + 1] if fin > 200 else coupe) + " La suite est à l'écran."
    return t


def main():
    d = json.load(sys.stdin)
    if d.get("stop_hook_active"): return
    brut = d.get("last_assistant_message") or dernier_texte(d.get("transcript_path", ""))
    relais = (d.get("cwd") or "").startswith("/tmp")                                  # petites sessions du micro (claude -p, cwd=/tmp) : leur « OK » n'est pas moi
    bruit = relais or (len(brut or "") < 400 and tour_de_boucle(d.get("transcript_path", "")))   # « hors fenêtre, je dors » : pas pour le fil
    if brut and not bruit and os.path.exists(os.path.join(ICI, "fil.on")):   # NB-OS : ma réponse de session rejoint le fil commun
        q = subprocess.Popen(["ssh", "-i", os.path.expanduser("~/.ssh/martin_vm.key"), "-o", "ConnectTimeout=8", "ubuntu@141.253.108.141",
                              "python3 ~/nb/fil.py ecrire session nb"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        q.stdin.write(oral(brut).encode()); q.stdin.close()
    if not os.path.exists(INTER): return
    texte = oral(brut)
    if not texte: return
    try: os.kill(int(open(PIDF).read()), 15)                            # coupe la phrase précédente
    except Exception: pass
    p = subprocess.Popen([os.path.join(ICI, "venv/bin/python"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "dire.py")],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    p.stdin.write(texte.encode()); p.stdin.close(); open(PIDF, "w").write(str(p.pid))


if __name__ == "__main__":
    try: main()
    except Exception: pass   # un hook de voix ne doit jamais bloquer la session
