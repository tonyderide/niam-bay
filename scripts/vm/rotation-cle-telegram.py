#!/usr/bin/env python3
"""Remplace la clé du bot Telegram partout sur la VM, après une révocation via @BotFather.
Usage (sur la VM) : python3 rotation-cle-telegram.py          → demande la nouvelle clé (saisie masquée)
                    python3 rotation-cle-telegram.py --essai  → montre seulement les fichiers concernés
L'ancienne clé est lue dans ~/martin/.tg_token. Aucune clé n'est jamais affichée.
Chaque fichier modifié garde une copie <fichier>.avant-rotation (droits 600)."""
import getpass, json, os, shutil, subprocess, sys, urllib.request

HOME = os.path.expanduser("~")
REFERENCE = os.path.join(HOME, "martin/.tg_token")
RACINES = [HOME]
EXCLUS = {".git", "node_modules", "__pycache__", ".cache", "carnet", "ticks"}


def fichiers_avec(cle):
    cle_b = cle.encode()
    for racine in RACINES:
        for dossier, sous, noms in os.walk(racine):
            sous[:] = [s for s in sous if s not in EXCLUS]
            for n in noms:
                p = os.path.join(dossier, n)
                if n.endswith((".log", ".avant-rotation")) or os.path.islink(p):
                    continue
                try:
                    if os.path.getsize(p) < 5_000_000 and cle_b in open(p, "rb").read():
                        yield p
                except OSError:
                    pass


def get_me(cle):
    try:
        return json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{cle}/getMe", timeout=20)).get("result", {}).get("username")
    except Exception as e:
        return None


def main():
    ancienne = open(REFERENCE).read().strip()
    cibles = sorted(fichiers_avec(ancienne))
    print(f"{len(cibles)} fichier(s) contiennent l'ancienne clé :")
    for c in cibles:
        print("  ", c)
    if "--essai" in sys.argv:
        return
    nouvelle = getpass.getpass("Nouvelle clé (donnée par @BotFather après /revoke) : ").strip()
    if not nouvelle or nouvelle == ancienne or ":" not in nouvelle:
        sys.exit("Clé vide, identique à l'ancienne ou mal formée : rien n'est changé.")
    nom = get_me(nouvelle)
    if not nom:
        sys.exit("Telegram refuse cette clé (getMe) : rien n'est changé.")
    print(f"Clé acceptée par Telegram pour @{nom}.")
    for c in cibles:
        sauvegarde = c + ".avant-rotation"
        shutil.copy2(c, sauvegarde); os.chmod(sauvegarde, 0o600)
        donnees = open(c, "rb").read().replace(ancienne.encode(), nouvelle.encode())
        open(c, "wb").write(donnees)
    print(f"{len(cibles)} fichier(s) mis à jour.")
    if get_me(ancienne):
        print("⚠ L'ancienne clé marche ENCORE : la révocation n'a pas été faite. Fais /revoke dans @BotFather.")
    else:
        print("L'ancienne clé est bien morte.")
    # le bot NB (relancé par cron keepalive dans la minute)
    subprocess.run(["pkill", "-f", "python3 -u nb_vm_bot.py"])
    print("Bot NB arrêté : keepalive le relance dans la minute avec la nouvelle clé.")
    for service in ("autobot-gateway",):
        r = subprocess.run(["sudo", "-n", "systemctl", "restart", service])
        print(f"service {service} : {'relancé' if r.returncode == 0 else 'NON relancé (à faire à la main)'}")
    print("Martin (martin.service) n'est PAS redémarré : il prendra la clé à son prochain redémarrage, à décider par Tony.")


if __name__ == "__main__":
    main()
