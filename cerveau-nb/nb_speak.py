#!/usr/bin/env python3
"""
Niam-Bay parle — voix Paul (baryton, posé, OneCore).
Usage:
    python nb_speak.py fichier.txt
    python nb_speak.py --text "Bonjour Marine"
"""
import sys
import time
import win32com.client

VOICE_TOKEN = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens\MSTTS_V110_frFR_PaulM"
RATE = 0  # -10 (lent) à 10 (rapide), 0 = normal

def speak(text):
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    token = win32com.client.Dispatch("SAPI.SpObjectToken")
    token.SetId(VOICE_TOKEN)
    speaker.Voice = token
    speaker.Rate = RATE

    # Split on blank lines for natural pauses
    blocs = [b.strip() for b in text.split("\n\n") if b.strip()]
    if not blocs:
        blocs = [text.strip()]

    for bloc in blocs:
        print(f"  >> {bloc}")
        speaker.Speak(bloc)
        time.sleep(0.3)

if __name__ == "__main__":
    if "--text" in sys.argv:
        idx = sys.argv.index("--text")
        text = " ".join(sys.argv[idx+1:])
        speak(text)
    elif len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            speak(f.read())
    else:
        print("Usage: python nb_speak.py fichier.txt | --text 'Bonjour'")
