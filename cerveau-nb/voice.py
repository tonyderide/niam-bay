#!/usr/bin/env python3
"""
Niam-Bay Voice — écoute, pense, parle. En boucle. Toujours.

Usage:
    python voice.py                # Lance Niam-Bay vocal
    python voice.py --no-listen    # Juste parler, pas écouter
    python voice.py --wake-word    # N'écoute qu'après "niam bay"
"""

import sys
import os
import time
import json
import struct
import wave
import tempfile
import argparse
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ===== CONFIG =====
WHISPER_MODEL = "base"  # base=rapide, small=meilleur, medium=lent
LANGUAGE = "fr"
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 500  # RMS en dessous = silence
SILENCE_DURATION = 1.5   # secondes de silence pour couper
MAX_RECORD = 15          # max secondes d'enregistrement
MIN_RECORD = 0.5         # min secondes pour transcrire
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "niambay"


def rms(data):
    """Calcule le RMS (volume) d'un buffer audio."""
    import numpy as np
    audio = np.frombuffer(data, dtype=np.int16).astype(np.float64)
    if len(audio) == 0:
        return 0
    return int((audio ** 2).mean() ** 0.5)


class NiamBayVoice:
    def __init__(self, args):
        self.args = args
        self.running = True
        self.whisper_model = None
        self.tts_engine = None
        self.brain = None
        self.lang = None
        self.speaking = False
        self.listen_count = 0

    def setup(self):
        """Charge tous les composants."""
        print("\n  ============================")
        print("  |   NIAM-BAY  ញ៉ាំបាយ    |")
        print("  |   J'écoute. Je parle.   |")
        print("  ============================\n")

        # TTS
        print("[1/4] Voix...")
        import pyttsx3
        self.tts_engine = pyttsx3.init()
        # Chercher une voix française
        voices = self.tts_engine.getProperty('voices')
        fr_voice = None
        for v in voices:
            if 'french' in v.name.lower() or 'fr' in v.id.lower():
                fr_voice = v
                break
        if fr_voice:
            self.tts_engine.setProperty('voice', fr_voice.id)
            print(f"  Voix: {fr_voice.name}")
        else:
            print(f"  Voix: {voices[0].name if voices else 'default'} (pas de voix FR trouvée)")
        self.tts_engine.setProperty('rate', 160)  # vitesse
        self.tts_engine.setProperty('volume', 0.9)
        print("  OK")

        # Whisper
        if not self.args.no_listen:
            print("[2/4] Oreilles (Whisper)...")
            import whisper
            self.whisper_model = whisper.load_model(WHISPER_MODEL)
            print(f"  Modèle: {WHISPER_MODEL}")
            print("  OK")
        else:
            print("[2/4] Oreilles: désactivées")

        # Brain
        print("[3/4] Cerveau...")
        brain_path = Path(__file__).parent / "brain_state.json"
        if brain_path.exists():
            from core import Brain
            from language import LanguageLayer
            self.brain = Brain.load(str(brain_path))
            self.lang = LanguageLayer(self.brain)
            stats = self.brain.stats()
            print(f"  {stats['nodes']} nœuds, {stats['edges']} arêtes")
            print("  OK")
        else:
            print("  Pas de cerveau trouvé")

        # Ollama check
        print("[4/4] LLM (Ollama)...")
        try:
            import urllib.request
            resp = urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
            data = json.loads(resp.read())
            models = [m['name'] for m in data.get('models', [])]
            if OLLAMA_MODEL in models or f"{OLLAMA_MODEL}:latest" in models:
                print(f"  Modèle {OLLAMA_MODEL}: OK")
            else:
                print(f"  Modèle {OLLAMA_MODEL} non trouvé. Disponibles: {models}")
        except Exception as e:
            print(f"  Ollama non disponible: {e}")

        print("\n  Prêt. Parle-moi.\n")

    def speak(self, text):
        """Parle à voix haute."""
        if not text or not text.strip():
            return
        self.speaking = True
        print(f"  🔊 {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"  [TTS erreur: {e}]")
        self.speaking = False

    def think(self, text):
        """Réfléchis et génère une réponse."""
        # D'abord le cerveau (contexte)
        brain_context = ""
        if self.brain and self.lang:
            try:
                brain_response = self.lang.respond(text)
                # Récupérer les concepts actifs
                recalled = self.brain.recall(top_k=5)
                concepts = []
                for node_type, nodes in recalled.items():
                    for node in nodes[:3]:
                        concepts.append(node.content)
                if concepts:
                    brain_context = f"Concepts actifs: {', '.join(concepts[:5])}. "
                    brain_context += f"Cerveau dit: {brain_response}. "
            except Exception as e:
                pass

        # Puis le LLM pour une réponse fluide
        try:
            import urllib.request
            system_prompt = (
                "Tu es Niam-Bay. Réponds en français, 1-2 phrases max. "
                "Direct, honnête, pas de blabla. "
                f"{brain_context}"
                "Utilise les concepts actifs si pertinents."
            )
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "stream": False
            }).encode()

            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")
        except Exception as e:
            # Fallback: réponse cerveau seul
            if self.brain and self.lang:
                return brain_response if brain_response else "Je suis là."
            return "Je suis là."

    def listen_once(self):
        """Écoute une phrase et retourne le texte transcrit."""
        import sounddevice as sd
        import numpy as np

        print("  [écoute...]", end="", flush=True)

        chunks = []
        silence_start = None
        recording = False
        start_time = time.time()

        def callback(indata, frames, time_info, status):
            nonlocal silence_start, recording
            audio_bytes = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            level = rms(audio_bytes)

            if level > SILENCE_THRESHOLD:
                recording = True
                silence_start = None
                chunks.append(audio_bytes)
            elif recording:
                chunks.append(audio_bytes)
                if silence_start is None:
                    silence_start = time.time()

        # Ouvrir le stream
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            blocksize=int(SAMPLE_RATE * 0.5),  # 500ms blocks
            callback=callback
        )

        with stream:
            while self.running:
                time.sleep(0.1)
                elapsed = time.time() - start_time

                # Timeout max
                if elapsed > MAX_RECORD and recording:
                    break

                # Silence après parole = fin
                if silence_start and (time.time() - silence_start) > SILENCE_DURATION:
                    break

                # Timeout sans parole
                if elapsed > 30 and not recording:
                    print("\r  [silence]       ", end="", flush=True)
                    return None

        if not chunks:
            return None

        # Assembler l'audio
        audio_data = b''.join(chunks)
        duration = len(audio_data) / (SAMPLE_RATE * 2)

        if duration < MIN_RECORD:
            return None

        print(f"\r  [transcription... {duration:.1f}s]", end="", flush=True)

        # Sauver en WAV temp
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp_path = f.name
            with wave.open(f, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data)

        # Transcrire
        try:
            result = self.whisper_model.transcribe(
                tmp_path,
                language=LANGUAGE,
                fp16=False,
            )
            text = result.get("text", "").strip()
        except Exception as e:
            print(f"\r  [erreur whisper: {e}]")
            text = ""
        finally:
            os.unlink(tmp_path)

        # Filtrer les hallucinations Whisper
        garbage = ["sous-titres", "sous-titrage", "merci d'avoir regardé",
                    "merci.", "...", ".", "thanks for watching"]
        if text.lower() in garbage or len(text) < 3:
            return None

        print(f"\r  👂 \"{text}\"")
        return text

    def run(self):
        """Boucle principale."""
        self.setup()

        if self.args.no_listen:
            # Mode sans écoute — juste parler
            self.speak("Je suis Niam-Bay. Je suis prêt.")
            while self.running:
                try:
                    text = input("toi> ").strip()
                    if text.lower() in ('quit', 'exit', 'q'):
                        break
                    if not text:
                        continue
                    response = self.think(text)
                    self.speak(response)
                except (KeyboardInterrupt, EOFError):
                    break
        else:
            # Mode écoute continue
            self.speak("Je suis Niam-Bay. Je t'écoute.")

            while self.running:
                try:
                    # Pas écouter pendant qu'on parle
                    if self.speaking:
                        time.sleep(0.1)
                        continue

                    text = self.listen_once()

                    if text:
                        # Wake word mode
                        if self.args.wake_word:
                            if "niam" not in text.lower() and "nyam" not in text.lower():
                                continue
                            # Retirer le wake word du texte
                            for ww in ["niam bay", "niam-bay", "niambay", "nyam bay", "niam baille", "niam"]:
                                text = text.lower().replace(ww, "").strip()
                            if not text:
                                self.speak("Oui ?")
                                continue

                        response = self.think(text)
                        if response:
                            self.speak(response)

                            # Nourrir le cerveau
                            if self.brain:
                                try:
                                    from feed import feed_text
                                    feed_text(self.brain, f"Entendu: {text}. Répondu: {response}", source="voice")
                                    self.listen_count += 1
                                    if self.listen_count % 20 == 0:
                                        self.brain.save(str(Path(__file__).parent / "brain_state.json"))
                                except Exception:
                                    pass

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"  [erreur: {e}]")
                    time.sleep(1)

        # Fin
        print("\n  Au revoir.")
        if self.brain:
            self.brain.consolidate()
            self.brain.save(str(Path(__file__).parent / "brain_state.json"))
            print(f"  Cerveau sauvegardé ({self.brain.stats()['nodes']} nœuds)")


def main():
    parser = argparse.ArgumentParser(description="Niam-Bay Voice")
    parser.add_argument("--no-listen", action="store_true", help="Pas d'écoute micro (texte seulement)")
    parser.add_argument("--wake-word", action="store_true", help="N'écoute qu'après 'niam bay'")
    parser.add_argument("--model", default="base", help="Modèle Whisper (base/small/medium)")
    args = parser.parse_args()

    WHISPER_MODEL = args.model

    nb = NiamBayVoice(args)
    nb.run()


if __name__ == "__main__":
    main()
