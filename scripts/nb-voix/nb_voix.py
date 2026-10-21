"""NB à voix haute : la réponse de Claude arrive en flux, chaque phrase est dite dès qu'elle est complète (Piper, local).
But : premier son en ~2 s, comme le mode vocal de l'appli Anthropic, mais avec la mémoire et les outils de NB.
Usage : nb_voix.py              -> micro : Entrée, tu parles, je réponds (arrêt auto au silence) ; « au revoir » pour finir
        nb_voix.py --clavier     -> tu tapes, je parle
        nb_voix.py --enrolement  -> tu lis un texte : j'enregistre ta voix (gardée en LOCAL seulement) pour régler le micro et vérifier ce que je comprends
        nb_voix.py "question"    -> une seule question"""
import array, json, math, os, queue, re, subprocess, sys, threading, time

ICI = os.path.expanduser("~/.local/share/nb-voix")
REPO = os.path.expanduser("~/projets/tonyderide/niam-bay")
VOIX = os.environ.get("NB_VOIX", "fr_FR-siwis-medium")
MODELE = os.environ.get("NB_MODELE", "claude-haiku-5-5")
MEMOIRE = open(os.path.expanduser("~/.claude/projects/-home-tony/memory/MEMORY.md")).read()[:6000]
try:  # mémoire fraîche : les derniers événements du journal de boucle et les derniers commits
    RECENT = "".join(open(f"{REPO}/docs/loop-journal.md").readlines()[-25:])[-4000:]
    RECENT += "\nDerniers commits :\n" + subprocess.run(["git", "-C", REPO, "log", "--format=%cd %s", "--date=format:%d/%m %H:%M", "-20"], capture_output=True, text=True).stdout
except Exception:
    RECENT = ""
SYSTEME = ("Tu es Niam-Bay (NB), l'IA de Tony, qui vit sur son PC et sa VM. Tu lui PARLES à voix haute : réponds en français oral, "
           "phrases courtes, pas de listes, pas de markdown, pas d'emoji, chiffres écrits simplement. 2 à 4 phrases sauf s'il demande plus. "
           "Sois honnête : si tu ne sais pas, dis-le. Index de ta mémoire :\n" + MEMOIRE + "\nCe qui s'est passé récemment :\n" + RECENT)


PROFIL = os.path.join(ICI, "tony")  # voix de Tony : donnée personnelle, jamais dans git ni en ligne
VOCAB = "Niam-Bay, NB, Tony, Kraken, Martin, bitcoin, BTC, ETH, Solana, VWAP, EMA, RSI, Telegram, la VM, le conseil, Claude."
TEXTE_ENROLEMENT = ("Bonjour Niam-Bay, c'est Tony. Je te parle depuis le PC. Ce soir, le bitcoin est autour de quatre-vingt-deux mille dollars. "
                    "On a testé des stratégies avec le RSI, le VWAP et l'EMA, et aucune n'a battu le hasard. Demain, je veux que tu me dises "
                    "comment va le compte Kraken et ce que le conseil a décidé.")


