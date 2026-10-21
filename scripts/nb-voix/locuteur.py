"""Est-ce bien Tony qui parle ? Empreinte vocale locale (WeSpeaker ResNet34, ONNX) comparée à celle de ses prises.
Tout reste sur le PC : modèle, prises et empreinte dans ~/.local/share/nb-voix (dossier tony/ en 0700).
Usage : locuteur.py --enroler   (calcule l'empreinte depuis les prises de ~/.local/share/nb-voix/tony/)"""
import glob, json, os, sys, wave
import numpy as np

ICI = os.path.expanduser("~/.local/share/nb-voix")
EMPREINTE = os.path.join(ICI, "tony", "empreinte.json")
_sess = None


def _fbank(x, sr=16000):
    """Banc de filtres mel log 80 façon Kaldi (25 ms / 10 ms, pré-accentuation, fenêtre de Povey), puis centrage."""
    x = x.astype(np.float64); n, h = 400, 160
    if len(x) < n: return None
    tr = np.lib.stride_tricks.sliding_window_view(x, n)[::h].copy()
    tr -= tr.mean(1, keepdims=True); tr[:, 1:] -= 0.97 * tr[:, :-1]; tr[:, 0] *= 0.03
    tr *= np.power(0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / (n - 1)), 0.85)
    sp = np.abs(np.fft.rfft(tr, 512)) ** 2
    mel = lambda f: 1127 * np.log(1 + f / 700); lo, hi = mel(20), mel(sr / 2); pts = np.linspace(lo, hi, 82)
    fr = mel(np.arange(257) * sr / 512); fb = np.zeros((80, 257))
    for i in range(80):
        l, c, r = pts[i:i + 3]; fb[i] = np.clip(np.minimum((fr - l) / (c - l), (r - fr) / (r - c)), 0, None)
    f = np.log(np.maximum(sp @ fb.T, 1.19e-7)); return (f - f.mean(0)).astype(np.float32)


def empreinte(x):
    """x : int16 mono 16 kHz -> vecteur normé de 256 (ou None si trop court)."""
    global _sess
    import onnxruntime as ort
    if _sess is None: _sess = ort.InferenceSession(os.path.join(ICI, "locuteur", "modele.onnx"))
    f = _fbank(x)
    if f is None or len(f) < 100: return None
    e = _sess.run(None, {"feats": f[None]})[0][0]; return e / np.linalg.norm(e)


def lire(f):
    w = wave.open(f); x = np.frombuffer(w.readframes(w.getnframes()), np.int16); sr = w.getframerate()
    return x if sr == 16000 else x[(np.arange(int(len(x) * 16000 / sr)) * sr / 16000).astype(int)]


def utile(x):
    """Garde les trames où il y a de la voix (énergie), pour que l'empreinte ne soit pas celle du silence."""
    t = x[: len(x) // 480 * 480].reshape(-1, 480).astype(float); r = np.sqrt((t ** 2).mean(1))
    return t[r > max(4 * np.percentile(r, 10) + 15, 40)].astype(np.int16).ravel()


def score(x):
    """Similarité cosinus avec l'empreinte de Tony (−1..1), ou None si pas d'empreinte ou audio trop court."""
    if not os.path.exists(EMPREINTE): return None
    d = json.load(open(EMPREINTE)); e = empreinte(utile(x))
    return None if e is None else float(np.dot(e, np.array(d["vecteur"])))


def est_tony(x):
    s = score(x)
    if s is None: return True, None            # pas encore d'empreinte : on laisse passer (et on le dit)
    return s >= json.load(open(EMPREINTE))["seuil"], s


def enroler():
    P = sorted(glob.glob(os.path.join(ICI, "tony", "*.wav"))); E = []
    for f in P:
        e = empreinte(utile(lire(f)))
        if e is not None: E.append((os.path.basename(f), e))
    if len(E) < 3: sys.exit(f"Trop peu de prises exploitables ({len(E)}) : il en faut au moins 3 avec de la voix.")
    # validation croisée : chaque prise contre la moyenne des AUTRES prises
    soi = [float(np.dot(e, (lambda m: m / np.linalg.norm(m))(np.mean([y for n2, y in E if n2 != n], 0)))) for n, e in E]
    ecartees = [n for (n, _), s_ in zip(E, soi) if s_ < 0.5]          # prise sans la voix de Tony (silence, NB par le haut-parleur…)
    if ecartees and len(E) - len(ecartees) >= 3:
        print("Prises écartées (ne ressemblent pas aux autres) :", ", ".join(ecartees))
        E = [(n, e) for (n, e), s_ in zip(E, soi) if s_ >= 0.5]
        soi = [float(np.dot(e, (lambda m: m / np.linalg.norm(m))(np.mean([y for n2, y in E if n2 != n], 0)))) for n, e in E]
    c = np.mean([e for _, e in E], 0); c /= np.linalg.norm(c)
    # imposteurs disponibles hors ligne : les voix de synthèse Piper (limite : ce ne sont pas de vraies personnes)
    from piper import PiperVoice
    autres = []
    for nom in ("fr_FR-tom-medium", "fr_FR-siwis-medium"):
        v = PiperVoice.load(os.path.join(ICI, "voix", nom + ".onnx"))
        a = np.concatenate([ch.audio_int16_array for ch in v.synthesize("Bonjour, je ne suis pas Tony. Je parle pour tester la reconnaissance de la voix, avec des phrases assez longues pour que le modèle ait de la matière.")])
        sr = v.config.sample_rate; a = a[(np.arange(int(len(a) * 16000 / sr)) * sr / 16000).astype(int)]
        autres.append((nom, float(np.dot(empreinte(a), c))))
    seuil = round(max(min(soi) - 0.05, max(s for _, s in autres) + 0.10, 0.45), 3)
    os.makedirs(os.path.dirname(EMPREINTE), mode=0o700, exist_ok=True)
    json.dump({"vecteur": c.tolist(), "seuil": seuil, "prises": [n for n, _ in E], "soi": soi, "imposteurs": autres}, open(EMPREINTE, "w"))
    os.chmod(EMPREINTE, 0o600)
    print(f"{len(E)} prises utilisées. Similarité de chaque prise avec les autres : min {min(soi):.2f}, médiane {np.median(soi):.2f}")
    print("Voix de synthèse (imposteurs) :", ", ".join(f"{n} {s:.2f}" for n, s in autres)); print(f"Seuil retenu : {seuil}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--enroler"]: enroler()
