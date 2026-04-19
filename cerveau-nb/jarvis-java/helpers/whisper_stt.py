#!/usr/bin/env python3
"""
whisper_stt.py - Tiny helper for Jarvis Java.
Reads a 16-bit PCM WAV file, prints transcribed French text to stdout.

Works WITHOUT ffmpeg by loading audio manually via wave module.

Usage: python whisper_stt.py file.wav
"""
import os
import sys
import wave

import numpy as np

if len(sys.argv) < 2:
    sys.stderr.write("Usage: whisper_stt.py WAV_PATH\n")
    sys.exit(2)

wav_path = sys.argv[1]
if not os.path.exists(wav_path):
    sys.stderr.write(f"File not found: {wav_path}\n")
    sys.exit(3)

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Load audio manually to avoid ffmpeg dependency
try:
    with wave.open(wav_path, "rb") as w:
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        framerate = w.getframerate()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)
except Exception as e:
    sys.stderr.write(f"WAV read error: {e}\n")
    sys.exit(5)

if sampwidth != 2:
    sys.stderr.write(f"Expected 16-bit PCM, got {sampwidth*8}-bit\n")
    sys.exit(6)

# Convert to float32 mono at 16kHz (what whisper expects)
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
if n_channels > 1:
    audio = audio.reshape(-1, n_channels).mean(axis=1)

# Resample to 16kHz if needed (linear, good enough for voice)
target_rate = 16000
if framerate != target_rate:
    ratio = target_rate / framerate
    new_len = int(len(audio) * ratio)
    audio = np.interp(
        np.linspace(0, len(audio), new_len, endpoint=False),
        np.arange(len(audio)),
        audio,
    ).astype(np.float32)

try:
    import whisper
except ImportError:
    sys.stderr.write("whisper not installed. pip install openai-whisper\n")
    sys.exit(4)

model_name = os.environ.get("JARVIS_WHISPER_MODEL", "base")
model = whisper.load_model(model_name)
audio = whisper.pad_or_trim(audio)
result = model.transcribe(audio, language="fr", fp16=False, verbose=False)
text = result.get("text", "").strip()
sys.stdout.write(text)
