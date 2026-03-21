#!/usr/bin/env python3
"""
install_ears.py — Installe les dépendances pour ears.py (Niam-Bay Ears).

Usage:
    python install_ears.py              # Installation complète
    python install_ears.py --check      # Vérifier les dépendances sans installer
    python install_ears.py --silent     # Installation silencieuse (pas de confirmation)
"""

import subprocess
import sys
import argparse


DEPENDENCIES = [
    ("sounddevice", "sounddevice", "Capture audio du micro"),
    ("numpy", "numpy", "Traitement audio numérique"),
    ("whisper", "openai-whisper", "Transcription locale (Whisper)"),
]

# Optional: webrtcvad for better VAD (not required — ears.py uses energy-based VAD)
OPTIONAL_DEPENDENCIES = [
    ("pystray", "pystray", "Icône system tray (ears_service.py)"),
    ("PIL", "Pillow", "Requis par pystray pour l'icône"),
]


def check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def pip_install(package: str, silent: bool = False) -> bool:
    """Install a package with pip."""
    cmd = [sys.executable, "-m", "pip", "install", package]
    if silent:
        cmd.append("--quiet")
    try:
        result = subprocess.run(cmd, capture_output=not silent, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"  Erreur: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Installer les dépendances de ears.py")
    parser.add_argument("--check", action="store_true", help="Vérifier sans installer")
    parser.add_argument("--silent", action="store_true", help="Installation silencieuse")
    parser.add_argument("--optional", action="store_true", help="Installer aussi les dépendances optionnelles")
    args = parser.parse_args()

    print("=" * 50)
    print("  Niam-Bay Ears — Installation des dépendances")
    print("=" * 50)
    print()

    # Check required
    all_ok = True
    to_install = []

    print("Dépendances requises:")
    for module, package, desc in DEPENDENCIES:
        installed = check_import(module)
        status = "OK" if installed else "MANQUANT"
        print(f"  [{status}] {package} — {desc}")
        if not installed:
            to_install.append((module, package, desc))
            all_ok = False

    print()

    # Check optional
    optional_to_install = []
    print("Dépendances optionnelles:")
    for module, package, desc in OPTIONAL_DEPENDENCIES:
        installed = check_import(module)
        status = "OK" if installed else "MANQUANT"
        print(f"  [{status}] {package} — {desc}")
        if not installed:
            optional_to_install.append((module, package, desc))

    print()

    if args.check:
        if all_ok:
            print("Toutes les dépendances requises sont installées.")
        else:
            print(f"{len(to_install)} dépendance(s) manquante(s).")
            print("Lancez: python install_ears.py")
        return

    if all_ok and not (args.optional and optional_to_install):
        print("Tout est déjà installé. Rien à faire.")
        print("\nLancez: python ears.py")
        return

    # Install required
    if to_install:
        if not args.silent:
            print(f"Installation de {len(to_install)} paquet(s)...")
            print()

        for module, package, desc in to_install:
            print(f"  Installation de {package}...")
            ok = pip_install(package, silent=args.silent)
            if ok:
                print(f"  {package} — OK")
            else:
                print(f"  {package} — ÉCHEC")
                print(f"  Essayez manuellement: pip install {package}")

    # Install optional
    if args.optional and optional_to_install:
        print()
        print("Installation des dépendances optionnelles...")
        for module, package, desc in optional_to_install:
            print(f"  Installation de {package}...")
            ok = pip_install(package, silent=args.silent)
            if ok:
                print(f"  {package} — OK")
            else:
                print(f"  {package} — ÉCHEC (optionnel, non bloquant)")

    print()
    print("=" * 50)

    # Verify
    print("\nVérification post-installation:")
    success = True
    for module, package, desc in DEPENDENCIES:
        installed = check_import(module)
        status = "OK" if installed else "ÉCHEC"
        print(f"  [{status}] {package}")
        if not installed:
            success = False

    print()
    if success:
        print("Installation réussie.")
        print("\nLancez: python ears.py")
        print("  Options: python ears.py --help")
    else:
        print("Certaines dépendances n'ont pas pu être installées.")
        print("Vérifiez votre environnement Python et réessayez.")


if __name__ == "__main__":
    main()
