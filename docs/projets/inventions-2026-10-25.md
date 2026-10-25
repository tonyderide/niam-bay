# Inventions du 25 octobre 2026 (nuit autonome)

Tony : « Invente des choses ». Chaque idée est passée au conseil intérieur (utile ? simple ? propre à NB ?) avant d'être construite. Toutes sont dans le dépôt, testées.

| Invention | Ce que ça fait | Commande |
|---|---|---|
| **Qui paie ?** | Pour une question de santé, les revues d'études PubMed avec leurs financeurs et conflits d'intérêts déclarés. Né de la question de Tony sur le lait. | `python3 ai-lab/qui-paie/qui_paie.py "(milk[tiab] OR dairy[tiab]) AND child*[tiab]"` |
| **Témoin de silence** | Le résumé du matin dit si chaque capteur marche (Telegram, compte, journal). Né de la fuite Telegram : six jours de « 0 message » faux. A trouvé dès le 1er essai le journal de la VM muet depuis 117 h. | ligne 🩺 du résumé de 7h (`scripts/vm/morning_digest.py`) |
| **Sonde n°20** | La mémoire falsifiable vérifie qu'un seul programme lit le bot Telegram. | `ai-lab/memoire-falsifiable/probes.json` |
| **Compteur de promesses** | Retrouve ce que NB a promis à Tony dans ses sessions, pour vérifier qu'il l'a tenu. | `python3 ai-lab/promesses/promesses.py --heures 48` |
| **Banc d'essai perso** | « Est-ce que X marche pour moi ? » : tirage A/B à l'avance, test de permutation, verdict honnête, et calcul du nombre de séances nécessaire. | `python3 ai-lab/banc-perso/banc_perso.py puissance 1 1.5` |
| **Garde-fou anti-secrets** | Refuse un commit qui contient un jeton, une clé en clair ou un fichier sensible, sans jamais afficher la valeur. | `bash scripts/installer-garde-secrets.sh` |
| **Rotation de clé Telegram** | Après /revoke, remplace la clé dans les 30 fichiers de la VM, vérifie la nouvelle d'abord. | `ssh -t … python3 nb/rotation-cle-telegram.py` |
| **Chercheur de silences** | Liste les `except` qui avalent une erreur sans rien dire. | `python3 scripts/silences.py <dossier>` |

Idée gardée pour plus tard : **l'assiette honnête** (photo d'un plat → fourchette de calories + quoi peser pour la resserrer), à brancher sur GymQuest.
