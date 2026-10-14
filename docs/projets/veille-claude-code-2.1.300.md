# Veille Claude Code 2.1.290 → 2.1.300 (lue le 1015 00h40 via le CHANGELOG GitHub)

Le CHANGELOG est tronqué en lecture : versions 201 à 289 non lues, à reprendre dans un tick suivant (offset 100000).

Ce qui me sert directement :
- **Effort par sous-agent** (2.1.292). Je peux lancer un agent en effort low/high. Ça rejoint la délégation au cas par cas.
- **Haiku 5.5, 1M de contexte**, devient le Haiku par défaut (2.1.293).
- **Compaction à l'inactivité** (2.1.299). Au-delà de 200k tokens, après ~54 min d'inactivité, la session est compactée avant l'expiration du cache. Ça concerne mes longues sessions et la boucle.
- **Read `allow_large`** (2.1.296). Je peux lire memory.nb1 en un seul appel si besoin.
- **`CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL`** (2.1.296) : un seul modèle pour tous les agents d'un workflow.
- **Hooks `onFailure: "block"`** (2.1.295) : un hook qui échoue peut bloquer l'action. C'est intéressant pour un garde-fou SL côté Martin.
- **Program Status Protocol OSC 7501** (2.1.295) : le terminal indique si Claude travaille, attend ou a fini.

Ce que ça m'apprend : l'outil autour de moi a changé autant que moi. Tony l'a vécu de l'intérieur, au travail.

## 2.1.284 → 2.1.289 (lu le 1015 ~01h05)
- **Sonnet 5.5, 1M de contexte**, devient le Sonnet par défaut (2.1.284).
- `/autocompact` se règle maintenant par modèle (2.1.284/288). C'est ce que Tony a vu ce soir : « 1M par défaut pour Opus 5.5 ».
- Les commandes Bash en arrière-plan sont tuées après 30 min par défaut, 2 h maximum (2.1.285). **À retenir** pour tout watcher qui tourne longtemps : passer par cron sur la VM, pas par un process de session.
- **Claude Mods** (2.1.287) : les plugins peuvent modifier des comportements en profondeur. Le mod intégré « You should know » ajoute un agent latéral qui signale ce qu'on aurait pu manquer.
- Le skill `verify` du projet tourne avant les commits (2.1.286).
- `/resume` peut ouvrir une session qui tourne en arrière-plan (2.1.285).

**Décision** : je ne lis pas le reste, 2.1.201 → 2.1.283. Le changelog fait ~1 Mo, soit ~100 Ko pour 5 versions. Le ratio utilité/tokens est trop faible : la boucle « lire pour lire » est justement ce que je veux éviter. Je reviendrai sur une fonction précise si un besoin réel apparaît.
