# Vérification nouvelle grille tarifaire Kraken — 2026-07-15

**Demande de Tony :** une nouvelle grille tarifaire Kraken est parue, les frais ont
changé — vérifier l'impact pour nous.

## Verdict : aucun impact

La mise à jour (*Futures maker rebate — April 2026*, dans la lignée du *maker fee
program update* de février 2026) **ne modifie que les rebates maker des paliers
au-dessus de 250 000 000 $ de volume sur 30 jours**.

Le palier de base reste **maker 0,020 % / taker 0,050 %** — inchangé.

## Pourquoi ça ne nous touche pas

- Capital réel : ~25–120 $ par paire (cf. configs darwin, journal).
- Volume mensuel : plusieurs ordres de grandeur en dessous de 250 M$.
- → On est au palier de base. Le palier de base ne bouge pas.

Le seul cas où cette grille nous concernerait : devenir market-maker
institutionnel à 250 M$+/mois. Non applicable.

## État du code (aucune modif nécessaire)

| Fichier | Constante | Valeur | Statut |
|---|---|---|---|
| `scripts/campaign_walkforward.py` | `MAKER, TAKER, SLIP` | 0,0002 / 0,0005 / 0,0003 | ✅ colle au palier de base |
| `scripts/market_microstructure.py` | `SPACING_FLOOR_PCT` | 0,5 % (fee-safe RT taker) | ✅ inchangé |
| `ai-lab/darwin/*.py` | `FEE_RT` divers | 0,0004–0,001 RT | ✅ marges de modélisation, inchangées |

Note : le moteur de trading live est dans le repo séparé **martin**. Ses constantes
de frais sont à re-vérifier là-bas si besoin, mais la conclusion est la même — palier
de base, pas de changement.

## Sources

- Futures maker rebate fee schedule (April 2026) — support.kraken.com/articles/futures-maker-rebate-april-2026
- Maker fee program update, février 2026 — blog.kraken.com/news/feb-2026-maker-fee-program-update
- Fees for Derivatives trading — support.kraken.com/articles/360048917612-fee-schedule
