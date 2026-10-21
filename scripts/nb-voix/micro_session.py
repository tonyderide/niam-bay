"""Les oreilles de NB pour une session Claude Code : Entrée -> tu parles -> Entrée ; transcription locale (faster-whisper),
vérification que c'est la voix de Tony (empreinte locale), puis envoi du texte dans la session via la messagerie entre sessions.
La réponse revient à voix haute grâce au hook Stop (hook_parler.py). Aucun copier-coller.
Usage : micro_session.py [nom-de-session]   (par défaut : tony-e4 ; le nom est affiché par ListAgents dans la session)"""
import os, subprocess, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locuteur
from nb_voix import Oreilles, ICI

SESSION = sys.argv[1] if len(sys.argv) > 1 else "tony-e4"
PIDF = os.path.join(ICI, "parle.pid")


def taire_nb():
    try: os.kill(int(open(PIDF).read()), 15)
    except Exception: pass


def envoyer(texte):
    """Une petite session Claude sans écran fait un SendMessage vers la session de Tony (le seul chemin officiel trouvé)."""
    consigne = (f"Utilise l'outil SendMessage (charge-le avec ToolSearch 'select:SendMessage' si besoin) pour envoyer EXACTEMENT ce message "
                f"à la session {SESSION}, sans rien changer ni ajouter :\n[voix de Tony] {texte}\nRéponds ensuite seulement OK ou l'erreur.")
    r = subprocess.run(["claude", "-p", consigne, "--model", "claude-haiku-5-5"], cwd="/tmp", capture_output=True, text=True, timeout=120)
    return "OK" in r.stdout, r.stdout.strip()[-200:]


def main():
    print(f"Oreilles de NB → session {SESSION}. Entrée pour parler, Entrée pour finir. Ctrl+C pour quitter.")
    o = Oreilles()
    if not os.path.exists(locuteur.EMPREINTE): print("(pas encore d'empreinte vocale : je ne vérifie pas que c'est toi)")
    while True:
        input("\n[Entrée pour parler] "); taire_nb()
        texte, niv = o.ecouter_bascule()
        if not texte: print("(rien compris)"); continue
        # la dernière prise est sur le disque ; on la relit pour la vérification de la voix
        prises = sorted(f for f in os.listdir(os.path.join(ICI, "tony")) if f.startswith("prise-"))
        x = locuteur.lire(os.path.join(ICI, "tony", prises[-1]))
        ok, s = locuteur.est_tony(x)
        print(f"Toi : {texte}   [voix {'reconnue' if ok else 'NON reconnue'}{f', score {s:.2f}' if s is not None else ''}]")
        if not ok:
            print("  → pas envoyé : ce n'était pas ta voix (ou trop court). Réessaie."); continue
        t = time.time(); ok, info = envoyer(texte)
        print(f"  → {'envoyé' if ok else 'ÉCHEC : ' + info} en {time.time() - t:.1f} s")


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nÀ plus tard.")
