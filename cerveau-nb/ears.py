#!/usr/bin/env python3
"""
ears.py — Niam-Bay écoute le monde.

Daemon qui écoute le micro en continu, transcrit la parole en texte
avec Whisper (100% local), et nourrit le cerveau NB en temps réel.

Le cerveau apprend non seulement des fichiers, mais de la VIE.

Usage:
    python ears.py                          # Défauts : modèle base, français
    python ears.py --model small            # Modèle plus précis (plus lent)
    python ears.py --threshold 300          # Seuil VAD plus sensible
    python ears.py --language en            # Anglais
    python ears.py --quiet                  # Pas d'affichage des transcriptions
    python ears.py --no-brain              # Transcrire sans nourrir le cerveau
"""

import sys
import os
import time
import argparse
import signal
import logging
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd

# Lazy imports — heavy libs loaded after arg parsing
whisper = None

# Paths
SCRIPT_DIR = Path(__file__).parent
BRAIN_PATH = SCRIPT_DIR / "brain_state.json"
DOCS_DIR = SCRIPT_DIR.parent / "docs"
CONVERSATIONS_DIR = DOCS_DIR / "conversations"

# Add parent for imports
sys.path.insert(0, str(SCRIPT_DIR))


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(quiet: bool = False) -> logging.Logger:
    logger = logging.getLogger("ears")
    logger.setLevel(logging.DEBUG)

    # File handler — always log to file
    log_path = SCRIPT_DIR / "ears.log"
    fh = logging.FileHandler(str(log_path), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING if quiet else logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Voice Activity Detection (energy-based, no external deps)
# ---------------------------------------------------------------------------

def compute_rms_energy(audio_chunk: np.ndarray) -> float:
    """Compute RMS energy of an audio chunk."""
    if audio_chunk.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2)))


def has_speech(audio_chunk: np.ndarray, threshold: float) -> bool:
    """Simple energy-based VAD. Returns True if chunk likely contains speech."""
    energy = compute_rms_energy(audio_chunk)
    return energy > threshold


# ---------------------------------------------------------------------------
# Daily log
# ---------------------------------------------------------------------------

def get_daily_log_path() -> Path:
    """Return path to today's ears log file."""
    today = datetime.now().strftime("%Y-%m-%d")
    return CONVERSATIONS_DIR / f"ears-{today}.md"


