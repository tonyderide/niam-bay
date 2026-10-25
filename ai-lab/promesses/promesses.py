"""Compteur de promesses : retrouve, dans les transcriptions de mes sessions, ce que j'ai PROMIS à Tony
(« je te dis quand… », « je repasse à 1h », « je te préviens »…), pour vérifier ensuite que je l'ai tenu.
Usage : python3 promesses.py [--heures 48] [transcriptions.jsonl ...]   (défaut : les sessions des dernières heures)
Sortie : liste datée ; la vérification « tenue / pas tenue » reste un jugement, noté à la main dans le journal."""
import argparse, glob, json, os, re, time

DOSSIER = os.path.expanduser("~/.claude/projects/-home-tony")
MOTIFS = re.compile(
    r"(je (te|vous) (dis|dirai|préviens|préviendrai|recontacte|redis|fais signe|tiens au courant)\b[^.\n]{0,90}"
    r"|je (repasse|reviens|regarde|vérifie|relance|surveille|refais le point)[^.\n]{0,40}\b(à|vers|dans|demain|ce soir|cette nuit|lundi|mardi)\b[^.\n]{0,60}"
    r"|je m'en (occupe|charge)[^.\n]{0,80}"
    r"|(c'est|ça sera) prêt (pour|avant|d'ici)[^.\n]{0,60}"
    r"|prochain (point|passage|tour) (vers|à)[^.\n]{0,40})", re.I)


def textes(fichier, depuis):
    for ligne in open(fichier, errors="replace"):
        try:
            d = json.loads(ligne)
        except ValueError:
            continue
        if d.get("type") != "assistant" or d.get("isSidechain"):
            continue
        t = d.get("timestamp", "")
        try:
            instant = time.mktime(time.strptime(t[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
        except ValueError:
            continue
        if instant < depuis:
            continue
        for bloc in d.get("message", {}).get("content", []):
            if isinstance(bloc, dict) and bloc.get("type") == "text":
                yield instant, bloc["text"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("fichiers", nargs="*"); ap.add_argument("--heures", type=float, default=48)
    a = ap.parse_args(); depuis = time.time() - a.heures * 3600
    fichiers = a.fichiers or [f for f in glob.glob(os.path.join(DOSSIER, "*.jsonl")) if os.path.getmtime(f) >= depuis]
    vus = set(); lignes = []
    for f in fichiers:
        for instant, texte in textes(f, depuis):
            for m in MOTIFS.finditer(texte):
                avant = texte[max(0, m.start() - 40):m.start()]
                if avant.count("«") > avant.count("»") or "`" in avant[-3:] or avant.rstrip().endswith(("Si", "si", "Quand")):
                    continue  # promesse citée, écrite pour quelqu'un d'autre, ou conditionnelle
                p = " ".join(m.group(0).split())
                cle = p.lower()[:60]
                if cle not in vus:
                    vus.add(cle); lignes.append((instant, p))
    for instant, p in sorted(lignes):
        print(f"- {time.strftime('%d/%m %H:%M', time.localtime(instant))} : « {p} »")
    print(f"\n{len(lignes)} promesse(s) sur {a.heures:.0f} h.")


if __name__ == "__main__":
    main()
