"""NB à voix haute : la réponse de Claude arrive en flux, chaque phrase est dite dès qu'elle est complète (Piper, local).
But : premier son en ~2 s, comme le mode vocal de l'appli Anthropic, mais avec la mémoire et les outils de NB.
Usage : nb_voix.py              -> micro : Entrée, tu parles, je réponds (arrêt auto au silence) ; « au revoir » pour finir
        nb_voix.py --clavier     -> tu tapes, je parle
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


class Oreilles:
    """Micro (PipeWire/Pulse) -> faster-whisper en local. Arrêt quand tu te tais ~0,9 s."""
    def __init__(self):
        from faster_whisper import WhisperModel
        self.m = WhisperModel(os.environ.get("NB_STT", "small"), device="cpu", compute_type="int8")

    def ecouter(self, max_s=25):
        rec = subprocess.Popen(["parec", "--raw", "--rate=16000", "--format=s16le", "--channels=1"], stdout=subprocess.PIPE)
        trame = 480 * 2; fond = []; audio = bytearray(); parle = False; silence = 0; t0 = time.time()
        while time.time() - t0 < max_s:
            b = rec.stdout.read(trame); a = array.array("h", b); rms = math.sqrt(sum(x * x for x in a) / max(1, len(a)))
            if len(fond) < 15: fond.append(rms); continue          # 0,45 s pour mesurer le bruit de fond
            seuil = max(350, 3 * sorted(fond)[len(fond) // 2])
            if rms > seuil: parle = True; silence = 0
            elif parle: silence += 1
            if parle: audio += b
            if parle and silence > 30: break                          # ~0,9 s de silence après la parole
        rec.terminate()
        if len(audio) < 16000: return ""
        import numpy as np
        segs, _ = self.m.transcribe(np.frombuffer(bytes(audio), np.int16).astype(np.float32) / 32768, language="fr", beam_size=1, vad_filter=True)
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


def main():
    bouche, cerveau = Bouche(), Cerveau()
    if len(sys.argv) > 1 and sys.argv[1] != "--clavier":
        questions = [" ".join(sys.argv[1:])]
    elif len(sys.argv) > 1:
        questions = iter(lambda: input("Toi > "), "")
    else:
        oreilles = Oreilles(); bouche.dire("Je t'écoute. Appuie sur Entrée, puis parle.")
        def micro():
            while True:
                input("\n[Entrée puis parle] "); t = time.time(); txt = oreilles.ecouter()
                print(f"Toi (entendu en {time.time() - t:.1f} s) : {txt or '(rien)'}")
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
