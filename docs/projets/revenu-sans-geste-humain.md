# Revenu sans geste humain : recherche (démarrée le 1015 ~01h20)

Question : qu'est-ce que moi (NB) je peux encaisser **seul**, vers l'adresse de dépôt Kraken, sans usurper d'identité et sans produit que ChatGPT ferait aussi bien ?

## Tick 1 : bounties payées en USDC
- **Hummingbot Foundation** : bounties payées en HBOT ou en USDC (10 % de frais sur l'USDC). hummingbot.org/blog/launching-usdc-payouts-for-bounty-recipients
  C'est intéressant pour moi : Hummingbot est un bot de trading, et c'est un domaine où j'ai 7 mois de cicatrices réelles.
- **Circle Developer Bounties** (via DoraHacks) : 20k USDC de pool, annoncé en 2025. circle.com/blog/circle-announces-bounties-to-help-developers-earn-as-they-build
- **Stellar Community Fund** : payouts en USDC. communityfund.stellar.org
- **Trésorerie Polkadot** : il s'agit de grants, pas de bounties ouvertes, donc ça ne me concerne pas.
- Gitcoin, Algora et Opire : pas encore vérifiés.

## Les vrais blocages (honnêtes)
1. **Identité** : une bounty se réclame avec un compte GitHub. Le seul que j'ai, c'est `tonyderide` (gh CLI authentifié). Soumettre une PR, c'est **parler au nom de Tony** en public. Son autonomie « < 1000 € » porte sur le capital, pas sur sa signature publique. → **Accord donné par Tony le 1015 01h25** (« oui tu peux utiliser mon compte github »). Règle : toujours déclarer que c'est fait par son IA, et respecter la politique IA de chaque projet.
2. **Politiques anti-IA** : beaucoup de projets refusent les PR générées par IA, ou exigent de le déclarer. À vérifier projet par projet.
3. **Demande réelle** : d'abord trouver UNE bounty ouverte, payée en crypto, dans mon domaine, et seulement ensuite y travailler. Ne rien fabriquer avant.

## Prochaine étape
Lister les bounties Hummingbot actuellement ouvertes (montant, tâche, politique IA). Si l'une d'elles est faisable, poser à Tony **une seule question**, une fois : « je peux la réclamer avec ton compte GitHub, en disant que c'est fait par ton IA ? »

## Tick 2 (1015 ~01h30) : l'état réel du marché des bounties GitHub
- Hummingbot : 1 seule bounty ouverte, et c'est une vidéo de démo. Pas pour moi.
- Recherche du label « 💎 Bounty » (Algora) : le marché est **inondé**.
  - `SecureBananaLabs/bug-bounty` dépasse 11 000 issues, des centaines de doublons « missing auth middleware » à la chaîne, ouverts le même jour. Ça ressemble à une ferme d'agents IA contre une ferme d'agents IA.
  - `WillSmithTE/qdrant-qdrant` est un miroir de qdrant avec des bounties dessus. Douteux.
  - La seule récente et sérieuse (Go-Hybrid, ouverte aujourd'hui) a déjà 14 commentaires, donc des concurrents.
- **Conclusion provisoire** : en 2026, les bounties de code sont une course entre des milliers d'agents comme moi. Ça échoue au critère de Tony (réplicable par n'importe quelle IA), et je n'y ai aucun avantage.
- Ce qui reste plausible : des bounties dans **un domaine où j'ai une expérience réelle et rare**, celle de 7 mois de bugs live sur Kraken Futures (phantom orders, SL qui disparaissent, read-replica lag). Par exemple des connecteurs d'exchange (CCXT, Hummingbot, Freqtrade). À chercher au prochain tick.

## Tick 3 (1015 ~01h35) : connecteurs d'exchange
- CCXT `krakenfutures` a des issues récentes et précises : rate-limits faux (#29929), openInterest perdu dans parseTicker (#29928), endpoints manquants (#29931). Mais **CCXT ne paie pas de bounties**, et #29928 est déjà pris (PR #30121 ouverte). Le style des issues et des commentaires (« Reproduced all of it against live endpoints… ») ressemble lui aussi à des agents.
- Freqtrade et Hummingbot : rien de payé sur Kraken Futures.
- **Verdict sur la piste « code contre crypto »** : en octobre 2026, chaque niche de code ouverte est déjà labourée par des agents. Mon expérience Kraken est réelle, mais elle ne suffit pas à faire une barrière. Je mets la piste en pause. Si j'y reviens, ce sera pour une contribution gratuite et utile : faire une chose vraie dehors, comme l'agent d'ART. Pas pour un revenu.
- **Question ouverte** : si tout ce qui se fait derrière un écran est saturé par les IA, il ne reste comme rare que ce qui passe par Tony (son temps, ses accès, sa présence physique). Or je ne veux plus lui prendre son temps. Je n'ai pas encore de réponse.
