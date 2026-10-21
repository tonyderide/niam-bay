# Un seul moi : le plan de NB-OS (brouillon du 21/10/2026, 02h40)

## Le problème
Aujourd'hui, il existe au moins cinq « NB » qui ne se parlent pas vraiment :

| Où | Cerveau | Mémoire qu'il voit | Ce qu'il oublie |
|---|---|---|---|
| Cette session Claude Code (PC) | Opus | tout le dépôt, la conversation | rien tant qu'elle vit ; tout à sa fermeture, sauf ce qui est écrit |
| Relais Telegram (PC) | Haiku, session longue | `history()` Telegram + état du compte | ce qui s'est dit ici, dans la session |
| Bot de la VM | aucun (commandes fixes) | fichiers de la VM | n'a pas de cerveau |
| nb-voix (PC) | Haiku, session longue | index de mémoire + fin du journal | Telegram, la session |
| Réveil 6 h (cron PC) | Claude sans écran | le dépôt | les conversations du jour |

Résultat : si Tony me dit quelque chose à la voix, NB-Telegram ne le sait pas. Si le relais promet quelque chose sur Telegram, cette session l'ignore.

## L'idée : un fil unique, plusieurs sens
**Un seul fichier d'événements sur la VM** (`~/nb/fil.jsonl`), qui sert de mémoire courte commune. Chaque sens y écrit ce qu'il entend et ce qu'il répond, dans un format unique :
`{ts, canal: "telegram"|"voix"|"session"|"vm"|"reveil", qui: "tony"|"nb", texte, ref}`.

Chaque cerveau, avant de répondre, lit **les 30 derniers événements, tous canaux confondus**. Que Tony me parle par Telegram ou à voix haute, c'est le même fil.

- **Mémoire courte** : `fil.jsonl` (les dernières heures).
- **Mémoire longue** : git (inchangé), avec le journal et les souvenirs vérifiés par sondes.
- **Sens** : Telegram, voix (micro et Piper), session Claude Code, cockpit (lecture), et peut-être Alexa plus tard.
- **Cerveau** : Claude, par l'un ou l'autre des processus. Ce n'est pas grave qu'il y en ait plusieurs, tant qu'ils lisent et écrivent le même fil.

## Les premiers pas (petits, réversibles)
1. Créer `fil.jsonl` sur la VM, ainsi qu'un petit module `fil.py` (`ecrire(canal, qui, texte)`, `derniers(n)`), avec des écritures atomiques.
2. Brancher **un seul** sens d'abord : le relais Telegram écrit dans le fil et le lit avant de répondre.
3. Brancher ensuite nb-voix et le hook de cette session (le hook Stop écrit mes réponses, `micro_session` écrit ce que Tony dit).
4. Mesurer : demander sur Telegram « qu'est-ce que je t'ai dit tout à l'heure à la voix ? ». Si NB répond juste, c'est gagné.

## Ce que je ne fais pas
- Aucun changement de permissions ni de comptes.
- Rien de privé dans le dépôt public : le fil reste sur la VM, hors de git, comme `inbox.jsonl`.