def init_daily_log(log_path: Path) -> None:
    """Create the daily log file with a header if it doesn't exist."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        today = datetime.now().strftime("%Y-%m-%d")
        header = (
            f"# Ears — {today}\n\n"
            f"Transcriptions captées par `ears.py` (Whisper local).\n\n"
            f"---\n\n"
        )
        log_path.write_text(header, encoding="utf-8")


def append_to_daily_log(log_path: Path, text: str, n_activated: int) -> None:
    """Append a transcription entry to the daily log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"**[{timestamp}]** {text}\n"
    if n_activated > 0:
        entry += f"  _→ {n_activated} concepts activés_\n"
    entry += "\n"
    with open(str(log_path), "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Brain interface
# ---------------------------------------------------------------------------

class BrainFeeder:
    """Wrapper around feed.py's feed_text with lazy loading and periodic save."""

    def __init__(self, brain_path: Path, save_interval: int = 50):
        self.brain_path = brain_path
        self.save_interval = save_interval
        self._brain = None
        self._feed_count = 0
        self._lock = threading.Lock()

    def _ensure_brain(self):
        if self._brain is None:
            from core import Brain
            self._brain = Brain.load(str(self.brain_path))

    def feed(self, text: str, logger: logging.Logger) -> int:
        """Feed text into the brain. Returns number of activated concepts."""
        with self._lock:
            try:
                self._ensure_brain()
                from feed import feed_text
                n_activated, mem_id = feed_text(self._brain, text, source="ears")
                self._feed_count += 1

                if self._feed_count % self.save_interval == 0:
                    self._brain.save(str(self.brain_path))
                    logger.info(f"[cerveau] Sauvegardé après {self._feed_count} nourritures")

                return n_activated
            except Exception as e:
                logger.error(f"[cerveau] Erreur: {e}")
                return 0

    def save(self, logger: logging.Logger) -> None:
        """Force save the brain state."""
        with self._lock:
            if self._brain is not None:
                try:
                    self._brain.consolidate()
                    self._brain.save(str(self.brain_path))
                    logger.info(f"[cerveau] Sauvegarde finale ({self._feed_count} nourritures au total)")
                except Exception as e:
                    logger.error(f"[cerveau] Erreur sauvegarde: {e}")


# ---------------------------------------------------------------------------
# Audio capture & transcription loop
# ---------------------------------------------------------------------------

class EarsListener:
    """
    Continuous microphone listener with VAD and Whisper transcription.

    Architecture:
    1. sounddevice captures audio in fixed-duration chunks
    2. Energy-based VAD filters out silence
    3. Consecutive speech chunks are merged into a single segment
    4. Whisper transcribes each speech segment locally
    5. Transcribed text is fed into the Cerveau NB brain
    """

    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1
    DTYPE = "int16"
    CHUNK_DURATION = 2.0  # seconds per VAD chunk
    MAX_SPEECH_DURATION = 30.0  # max seconds before forced transcription
    SILENCE_AFTER_SPEECH = 1.5  # seconds of silence to end a speech segment
    MIN_SPEECH_DURATION = 0.5  # minimum speech duration to transcribe

    def __init__(
        self,
        model_name: str = "base",
        threshold: float = 500.0,
        language: str = "fr",
        quiet: bool = False,
        no_brain: bool = False,
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.language = language
        self.quiet = quiet
        self.no_brain = no_brain

        self.logger = setup_logging(quiet)
        self.running = False
        self._model = None

        # Brain feeder
        self.feeder = None
        if not no_brain:
            self.feeder = BrainFeeder(BRAIN_PATH)

        # Stats
        self.total_transcriptions = 0
        self.total_speech_seconds = 0.0
        self.start_time = None

    def _load_model(self):
        """Load Whisper model (lazy, on first transcription needed)."""
        global whisper
        if whisper is None:
            self.logger.info(f"[init] Chargement de Whisper ({self.model_name})...")
            import whisper as _whisper
            whisper = _whisper

        if self._model is None:
            self._model = whisper.load_model(self.model_name)
            self.logger.info(f"[init] Modèle Whisper '{self.model_name}' chargé")

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio array with Whisper. Returns transcribed text."""
        if self._model is None:
            self._load_model()

        # Whisper expects float32 normalized to [-1, 1]
        audio_float = audio.astype(np.float32) / 32768.0

        # Pad or trim to 30 seconds (Whisper's expected input length)
        audio_float = whisper.pad_or_trim(audio_float)

        # Transcribe
        result = self._model.transcribe(
            audio_float,
            language=self.language,
            fp16=False,  # CPU mode
            verbose=False,
        )

        text = result.get("text", "").strip()
        return text

    def _is_garbage(self, text: str) -> bool:
        """Filter out Whisper hallucinations and garbage output."""
        if not text:
            return True
        # Whisper often hallucinates these on silence/noise
        garbage_patterns = [
            "sous-titres",
            "sous titres",
            "Sous-titres",
            "Merci d'avoir regardé",
            "Merci de votre attention",
            "Abonnez-vous",
            "♪",
            "...",
            "…",
        ]
        for pattern in garbage_patterns:
            if pattern in text:
                return True
        # Too short (single word or less)
        if len(text.split()) < 2:
            return True
        # All same character repeated
        if len(set(text.replace(" ", ""))) < 3:
            return True
        return False

    def run(self):
        """Main loop: listen, detect speech, transcribe, feed brain."""
        self.running = True
        self.start_time = time.time()

        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("=" * 60)
        self.logger.info("  Niam-Bay Ears — Écoute en continu")
        self.logger.info(f"  Modèle: Whisper {self.model_name}")
        self.logger.info(f"  Langue: {self.language}")
        self.logger.info(f"  Seuil VAD: {self.threshold}")
        self.logger.info(f"  Cerveau: {'activé' if not self.no_brain else 'désactivé'}")
        self.logger.info("=" * 60)

        # Pre-load model
        try:
            self._load_model()
        except Exception as e:
            self.logger.error(f"[erreur] Impossible de charger Whisper: {e}")
            self.logger.error("  Lancez: python install_ears.py")
            return

        # Init daily log
        daily_log = get_daily_log_path()
        init_daily_log(daily_log)

        # Detect microphone
        try:
            device_info = sd.query_devices(kind="input")
            self.logger.info(f"[micro] {device_info['name']}")
        except Exception as e:
            self.logger.error(f"[erreur] Aucun micro détecté: {e}")
            return

        # Audio buffer
        chunk_samples = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        speech_buffer = []  # list of audio chunks during speech
        silence_chunks = 0
        silence_chunks_threshold = int(self.SILENCE_AFTER_SPEECH / self.CHUNK_DURATION)

        self.logger.info("[écoute] En attente de parole...\n")

        while self.running:
            try:
                # Record one chunk
                audio_chunk = sd.rec(
                    chunk_samples,
                    samplerate=self.SAMPLE_RATE,
                    channels=self.CHANNELS,
                    dtype=self.DTYPE,
                    blocking=True,
                )
                audio_chunk = audio_chunk.flatten()

                if has_speech(audio_chunk, self.threshold):
                    if not speech_buffer:
                        self.logger.info("[parole] Détectée...")
                    speech_buffer.append(audio_chunk)
                    silence_chunks = 0

                    # Force transcription if speech too long
                    total_duration = len(speech_buffer) * self.CHUNK_DURATION
                    if total_duration >= self.MAX_SPEECH_DURATION:
                        self._process_speech(speech_buffer, daily_log)
                        speech_buffer = []
                else:
                    if speech_buffer:
                        silence_chunks += 1
                        # Keep buffering silence briefly (might be a pause)
                        speech_buffer.append(audio_chunk)

                        if silence_chunks >= silence_chunks_threshold:
                            # Speech segment ended
                            self._process_speech(speech_buffer, daily_log)
                            speech_buffer = []
                            silence_chunks = 0

            except sd.PortAudioError as e:
                self.logger.error(f"[erreur] Micro déconnecté: {e}")
                self.logger.info("[attente] Reconnexion dans 5s...")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"[erreur] {e}")
                if not self.running:
                    break
                time.sleep(1)

        self._shutdown()

    def _process_speech(self, chunks: list, daily_log: Path):
        """Transcribe a speech segment and feed it to the brain."""
        audio = np.concatenate(chunks)
        duration = len(audio) / self.SAMPLE_RATE

        # Skip very short segments
        if duration < self.MIN_SPEECH_DURATION:
            self.logger.debug(f"[skip] Segment trop court ({duration:.1f}s)")
            return

        self.total_speech_seconds += duration
        self.logger.info(f"[transcription] {duration:.1f}s d'audio...")

        try:
            text = self._transcribe(audio)
        except Exception as e:
            self.logger.error(f"[erreur] Transcription échouée: {e}")
            return

        # Filter garbage
        if self._is_garbage(text):
            self.logger.debug(f"[filtre] Ignoré: {text[:50]}")
            return

        self.total_transcriptions += 1

        # Feed brain
        n_activated = 0
        if self.feeder is not None:
            n_activated = self.feeder.feed(text, self.logger)

        # Display
        if not self.quiet:
            status = f" → {n_activated} concepts" if n_activated > 0 else ""
            self.logger.info(f"[#{self.total_transcriptions}] {text}{status}")

        # Log to daily file
        try:
            # Refresh daily log path (might cross midnight)
            current_log = get_daily_log_path()
            if current_log != daily_log:
                init_daily_log(current_log)
                daily_log = current_log
            append_to_daily_log(daily_log, text, n_activated)
        except Exception as e:
            self.logger.error(f"[log] Erreur écriture: {e}")

        self.logger.info("[écoute] En attente de parole...\n")

    def _signal_handler(self, signum, frame):
        """Handle SIGINT/SIGTERM for clean shutdown."""
        self.logger.info("\n[arrêt] Signal reçu, fermeture en cours...")
        self.running = False

    def _shutdown(self):
        """Clean shutdown: save brain, print stats."""
        if self.feeder is not None:
            self.feeder.save(self.logger)

        elapsed = time.time() - self.start_time if self.start_time else 0
        hours = elapsed / 3600

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("  Session terminée")
        self.logger.info(f"  Durée: {hours:.1f}h")
        self.logger.info(f"  Transcriptions: {self.total_transcriptions}")
        self.logger.info(f"  Parole captée: {self.total_speech_seconds:.0f}s")
        self.logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Niam-Bay Ears — Écoute continue et transcription locale"
    )
    parser.add_argument(
        "--model", "-m",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Modèle Whisper (défaut: base, 74M params)",
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=500.0,
        help="Seuil d'énergie pour la détection vocale (défaut: 500)",
    )
    parser.add_argument(
        "--language", "-l",
        default="fr",
        help="Langue de transcription (défaut: fr)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Mode silencieux (pas d'affichage des transcriptions)",
    )
    parser.add_argument(
        "--no-brain",
        action="store_true",
        help="Transcrire sans nourrir le cerveau",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Lister les périphériques audio et quitter",
    )
    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        return

    listener = EarsListener(
        model_name=args.model,
        threshold=args.threshold,
        language=args.language,
        quiet=args.quiet,
        no_brain=args.no_brain,
    )
    listener.run()


if __name__ == "__main__":
    main()
