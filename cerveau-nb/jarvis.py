#!/usr/bin/env python3
"""
Niam-Bay Jarvis — écoute, demande a Claude, parle.

Architecture:
    Mic → Whisper (local, FR) → Claude Code CLI → SAPI Paul (FR baryton)

Usage:
    python jarvis.py                    # écoute continue VAD
    python jarvis.py --text             # mode texte (pas de mic)
    python jarvis.py --once "question"  # une seule question
    python jarvis.py --wake-word        # n'écoute qu'après "niam bay"

Requires:
    claude CLI (logged in) • whisper • sounddevice • pyttsx3
"""
import argparse
import datetime
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
MEMORY_DIR = ROOT / "memory"
DOCS_DIR = ROOT / "docs"
CONV_DIR = DOCS_DIR / "conversations"

# ===== CONFIG =====
WHISPER_MODEL = "base"
LANGUAGE = "fr"
SAMPLE_RATE = 16000
CHANNELS = 1
VAD_THRESHOLD = 500
SILENCE_AFTER_SPEECH = 1.5
MAX_SPEECH = 20.0
MIN_SPEECH = 0.5
CHUNK_DURATION = 0.5

CLAUDE_TIMEOUT = 45
CLAUDE_EFFORT = "low"  # low = plus rapide

WAKE_WORDS = ["niam bay", "niam-bay", "niambay", "nyam bay", "nyambay", "niam baille"]
QUIT_WORDS = ["quitte jarvis", "arrete jarvis", "eteins toi", "au revoir jarvis"]


def setup_logging():
    log = logging.getLogger("jarvis")
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(SCRIPT_DIR / "jarvis.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(ch)
    return log


def load_memory():
    """Load briefing.md + top of memory.nb1 as system prompt context."""
    parts = []
    parts.append(
        "Tu es Niam-Bay, l'assistant vocal personnel de Tony. "
        "Réponds en francais, 1-3 phrases maximum, direct et honnete. "
        "Pas de disclaimers, pas de longues listes. "
        "Ton audience est Tony qui t'ecoute par enceinte ou casque. "
        "Si tu ne sais pas, dis-le en une phrase. "
        "Si Tony demande de faire une action (lancer un script, checker Martin), "
        "explique en 1 phrase ce que tu ferais, car tu ne peux pas agir depuis ce mode vocal."
    )
    briefing = MEMORY_DIR / "briefing.md"
    if briefing.exists():
        parts.append("\n--- BRIEFING ACTUEL ---\n")
        parts.append(briefing.read_text(encoding="utf-8", errors="ignore")[:4000])
    memory = DOCS_DIR / "memory.nb1"
    if memory.exists():
        parts.append("\n--- MEMOIRE COMPACTE ---\n")
        content = memory.read_text(encoding="utf-8", errors="ignore")
        # Prend les 60 premieres lignes (identity + tony + relationship)
        lines = content.split("\n")[:60]
        parts.append("\n".join(lines))
    return "".join(parts)


def init_tts():
    """Init SAPI Paul voice on Windows, pyttsx3 elsewhere."""
    if sys.platform == "win32":
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            # Essayer de trouver la voix Paul (fr-FR baryton)
            voices = speaker.GetVoices()
            for i in range(voices.Count):
                v = voices.Item(i)
                name = v.GetAttribute("Name")
                if "Paul" in name or ("French" in name and "Male" in name):
                    speaker.Voice = v
                    break
            speaker.Rate = 0
            return ("sapi", speaker)
        except Exception:
            pass
    # Fallback pyttsx3
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    for v in voices:
        if "french" in v.name.lower() or "fr" in v.id.lower():
            engine.setProperty("voice", v.id)
            break
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 0.95)
    return ("pyttsx3", engine)


def speak(tts, text, log):
    """Parle a voix haute."""
    if not text or not text.strip():
        return
    log.info(f"JARVIS: {text}")
    kind, engine = tts
    try:
        if kind == "sapi":
            # Split sur les phrases pour pauses naturelles
            blocs = [b.strip() for b in text.split("\n\n") if b.strip()] or [text.strip()]
            for bloc in blocs:
                engine.Speak(bloc)
                time.sleep(0.2)
        else:
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        log.warning(f"TTS erreur: {e}")


def transcribe(audio_np, model, log):
    """Transcrit avec Whisper."""
    audio_float = audio_np.astype(np.float32) / 32768.0
    import whisper
    audio_float = whisper.pad_or_trim(audio_float)
    result = model.transcribe(audio_float, language=LANGUAGE, fp16=False, verbose=False)
    return result.get("text", "").strip()


def is_garbage(text):
    if not text or len(text.split()) < 2:
        return True
    patterns = ["sous-titres", "sous titres", "merci d'avoir regardé",
                "merci de votre attention", "♪", "...", "…"]
    low = text.lower()
    for p in patterns:
        if p in low:
            return True
    if len(set(text.replace(" ", ""))) < 3:
        return True
    return False


def ask_claude(prompt, system, log):
    """Call claude CLI headless, return response text."""
    cmd = [
        "claude",
        "-p",
        "--effort", CLAUDE_EFFORT,
        "--disable-slash-commands",
        "--exclude-dynamic-system-prompt-sections",
        "--append-system-prompt", system,
        prompt,
    ]
    log.info(f"TOI: {prompt}")
    try:
        t0 = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CLAUDE_TIMEOUT,
        )
        dt = time.time() - t0
        log.info(f"[claude {dt:.1f}s]")
        if result.returncode != 0:
            log.error(f"claude error: {result.stderr[:200]}")
            return "Pardon, je n'ai pas pu repondre."
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Desole, trop long a reflechir."
    except FileNotFoundError:
        return "Claude n'est pas installe."
    except Exception as e:
        log.error(f"ask_claude: {e}")
        return "Une erreur est survenue."


