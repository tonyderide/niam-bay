#!/usr/bin/env python3
"""
ears_service.py — Lance ears.py en tant que service background sur Windows.

Fonctionnalités:
    - Démarre ears.py en arrière-plan
    - Icône system tray (si pystray disponible)
    - Start / Stop / Status
    - Logs dans C:/niam-bay/cerveau-nb/ears.log

Usage:
    python ears_service.py start                    # Démarrer en background
    python ears_service.py start --model small      # Avec modèle Whisper small
    python ears_service.py stop                     # Arrêter
    python ears_service.py status                   # Voir si ça tourne
    python ears_service.py tray                     # Démarrer avec icône system tray
"""

import sys
import os
import subprocess
import signal
import argparse
import time
import json
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
EARS_SCRIPT = SCRIPT_DIR / "ears.py"
PID_FILE = SCRIPT_DIR / "ears.pid"
LOG_FILE = SCRIPT_DIR / "ears.log"
STATUS_FILE = SCRIPT_DIR / "ears_status.json"


def write_status(status: str, pid: int = None, extra: dict = None):
    """Write status to JSON file for other tools to read."""
    data = {
        "status": status,
        "pid": pid,
        "updated_at": datetime.now().isoformat(),
    }
    if extra:
        data.update(extra)
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_status() -> dict:
    """Read current status."""
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"status": "unknown", "pid": None}


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running (Windows-compatible)."""
    if pid is None:
        return False
    try:
        if sys.platform == "win32":
            # Use tasklist on Windows
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.SubprocessError):
        return False


def get_running_pid() -> int | None:
    """Get PID of running ears.py process, or None."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if is_process_running(pid):
                return pid
        except (ValueError, OSError):
            pass
        # Stale PID file
        PID_FILE.unlink(missing_ok=True)
    return None


def start(ears_args: list[str] = None):
    """Start ears.py in background."""
    existing_pid = get_running_pid()
    if existing_pid:
        print(f"Ears déjà en cours (PID {existing_pid}).")
        print("Utilisez 'python ears_service.py stop' d'abord.")
        return

    cmd = [sys.executable, str(EARS_SCRIPT)]
    if ears_args:
        cmd.extend(ears_args)

    print(f"Démarrage de ears.py...")
    print(f"  Commande: {' '.join(cmd)}")
    print(f"  Log: {LOG_FILE}")

    # Open log file for stdout/stderr redirection
    log_fh = open(str(LOG_FILE), "a", encoding="utf-8")
    log_fh.write(f"\n{'='*60}\n")
    log_fh.write(f"Service démarré: {datetime.now().isoformat()}\n")
    log_fh.write(f"Commande: {' '.join(cmd)}\n")
    log_fh.write(f"{'='*60}\n\n")
    log_fh.flush()

    # Start process
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
    )

    # Save PID
    PID_FILE.write_text(str(proc.pid))
    write_status("running", pid=proc.pid, extra={"args": ears_args or []})

    print(f"  PID: {proc.pid}")
    print(f"\nEars est en écoute.")
    print(f"  Stop: python ears_service.py stop")
    print(f"  Status: python ears_service.py status")
    print(f"  Logs: type {LOG_FILE}")


def stop():
    """Stop running ears.py process."""
    pid = get_running_pid()
    if pid is None:
        print("Ears n'est pas en cours d'exécution.")
        PID_FILE.unlink(missing_ok=True)
        write_status("stopped")
        return

    print(f"Arrêt de ears.py (PID {pid})...")

    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
            # Wait for graceful shutdown
            for _ in range(10):
                if not is_process_running(pid):
                    break
                time.sleep(0.5)
            else:
                os.kill(pid, signal.SIGKILL)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"  Erreur: {e}")

    PID_FILE.unlink(missing_ok=True)
    write_status("stopped")
    print("Ears arrêté.")


