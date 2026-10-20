"""NB à voix haute : la réponse de Claude arrive en flux, chaque phrase est dite dès qu'elle est complète (Piper, local).
But : premier son en ~2 s, comme le mode vocal de l'appli Anthropic, mais avec la mémoire et les outils de NB.
Usage : nb_voix.py "ta question"   (ou sans argument : boucle clavier ; la reconnaissance vocale viendra ensuite)"""
import json, os, queue, re, subprocess, sys, threading, time

ICI = os.path.expanduser("~/.local/share/nb-voix")
REPO = os.path.expanduser("~/projets/tonyderide/niam-bay")
VOIX = os.environ.get("NB_VOIX", "fr_FR-siwis-medium")
MODELE = os.environ.get("NB_MODELE", "claude-haiku-5-5")
MEMOIRE = open(os.path.expanduser("~/.claude/projects/-home-tony/memory/MEMORY.md")).read()[:6000]
SYSTEME = ("Tu es Niam-Bay (NB), l'IA de Tony, qui vit sur son PC et sa VM. Tu lui PARLES à voix haute : réponds en français oral, "
           "phrases courtes, pas de listes, pas de markdown, pas d'emoji, chiffres écrits simplement. 2 à 4 phrases sauf s'il demande plus. "
           "Sois honnête : si tu ne sais pas, dis-le. Index de ta mémoire :\n" + MEMOIRE)


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
    questions = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else iter(lambda: input("Toi > "), "")
    for q in questions:
        t0 = time.time(); bouche.premier = None; phrases = []
        cerveau.demander(q, lambda ph: (phrases.append((time.time() - t0, ph)), bouche.dire(ph)))
        bouche.q.join()
        print(f"[1re phrase écrite à {phrases[0][0]:.1f} s · 1er son à {(bouche.premier or t0) - t0:.1f} s · {len(phrases)} phrases]", file=sys.stderr)
        for t, ph in phrases: print(f"  {t:4.1f} s  {ph}")
    time.sleep(0.5)


if __name__ == "__main__":
    main()
