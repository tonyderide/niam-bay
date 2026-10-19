"""L'alarme de l'angle mort (conseil 1019, 6.55) : DRAPEAU, jamais verdict.
Si une affirmation date un fait APRÈS la date limite de connaissances du modèle qui l'a écrite, on demande une source :
le modèle ne pouvait pas le savoir sans recherche."""
import re
CUTOFF = {"claude-opus-5-5": (2026, 6), "claude-sonnet-5-5": (2026, 6), "claude-haiku-5-5": (2026, 6)}  # (année, mois) ; à compléter quand Tony dit quel modèle
MOIS = {m: i + 1 for i, m in enumerate(["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"])}


def dates(text):
    t = text.lower(); out = []
    for m, y in re.findall(r"\b(" + "|".join(MOIS) + r")\s+(20\d\d)\b", t): out.append((int(y), MOIS[m]))
    for d, mo, y in re.findall(r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\b", t): out.append((int(y), int(mo)))
    for y in re.findall(r"\b(20\d\d)\b", t):
        if not any(o[0] == int(y) for o in out): out.append((int(y), 12 if int(y) > 0 else 1))  # année seule : on suppose la fin d'année (prudent)
    return out


def flag(claim, auteur):
    cut = CUTOFF.get(auteur)
    if not cut: return None
    late = [d for d in dates(claim) if d > cut]
    return f"⏳ angle mort : {auteur} s'arrête en {cut[1]:02d}/{cut[0]}, ce fait date de {late[0][1]:02d}/{late[0][0]} → demande-lui sa source" if late else None