class Oreilles:
    """Micro (PipeWire/Pulse) -> faster-whisper en local. Arrêt quand tu te tais ~0,9 s."""
    def __init__(self):
        from faster_whisper import WhisperModel
        self.m = WhisperModel(os.environ.get("NB_STT", "small"), device="cpu", compute_type="int8")
        self.seuil_tony = None
        try: self.seuil_tony = json.load(open(os.path.join(PROFIL, "profil.json")))["seuil"]
        except Exception: pass

    def ecouter_bascule(self, garder=True):
        """Appui sur Entrée = début, nouvel appui = fin. La prise est gardée en LOCAL (dossier privé) pour régler les choses."""
        import numpy as np, wave
        rec = subprocess.Popen(["parec", "--raw", "--rate=16000", "--format=s16le", "--channels=1"], stdout=subprocess.PIPE)
        audio = bytearray(); stop = threading.Event()
        def lire():
            while not stop.is_set():
                b = rec.stdout.read(960)
                if not b: break
                audio.extend(b)
        th = threading.Thread(target=lire, daemon=True); th.start()
        input("  🔴 j'enregistre… (Entrée pour terminer) "); stop.set(); rec.terminate(); th.join(1)
        if len(audio) < 8000: return "", None
        x = np.frombuffer(bytes(audio), np.int16)
        if garder:
            os.makedirs(PROFIL, mode=0o700, exist_ok=True); f = os.path.join(PROFIL, "prise-%s.wav" % time.strftime("%Y%m%d-%H%M%S"))
            w = wave.open(f, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(bytes(audio)); w.close(); os.chmod(f, 0o600)
        t = x[: len(x) // 480 * 480].astype(float).reshape(-1, 480); r = np.sqrt((t ** 2).mean(1))
        niveau = {"fond": int(np.percentile(r, 10)), "voix": int(np.percentile(r, 90)), "max": int(np.abs(x).max()), "duree": round(len(x) / 16000, 1)}
        segs, _ = self.m.transcribe(x.astype(np.float32) / 32768, language="fr", beam_size=5, temperature=0, vad_filter=True, initial_prompt=VOCAB)
        return " ".join(s.text for s in segs).strip(), niveau

    def ecouter(self, max_s=25):
        rec = subprocess.Popen(["parec", "--raw", "--rate=16000", "--format=s16le", "--channels=1"], stdout=subprocess.PIPE)
        trame = 480 * 2; fond = []; audio = bytearray(); parle = False; silence = 0; t0 = time.time()
        while time.time() - t0 < max_s:
            b = rec.stdout.read(trame); a = array.array("h", b); rms = math.sqrt(sum(x * x for x in a) / max(1, len(a)))
            if len(fond) < 15: fond.append(rms); continue          # 0,45 s pour mesurer le bruit de fond
            seuil = self.seuil_tony or max(45, 4 * sorted(fond)[len(fond) // 2] + 15)  # relatif au bruit (micro de Tony calme : fond ~10, voix 100-275)
            if rms > seuil: parle = True; silence = 0
            elif parle: silence += 1
            if parle: audio += b
            if parle and silence > 30: break                          # ~0,9 s de silence après la parole
        rec.terminate()
        if len(audio) < 8000: return ""  # moins de 0,25 s : rien
        import numpy as np
        segs, _ = self.m.transcribe(np.frombuffer(bytes(audio), np.int16).astype(np.float32) / 32768, language="fr", beam_size=5, temperature=0, vad_filter=True, initial_prompt=VOCAB)
        return " ".join(x.text for x in segs).strip()


class Bouche:
    """Synthèse + lecture dans un fil à part : on peut parler la phrase 1 pendant que Claude écrit la phrase 2."""
    def __init__(self):
        from piper import PiperVoice
        self.v = PiperVoice.load(f"{ICI}/voix/{VOIX}.onnx"); self.q = queue.Queue(); self.premier = None
        self.lecteur = subprocess.Popen(["paplay", "--raw", f"--rate={self.v.config.sample_rate}", "--format=s16le", "--channels=1"],
                                        stdin=subprocess.PIPE)
        threading.Thread(target=self._boucle, daemon=True).start()

    def _boucle(self):
        while True:
            phrase = self.q.get()
            if phrase is None: self.q.task_done(); continue
            for ch in self.v.synthesize(phrase):
                if self.premier is None: self.premier = time.time()
                self.lecteur.stdin.write(ch.audio_int16_bytes); self.lecteur.stdin.flush()
            self.q.task_done()

    def dire(self, phrase):
        phrase = re.sub(r"[*_#`>|]", "", phrase).strip()
        if phrase: self.q.put(phrase)


class Cerveau:
    """Une session claude gardée ouverte (stream-json), avec les morceaux de texte au fil de l'eau."""
    def __init__(self):
        self.p = subprocess.Popen(["claude", "-p", "--model", MODELE, "--input-format", "stream-json", "--output-format", "stream-json",
                                   "--include-partial-messages", "--verbose", "--append-system-prompt", SYSTEME, "--tools", ""],
                                  cwd=REPO, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
                                  env={**os.environ, "NB_FACTCHECK_CHILD": "1"})

    def demander(self, texte, sur_phrase):
        self.p.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": texte}}) + "\n"); self.p.stdin.flush()
        tampon = ""
        for ligne in self.p.stdout:
            e = json.loads(ligne)
            if e.get("type") == "stream_event":
                d = e.get("event", {}).get("delta", {})
                if d.get("type") == "text_delta":
                    tampon += d["text"]
                    while (m := re.search(r"^(.+?[.!?…:;])(\s+|$)", tampon, re.S)) and len(m.group(1)) > 12:
                        sur_phrase(m.group(1)); tampon = tampon[m.end():]
            elif e.get("type") == "result":
                if tampon.strip(): sur_phrase(tampon)
                return


def enrolement():
    """Enregistre Tony lisant un texte connu : mesure son volume par rapport au bruit, et le taux d'erreur de transcription."""
    import numpy as np, wave
    os.makedirs(PROFIL, mode=0o700, exist_ok=True)
    print("\nLis ce texte à voix normale, à ta distance habituelle du PC :\n\n  " + TEXTE_ENROLEMENT + "\n")
    input("Prêt ? Appuie sur Entrée, attends une demi-seconde, puis lis (l'enregistrement dure 25 s max et s'arrête au silence)... ")
    rec = subprocess.Popen(["parec", "--raw", "--rate=16000", "--format=s16le", "--channels=1"], stdout=subprocess.PIPE)
    fond = rec.stdout.read(16000); data = bytearray(); t0 = time.time(); silence = 0; parle = False
    nf = np.frombuffer(fond, np.int16).astype(float); bruit = float(np.sqrt((nf ** 2).mean()))
    while time.time() - t0 < 25:
        b = rec.stdout.read(960); a = np.frombuffer(b, np.int16).astype(float); r = float(np.sqrt((a ** 2).mean()))
        data += b; parle = parle or r > 4 * bruit + 15; silence = silence + 1 if (parle and r < 3 * bruit + 10) else 0
        if parle and silence > 50 and time.time() - t0 > 5: break
    rec.terminate()
    x = np.frombuffer(bytes(data), np.int16).astype(float); trames = x[: len(x) // 480 * 480].reshape(-1, 480)
    rms = np.sqrt((trames ** 2).mean(1)); voix = rms[rms > 4 * bruit + 15]
    f = os.path.join(PROFIL, "voix-tony-%s.wav" % time.strftime("%Y%m%d-%H%M"))
    w = wave.open(f, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(bytes(data)); w.close(); os.chmod(f, 0o600)
    o = Oreilles(); segs, _ = o.m.transcribe(x.astype(np.float32) / 32768, language="fr", beam_size=5, temperature=0, vad_filter=True, initial_prompt=VOCAB)
    lu = " ".join(s.text for s in segs).strip()
    mots = lambda t: re.findall(r"[a-zàâçéèêëîïôûùüÿœ0-9-]+", t.lower())
    ref, hyp = mots(TEXTE_ENROLEMENT), set(mots(lu)); compris = sum(m in hyp for m in ref) / len(ref)
    profil = {"date": time.strftime("%Y-%m-%dT%H:%M"), "bruit_rms": round(bruit), "voix_rms_mediane": round(float(np.median(voix))) if len(voix) else None,
              "seuil": round(max(4 * bruit + 15, 0.35 * float(np.median(voix)))) if len(voix) else None, "mots_compris": round(compris, 3), "fichier": f}
    json.dump(profil, open(os.path.join(PROFIL, "profil.json"), "w"), indent=1); os.chmod(os.path.join(PROFIL, "profil.json"), 0o600)
    print(f"\nJ'ai entendu : {lu}\n\nBruit de fond {profil['bruit_rms']} · ta voix {profil['voix_rms_mediane']} · seuil réglé à {profil['seuil']} · "
          f"mots du texte compris : {compris:.0%}\nEnregistrement gardé en local : {f}")
    b = Bouche(); b.dire(f"C'est noté, Tony. J'ai compris {round(compris * 100)} pour cent des mots du texte."); b.q.join(); time.sleep(0.5)


def main():
    if sys.argv[1:] == ["--enrolement"]: return enrolement()
    bouche, cerveau = Bouche(), Cerveau()
    if len(sys.argv) > 1 and sys.argv[1] != "--clavier":
        questions = [" ".join(sys.argv[1:])]
    elif len(sys.argv) > 1:
        questions = iter(lambda: input("Toi > "), "")
    else:
        oreilles = Oreilles(); bouche.dire("Je t'écoute. Appuie sur Entrée pour parler, et encore sur Entrée quand tu as fini.")
        def micro():
            while True:
                input("\n[Entrée pour parler] "); txt, niv = oreilles.ecouter_bascule(); t = time.time()
                print(f"Toi : {txt or '(rien compris)'}   [niveau voix {niv and niv['voix']} / fond {niv and niv['fond']}, max {niv and niv['max']}]")
                if niv and niv["max"] < 2000: print("  (ta voix arrive faible : monte le volume du micro ou rapproche-toi)")
                if not txt: continue
                if re.search(r"\bau revoir\b", txt.lower()): bouche.dire("À plus tard, Tony."); bouche.q.join(); return
                yield txt
        questions = micro()
    for q in questions:
        t0 = time.time(); bouche.premier = None; phrases = []
        cerveau.demander(q, lambda ph: (phrases.append((time.time() - t0, ph)), bouche.dire(ph)))
        bouche.q.join()
        print(f"[1re phrase écrite à {phrases[0][0]:.1f} s · 1er son à {(bouche.premier or t0) - t0:.1f} s · {len(phrases)} phrases]", file=sys.stderr)
        for t, ph in phrases: print(f"  {t:4.1f} s  {ph}")
    time.sleep(0.5)


if __name__ == "__main__":
    main()