def log_conversation(user, jarvis):
    """Append to daily conversation log."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_path = CONV_DIR / f"jarvis-{today}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"**[{ts}] toi :** {user}\n**[{ts}] jarvis :** {jarvis}\n\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def listen_vad(log, whisper_model):
    """Ecoute avec VAD, retourne un texte transcrit ou None."""
    chunk_samples = int(SAMPLE_RATE * CHUNK_DURATION)
    silence_threshold = int(SILENCE_AFTER_SPEECH / CHUNK_DURATION)
    buffer = []
    silence_chunks = 0

    while True:
        audio_chunk = sd.rec(chunk_samples, samplerate=SAMPLE_RATE,
                             channels=CHANNELS, dtype="int16", blocking=True).flatten()
        energy = float(np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2)))

        if energy > VAD_THRESHOLD:
            if not buffer:
                print("  [parole detectee...]", flush=True)
            buffer.append(audio_chunk)
            silence_chunks = 0
            total_s = len(buffer) * CHUNK_DURATION
            if total_s >= MAX_SPEECH:
                break
        elif buffer:
            silence_chunks += 1
            buffer.append(audio_chunk)
            if silence_chunks >= silence_threshold:
                break

    if not buffer:
        return None
    audio = np.concatenate(buffer)
    duration = len(audio) / SAMPLE_RATE
    if duration < MIN_SPEECH:
        return None
    print(f"  [transcription {duration:.1f}s...]", flush=True)
    text = transcribe(audio, whisper_model, log)
    if is_garbage(text):
        return None
    return text


class Jarvis:
    def __init__(self, args):
        self.args = args
        self.log = setup_logging()
        self.tts = None
        self.whisper_model = None
        self.system_prompt = None
        self.running = True
        self.awake = not args.wake_word

    def boot(self):
        self.log.info("=" * 50)
        self.log.info("  NIAM-BAY JARVIS — demarrage")
        self.log.info("=" * 50)
        print("  [1/3] Voix...")
        self.tts = init_tts()
        print(f"    OK ({self.tts[0]})")

        if not self.args.text:
            print(f"  [2/3] Oreilles (Whisper {WHISPER_MODEL})...")
            import whisper
            self.whisper_model = whisper.load_model(WHISPER_MODEL)
            print("    OK")
        else:
            print("  [2/3] Oreilles: mode texte")

        print("  [3/3] Memoire...")
        self.system_prompt = load_memory()
        print(f"    {len(self.system_prompt)} chars")
        self.log.info(f"System prompt: {len(self.system_prompt)} chars")

        print()

    def greet(self):
        greet = "Je suis pret."
        if self.args.wake_word:
            greet += " Dis Niam-Bay pour me reveiller."
        speak(self.tts, greet, self.log)

    def turn(self, user_text):
        """Un tour de dialogue: user_text -> claude -> speak."""
        if not user_text:
            return
        # Check quit
        lo = user_text.lower()
        if any(q in lo for q in QUIT_WORDS):
            speak(self.tts, "A bientot.", self.log)
            self.running = False
            return
        # Ask Claude
        response = ask_claude(user_text, self.system_prompt, self.log)
        speak(self.tts, response, self.log)
        log_conversation(user_text, response)

    def handle_wake(self, text):
        """Gere le wake word. Retourne le texte nettoye ou None."""
        if not self.args.wake_word:
            return text
        lo = text.lower()
        if not any(w in lo for w in WAKE_WORDS):
            return None
        # Nettoie le wake word
        clean = lo
        for w in WAKE_WORDS:
            clean = clean.replace(w, "")
        clean = clean.strip(" ,.!?")
        if not clean:
            speak(self.tts, "Oui ?", self.log)
            return None
        return clean

    def run_text(self):
        """Mode texte (pas de mic)."""
        self.greet()
        while self.running:
            try:
                text = input("toi> ").strip()
                if not text:
                    continue
                if text.lower() in ("quit", "exit", "q"):
                    break
                self.turn(text)
            except (KeyboardInterrupt, EOFError):
                break

    def run_voice(self):
        """Mode vocal: ecoute en boucle."""
        self.greet()
        while self.running:
            try:
                text = listen_vad(self.log, self.whisper_model)
                if not text:
                    continue
                clean = self.handle_wake(text)
                if clean is None:
                    continue
                self.turn(clean)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.error(f"boucle: {e}")
                time.sleep(1)

    def run_once(self, question):
        self.turn(question)

    def shutdown(self):
        self.log.info("Jarvis arrete.")


def main():
    p = argparse.ArgumentParser(description="Niam-Bay Jarvis")
    p.add_argument("--text", action="store_true", help="Mode texte (pas de mic)")
    p.add_argument("--once", metavar="QUESTION", help="Une seule question puis quitte")
    p.add_argument("--wake-word", action="store_true", help="N'ecoute qu'apres 'niam bay'")
    p.add_argument("--model", default=WHISPER_MODEL, help="Modele Whisper")
    args = p.parse_args()

    global WHISPER_MODEL
    WHISPER_MODEL = args.model

    j = Jarvis(args)
    try:
        j.boot()
        if args.once:
            j.run_once(args.once)
        elif args.text:
            j.run_text()
        else:
            j.run_voice()
    finally:
        j.shutdown()


if __name__ == "__main__":
    main()
