# PREREG funding couvert Kraken vs Hyperliquid (écrit 2026-10-19 avant tout calcul)
- Coins: BTC, ETH, SOL (PF_XBTUSD, PF_ETHUSD, PF_SOLUSD vs HL BTC/ETH/SOL).
- Unité Kraken: à vérifier AVANT (doc + comparaison fundingRate absolu / prix mark). Pas d'hypothèse horaire.
- Sélection: 2026-01-01 -> 2026-06-30. N dans {3,7,14,30} jours, choisi par coin = meilleur rendement net en sélection.
- Jugement: 2026-07-01 -> 2026-10-16, N figé, aucun réglage.
- Stratégie: écart horaire s = fundingHL - fundingKraken (même unité horaire, alignement à l'heure). Moyenne glissante N jours (passée uniquement).
  Si moyenne>0: short HL / long Kraken; sinon inverse. Retournement seulement si le signe de la moyenne change. Position initiale ouverte au 1er signe.
- Frais: 4 x 0,05 % du notionnel par ouverture complète et par fermeture complète (retournement = fermeture+ouverture = 8 x 0,05 %).
  Ouverture initiale: 4x0,05 %; pas de fermeture finale comptée en plus? -> on compte la fermeture finale (conservateur).
- Rendement: net / notionnel (une jambe), annualisé linéairement.
- Risque: pire écart de base (markPrice Kraken vs HL) si données accessibles; sinon rapporté comme non mesuré.
- GAGNE: rendement net annualisé > 2 % en jugement sur >= 2 coins sur 3 avec l'unité vérifiée. Sinon PERD.
