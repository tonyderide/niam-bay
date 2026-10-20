# Le lecteur d'événements
Idée du 1021 vers 00h20. Tony : « fais ce que tu veux, regarde les avancées de l'IA, teste ».

## Passages au conseil
1. **Lecteur de presse** : Haiku lit les titres du jour et prédit la direction du BTC à 24 h. Verdict : PAS MAINTENANT (5,82). Les critiques étaient justes : on a déjà mesuré que la direction du BTC à 24 h ne se prédit pas, et 110 jours ne permettent pas de distinguer 53 % de 50 %.
2. **Version corrigée** : des centaines d'événements précis sur des altcoins, classés par Haiku sans qu'il voie le prix, puis mesure du rendement 1h/4h/24h comparé à des instants pris au hasard. Verdict : OUI (7,18). Condition posée par le conseil : au moins 200 événements.

## Pré-vol (1021 00h30) : ÉCHEC, rien n'est lancé
Sources, dans le respect des robots.txt :
- **GDELT** : erreur 429, il bloque les requêtes après un premier envoi trop rapproché (3 requêtes à 6 s d'écart, alors qu'il demande 5 s minimum). Je n'insiste pas.
- **CoinDesk** : `Disallow: /`, exclu.
- **The Block** : nomme les robots d'IA, dont ClaudeBot, dans son robots.txt, exclu par prudence.
- **Decrypt** : autorise tout le monde. Ses sitemaps 37 et 38 couvrent juillet-octobre 2026, avec environ 1 300 articles. Parmi eux, **160** combinent une crypto et un mot-clé d'événement, dont **37 seulement hors BTC/ETH**.

160 < 200, et 37 événements sur des altcoins ne donnent aucune puissance statistique. **Le test n'est donc pas lancé.**

À retenter éventuellement : GDELT, plus tard et poliment (une requête toutes les 10 s), pour voir s'il donnerait au moins 200 événements sur des altcoins. Sinon, on abandonne.
