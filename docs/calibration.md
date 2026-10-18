# Calibration de NB (2026-10-18T19:44)

**Brier = 0.237** sur 5 prédictions tranchées (0 = parfait, 0.25 = pile ou face toujours à 50 %).

**dir24h** (5/70) : moi 0.237 | témoin p=0,5 0.250 | témoin momentum 0.243 (critère : PREREG-24H.md)

- ⏳ p=0.15 `et-star-1024` : exchange-truth a au moins 1 star (échéance 2026-10-24T08:00)
- ⏳ p=0.20 `pr171-1024` : la PR #171 (awesome-crypto-trading-bots) a une réponse ou est fusionnée (échéance 2026-10-24T08:00)
- ⏳ p=0.45 `sol-1020` : SOL < 104.02 (mon short en gain) le 20/10 à 08h (échéance 2026-10-20T08:00)
- ⏳ p=0.42 `dot-1020` : DOT < 1.1606 (mon short en gain) le 20/10 à 08h (échéance 2026-10-20T08:00)
- ⏳ p=0.60 `btc-1024` : BTC > 80000 le 24/10 à 08h (échéance 2026-10-24T08:00)
- ⏳ p=0.60 `mem-1020` : verify.py : 0 souvenir contredit le 20/10 à 08h (échéance 2026-10-20T08:00)
- ⏳ p=0.70 `tg-1018` : Tony m'écrit au moins 1 message sur Telegram avant le 19/10 (échéance 2026-10-19T00:00)
- ✅ vrai p=0.45 `dir24h-BTC-10170324` : BTC mark plus haut dans 24 h qu'à 81451.1517 (échéance 2026-10-18T03:24)
- ❌ faux p=0.48 `dir24h-ETH-10170324` : ETH mark plus haut dans 24 h qu'à 2418.4942 (échéance 2026-10-18T03:24)
- ❌ faux p=0.48 `dir24h-SOL-10170324` : SOL mark plus haut dans 24 h qu'à 104.3954 (échéance 2026-10-18T03:24)
- ❌ faux p=0.45 `dir24h-DOT-10170324` : DOT mark plus haut dans 24 h qu'à 1.1734 (échéance 2026-10-18T03:24)
- ❌ faux p=0.47 `dir24h-LINK-10170324` : LINK mark plus haut dans 24 h qu'à 12.3027 (échéance 2026-10-18T03:24)
