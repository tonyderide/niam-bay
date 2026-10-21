"""Dit le texte reçu sur l'entrée standard avec Piper (phrase par phrase, pour que le son commence vite)."""
import os, re, signal, subprocess, sys
from piper import PiperVoice

ICI = os.path.expanduser("~/.local/share/nb-voix")
v = PiperVoice.load(f"{ICI}/voix/{os.environ.get('NB_VOIX', 'fr_FR-siwis-medium')}.onnx")
lecteur = subprocess.Popen(["paplay", "--raw", f"--rate={v.config.sample_rate}", "--format=s16le", "--channels=1"], stdin=subprocess.PIPE)
signal.signal(signal.SIGTERM, lambda *a: (lecteur.kill(), sys.exit(0)))
for phrase in re.split(r"(?<=[.!?…])\s+", sys.stdin.read()):
    for ch in v.synthesize(phrase):
        lecteur.stdin.write(ch.audio_int16_bytes); lecteur.stdin.flush()
lecteur.stdin.close(); lecteur.wait()
