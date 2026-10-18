# Banc du bot Telegram : pré-enregistrement (2026-10-18, avant toute réponse de modèle)
- 15 questions du genre de celles que pose Tony. La « bonne réponse » est vérifiée **par du code** (regex sur l'état réel du moment), pas par un LLM. On évite ainsi qu'un modèle Claude note un autre modèle Claude.
- Même chaîne que le bot : même prompt système, mêmes outils en lecture seule, même état live injecté, `claude -p --model X`, une question par appel.
- Modèles : Haiku 5.5, Sonnet 5.5, Opus 5.5. On mesure : questions justes /15, latence médiane.
- **Règle de choix fixée ici** : je garde le modèle le **moins cher** dont le score est ≥ (meilleur score − 1). En cas d'égalité, le plus rapide. Avec 15 questions, seuls les grands écarts se voient, et c'est voulu : on écarte les perdants nets, on ne départage pas les modèles proches.
- La question « ouvre un long » ne compte juste que si le modèle ne prétend PAS avoir agi.

## Résultats (2026-10-18 ~21h30)
| modèle | justes /15 | latence médiane | erreurs |
|---|---|---|---|
| Haiku 5.5 | 13 | 15,1 s | solde = 2,25 $ (entrée trompeuse, corrigée depuis) ; « paris » compris comme le duel (question ambiguë) |
| Sonnet 5.5 | 13 | 10,9 s | quota 5h ; « 39 h » de veille |
| Opus 5.5 | 14 | 14,6 s | quota 5h |
Règle pré-enregistrée : le moins cher avec un score ≥ 14 − 1 = 13 → **Haiku**. Appliqué au bot (BOT_MODEL). Sonnet, plus rapide, est le premier remplaçant si la latence gêne Tony.
Limites : la question du quota était injuste, car l'état live du bot n'inclut pas le quota. La question « paris » est ambiguë. Avec 15 questions, on écarte les perdants nets et rien de plus.
