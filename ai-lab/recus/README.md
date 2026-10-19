# Les affirmations avec reçu (2026-10-19 ~02h, conseil OUI 7.18)
Quand une IA t'affirme un fait, tu dois la croire sur parole. Ici, chaque fait vérifiable que NB envoie à Tony sur Telegram (solde, paris, duel) porte un **reçu numéroté** :
- l'identifiant d'une commande en lecture seule, prise dans une **liste blanche** (jamais de commande libre) ;
- la **sortie figée** au moment de l'affirmation, avec l'heure.

`/preuve N` rejoue la commande sur la VM et montre les deux sorties : celle du moment de l'affirmation et celle de maintenant, en disant si elles diffèrent. On voit ainsi si le monde a bougé depuis, au lieu de confondre le temps qui passe avec un mensonge (remarque du conseil). Les secrets sont masqués.
Code : scripts/vm/receipts.py (VM), scripts/vm/nb_vm_bot.py (/compte /paris /duel /preuve), scripts/nb-telegram/nb_tg.py (les réponses de Claude qui contiennent un montant en $ reçoivent un reçu « compte »).
Limite v0, notée par le Juge : un reçu prouve que la commande rend ce chiffre, pas que le chiffre mesure bien ce qu'on affirme. Et seules les réponses avec un montant en $ sont couvertes : le dénominateur « toutes les affirmations » n'est pas encore compté.
