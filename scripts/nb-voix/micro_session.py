"""Les oreilles de NB pour une session Claude Code : Entrée -> tu parles -> Entrée ; transcription locale (faster-whisper),
vérification que c'est la voix de Tony (empreinte locale), puis envoi du texte dans la session via la messagerie entre sessions.
La réponse revient à voix haute grâce au hook Stop (hook_parler.py). Aucun copier-coller.
Usage : micro_session.py [nom-de-session] [--bouton]
  par défaut MAINS LIBRES : j'écoute en continu, je démarre quand tu parles, j'arrête après 3 s de silence, je n'écoute pas pendant que je parle.
  --bouton : Entrée pour parler, Entrée pour finir."""
import os, subprocess, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locuteur
from nb_voix import Oreilles, ICI

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SESSION = ARGS[0] if ARGS else "tony-e4"
BOUTON = "--bouton" in sys.argv
SILENCE_FIN = 3.0   # secondes de silence pour être sûr que Tony a fini (demande de Tony, 1021)
PIDF = os.path.join(ICI, "parle.pid")


def taire_nb():
    try: os.kill(int(open(PIDF).read()), 15)
    except Exception: pass


def nb_parle():
    try: os.kill(int(open(PIDF).read()), 0); return True
    except Exception: return False


def ecouter_mains_libres():
    """Écoute continue : démarre sur la voix, finit après SILENCE_FIN s de silence. Pendant que NB parle, on n'écoute pas."""
    import array, collections, math, wave
    rec = subprocess.Popen(["parec", "--raw", "--rate=16000", "--format=s16le", "--channels=1"], stdout=subprocess.PIPE)
    T = 960; fond = collections.deque(maxlen=200); avant = collections.deque(maxlen=10)   # 30 ms par trame ; 0,3 s de pré-écoute
    audio = bytearray(); parle = False; fort = 0; silence = 0; calme_depuis = 0
    try:
        while True:
            b = rec.stdout.read(T); a = array.array("h", b); r = math.sqrt(sum(v * v for v in a) / max(1, len(a)))
            if nb_parle(): audio.clear(); parle = False; fort = silence = 0; calme_depuis = time.time(); continue
            if time.time() - calme_depuis < 0.6: continue                       # la fin de ma propre voix résonne encore
            if not parle: fond.append(r)
            seuil = max(45, 4 * sorted(fond)[len(fond) // 2] + 15) if len(fond) > 15 else 1e9
            if not parle:
                avant.append(b); fort = fort + 1 if r > seuil else 0
                if fort >= 3: parle = True; audio = bytearray(b"".join(avant)); silence = 0; print("  🔴 je t'entends…", flush=True)
                continue
            audio += b; silence = silence + 1 if r < seuil * 0.8 else 0
            if silence * 0.03 >= SILENCE_FIN or len(audio) > 16000 * 2 * 90:
                if len(audio) > 16000 * 2 * (SILENCE_FIN + 0.6): return bytes(audio[: len(audio) - int(silence * T * 0.9)])
                parle = False; audio.clear(); fort = 0                        # bruit bref : on oublie
    finally:
        rec.terminate()


def envoyer(texte):
    """Une petite session Claude sans écran fait un SendMessage vers la session de Tony (le seul chemin officiel trouvé)."""
    consigne = (f"Utilise l'outil SendMessage (charge-le avec ToolSearch 'select:SendMessage' si besoin) pour envoyer EXACTEMENT ce message "
                f"à la session {SESSION}, sans rien changer ni ajouter :\n[voix de Tony] {texte}\nRéponds ensuite seulement OK ou l'erreur.")
    r = subprocess.run(["claude", "-p", consigne, "--model", "claude-haiku-5-5"], cwd="/tmp", capture_output=True, text=True, timeout=120)
    return "OK" in r.stdout, r.stdout.strip()[-200:]


def main():
    print(f"Oreilles de NB → session {SESSION}. Ctrl+C pour quitter.")
    o = Oreilles()
    if not os.path.exists(locuteur.EMPREINTE): print("(pas encore d'empreinte vocale : je ne vérifie pas que c'est toi)")
    if not BOUTON: print(f"MAINS LIBRES : parle quand tu veux, j'envoie après {SILENCE_FIN:.0f} s de silence.")
    while True:
        if BOUTON:
            input("\n[Entrée pour parler] "); taire_nb()
            texte, niv = o.ecouter_bascule()
            prises = sorted(f for f in os.listdir(os.path.join(ICI, "tony")) if f.startswith("prise-"))
            x = locuteur.lire(os.path.join(ICI, "tony", prises[-1]))
        else:
            print("\n👂 j'écoute…", flush=True); x = np.frombuffer(ecouter_mains_libres(), np.int16)
            segs, _ = o.m.transcribe(x.astype(np.float32) / 32768, language="fr", beam_size=1, vad_filter=True, initial_prompt=__import__("nb_voix").VOCAB)
            texte = " ".join(sg.text for sg in segs).strip()
        if not texte: print("(rien compris)"); continue
        ok, s = locuteur.est_tony(x)
        print(f"Toi : {texte}   [voix {'reconnue' if ok else 'NON reconnue'}{f', score {s:.2f}' if s is not None else ''}]")
        if not ok:
            print("  → pas envoyé : ce n'était pas ta voix (ou trop court). Réessaie."); continue
        t = time.time(); ok, info = envoyer(texte)
        print(f"  → {'envoyé' if ok else 'ÉCHEC : ' + info} en {time.time() - t:.1f} s")


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nÀ plus tard.")