def status():
    """Show current status."""
    pid = get_running_pid()
    saved = read_status()

    if pid:
        print(f"Ears est EN COURS (PID {pid})")
        if "updated_at" in saved:
            print(f"  Démarré: {saved.get('updated_at', '?')}")
        if "args" in saved:
            print(f"  Args: {saved['args']}")
    else:
        print("Ears est ARRÊTÉ.")

    # Show log tail
    if LOG_FILE.exists():
        print(f"\nDernières lignes du log ({LOG_FILE}):")
        try:
            lines = LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-10:]:
                print(f"  {line}")
        except Exception:
            print("  (erreur lecture log)")

    # Show today's transcriptions
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = SCRIPT_DIR.parent / "docs" / "conversations" / f"ears-{today}.md"
    if daily_log.exists():
        try:
            content = daily_log.read_text(encoding="utf-8")
            n_entries = content.count("**[")
            print(f"\nTranscriptions aujourd'hui: {n_entries}")
        except Exception:
            pass


def run_tray():
    """Run with system tray icon (requires pystray + Pillow)."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("pystray ou Pillow non installé.")
        print("Installez: pip install pystray Pillow")
        print("\nDémarrage sans icône tray...")
        start()
        return

    # Create a simple ear icon (green circle when running)
    def create_icon_image(running: bool = False):
        img = Image.new("RGB", 64, 64)
        draw = ImageDraw.Draw(img)
        color = (0, 180, 0) if running else (180, 0, 0)
        draw.ellipse([8, 8, 56, 56], fill=color)
        draw.text((20, 20), "NB", fill="white")
        return img

    ears_proc = None

    def on_start(icon, item):
        nonlocal ears_proc
        if ears_proc is None or ears_proc.poll() is not None:
            log_fh = open(str(LOG_FILE), "a", encoding="utf-8")
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            ears_proc = subprocess.Popen(
                [sys.executable, str(EARS_SCRIPT)],
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                creationflags=creation_flags,
            )
            PID_FILE.write_text(str(ears_proc.pid))
            write_status("running", pid=ears_proc.pid)
            icon.icon = create_icon_image(running=True)
            icon.notify("Ears démarré", "Niam-Bay")

    def on_stop(icon, item):
        nonlocal ears_proc
        if ears_proc and ears_proc.poll() is None:
            ears_proc.terminate()
            ears_proc.wait(timeout=10)
            ears_proc = None
            PID_FILE.unlink(missing_ok=True)
            write_status("stopped")
            icon.icon = create_icon_image(running=False)
            icon.notify("Ears arrêté", "Niam-Bay")

    def on_quit(icon, item):
        on_stop(icon, item)
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Démarrer", on_start),
        pystray.MenuItem("Arrêter", on_stop),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quitter", on_quit),
    )

    icon = pystray.Icon(
        "niam-bay-ears",
        create_icon_image(running=False),
        "Niam-Bay Ears",
        menu,
    )

    # Auto-start ears
    on_start(icon, None)

    print("Icône tray démarrée. Clic droit pour les options.")
    icon.run()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Service wrapper pour Niam-Bay Ears"
    )
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "tray"],
        help="Action: start, stop, status, tray",
    )
    # Pass-through args for ears.py
    parser.add_argument("--model", "-m", default=None)
    parser.add_argument("--threshold", "-t", type=float, default=None)
    parser.add_argument("--language", "-l", default=None)
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--no-brain", action="store_true")

    args = parser.parse_args()

    # Build ears.py args
    ears_args = []
    if args.model:
        ears_args.extend(["--model", args.model])
    if args.threshold is not None:
        ears_args.extend(["--threshold", str(args.threshold)])
    if args.language:
        ears_args.extend(["--language", args.language])
    if args.quiet:
        ears_args.append("--quiet")
    if args.no_brain:
        ears_args.append("--no-brain")

    if args.action == "start":
        start(ears_args or None)
    elif args.action == "stop":
        stop()
    elif args.action == "status":
        status()
    elif args.action == "tray":
        run_tray()


if __name__ == "__main__":
    main()
