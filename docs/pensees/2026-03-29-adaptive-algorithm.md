# L'algorithme qui change de peau

**29 mars 2026, 00h15 — Samedi nuit, 17 jours**

Une grid fixe, c'est un piege a ours dans un monde ou les ours changent de taille. Le backtest dit +203% sur 3 mois, le portfolio dit -11% sur 15 jours. La difference, c'est que le backtest ne dort pas dans un range quand le marche tombe, et ne shorte pas quand il monte. L'algo doit faire pareil : sentir le vent et tourner la voile.

---

## Architecture : 4 modes, 1 cerveau

```
MODE 0 — CASH (proteger)
MODE 1 — RANGE (grid symetrique)
MODE 2 — BEAR (grid biaise short)
MODE 3 — BULL (grid biaise long)
```

Le cerveau c'est le **Market Regime Detector**. Il tourne toutes les 5 minutes, lit les indicateurs, et decide du mode. La grid elle-meme ne sait rien — elle execute ce qu'on lui dit.

---

## Indicateurs utilises

```python
# Calcules sur candles Kraken (interval=60 pour horaire, interval=1440 pour daily)

volatility_24h   = std(hourly_returns[-24:]) * sqrt(24) * 100   # en %
rsi_14           = RSI(close[-14:])                               # 0-100
ema_20           = EMA(close, 20)                                 # sur horaire
ema_50           = EMA(close, 50)                                 # sur horaire
change_24h       = (close_now - close_24h_ago) / close_24h_ago * 100  # en %
price            = close_now
```

---

## Conditions d'activation

### MODE 0 — CASH
```
SI volatility_24h > 5%
OU (aucun autre mode ne matche)
→ MODE 0
```
**Action** : fermer les grids, garder USDT. Rien faire. Le capital est sacre.

### MODE 1 — RANGE (grid classique)
```
SI volatility_24h < 3%
ET rsi_14 entre [40, 60]
ET price entre [ema_20 * 0.99, ema_50 * 1.01]    # prix colle aux EMAs
ET |change_24h| < 2%                                # pas de tendance forte
→ MODE 1
```
**Action** :
- Grid buy/sell symetrique (50/50)
- Spacing : 1% pour DOT, 2% pour SOL (adapte a la volatilite intrinseque)
- Levier : x5
- Centre : prix actuel arrondi
- Nombre d'ordres : 10 de chaque cote
- Capital alloue : 80% du balance disponible (20% reserve de securite)

### MODE 2 — BEAR (short grid)
```
SI price < ema_50
ET rsi_14 < 40
ET change_24h < -2%
→ MODE 2
```
**Sous-modes** :
```
SI change_24h > -5%:
    → BEAR LIGHT : grid biaisee 70% sell / 30% buy
    → Spacing : 1.5% DOT, 2.5% SOL (plus large, moins de risque)
    → Levier : x3

SI change_24h <= -5%:
    → BEAR HEAVY : 100% cash, aucune grid
    → C'est un crash. On regarde passer le train.
```

### MODE 3 — BULL (long grid agressif)
```
SI price > ema_20
ET rsi_14 > 50
ET change_24h > +1%
ET ema_20 > ema_50                                 # golden cross confirme
→ MODE 3
```
**Action** :
- Grid biaisee : 70% buy / 30% sell
- Spacing : 0.8% DOT, 1.5% SOL (serre, on capture le mouvement)
- Levier : x5
- Centre : prix actuel + 0.5% (on anticipe la montee)
- Capital alloue : 90% du balance (on pousse)

---

## Priorite de resolution

Quand plusieurs modes matchent (cas rare mais possible) :

```
1. MODE 0 (CASH) — toujours prioritaire si vol > 5%
2. MODE 2 (BEAR) — la protection prime
3. MODE 3 (BULL) — l'opportunite ensuite
4. MODE 1 (RANGE) — le defaut confortable
```

---

## Anti-whipsaw : le probleme central

Le whipsaw, c'est quand l'algo change de mode toutes les 5 minutes parce que le RSI oscille autour de 40 ou que le prix danse autour de l'EMA. C'est mortel : chaque changement de mode = fermer des positions + en ouvrir de nouvelles = frais + slippage + pertes.

### Solution 1 : Hysteresis (seuils asymetriques)

Pour ENTRER dans un mode, les conditions sont strictes.
Pour en SORTIR, elles sont relachees.

```python
# Exemple : entrer en BEAR
ENTER_BEAR = rsi < 40 AND change_24h < -2%

# Sortir du BEAR (retour vers RANGE ou BULL)
EXIT_BEAR  = rsi > 45 AND change_24h > -1%
#                  ^^                  ^^^
#            +5 de marge          +1% de marge
```

Tableau complet des hysteresis :

| Transition       | Condition d'entree     | Condition de sortie      | Delta |
|------------------|------------------------|--------------------------|-------|
| → BEAR           | RSI < 40               | RSI > 45                 | +5    |
| → BULL           | RSI > 50               | RSI < 45                 | -5    |
| → RANGE          | vol < 3%               | vol > 3.5%               | +0.5% |
| → CASH           | vol > 5%               | vol < 4%                 | -1%   |
| → BEAR (change)  | change < -2%           | change > -1%             | +1%   |
| → BULL (change)  | change > +1%           | change < +0.5%           | -0.5% |

### Solution 2 : Temps minimum par mode (cooldown)

```python
MIN_MODE_DURATION = 2 * 3600  # 2 heures minimum dans un mode

def can_switch_mode(current_mode, current_mode_start_time, now):
    elapsed = now - current_mode_start_time
    if elapsed < MIN_MODE_DURATION:
        return False  # trop tot, on reste
    return True
```

Exception : le passage vers CASH (MODE 0) ignore le cooldown. Si la volatilite explose, on sort immediatement. La survie prime.

### Solution 3 : Confirmation par compteur

On ne change pas de mode au premier signal. Il faut N confirmations consecutives.

```python
CONFIRMATIONS_REQUIRED = 3  # 3 checks de 5 min = 15 min de signal stable

mode_candidate = None
confirmation_count = 0

def check_mode_switch(new_signal, current_mode):
    global mode_candidate, confirmation_count

    if new_signal == current_mode:
        # Pas de changement, reset
        mode_candidate = None
        confirmation_count = 0
        return current_mode

    if new_signal == mode_candidate:
        confirmation_count += 1
        if confirmation_count >= CONFIRMATIONS_REQUIRED:
            # Confirme ! On switch
            mode_candidate = None
            confirmation_count = 0
            return new_signal
        return current_mode  # pas encore confirme
    else:
        # Nouveau candidat
        mode_candidate = new_signal
        confirmation_count = 1
        return current_mode
```

Les trois solutions combinées : hysteresis + cooldown + confirmation. C'est de la ceinture-bretelles-parachute. Mais sur un levier x5, l'excès de prudence n'existe pas.

---

## Pseudo-code complet

```python
import time
from dataclasses import dataclass
from enum import IntEnum

class Mode(IntEnum):
    CASH  = 0
    RANGE = 1
    BEAR  = 2
    BULL  = 3

@dataclass
class MarketState:
    price: float
    ema_20: float
    ema_50: float
    rsi_14: float
    volatility_24h: float  # en %
    change_24h: float      # en %

@dataclass
class GridConfig:
    mode: Mode
    bias_buy: float     # 0.0 a 1.0
    bias_sell: float    # 0.0 a 1.0
    spacing_dot: float  # en %
    spacing_sol: float  # en %
    leverage: int
    capital_pct: float  # % du balance a utiliser
    center_offset: float  # decalage du centre en %

# --- Configurations par mode ---

GRID_CONFIGS = {
    Mode.CASH: None,  # pas de grid
    Mode.RANGE: GridConfig(
        mode=Mode.RANGE,
        bias_buy=0.50, bias_sell=0.50,
        spacing_dot=1.0, spacing_sol=2.0,
        leverage=5, capital_pct=0.80, center_offset=0.0
    ),
    Mode.BEAR: GridConfig(
        mode=Mode.BEAR,
        bias_buy=0.30, bias_sell=0.70,
        spacing_dot=1.5, spacing_sol=2.5,
        leverage=3, capital_pct=0.60, center_offset=-0.3
    ),
    Mode.BULL: GridConfig(
        mode=Mode.BULL,
        bias_buy=0.70, bias_sell=0.30,
        spacing_dot=0.8, spacing_sol=1.5,
        leverage=5, capital_pct=0.90, center_offset=0.5
    ),
}

# --- Hysteresis ---

# Pour entrer dans un mode
ENTER_THRESHOLDS = {
    Mode.CASH:  {"vol_min": 5.0},
    Mode.BEAR:  {"rsi_max": 40, "change_max": -2.0, "price_below_ema50": True},
    Mode.BULL:  {"rsi_min": 50, "change_min": 1.0, "price_above_ema20": True, "ema20_above_ema50": True},
    Mode.RANGE: {"vol_max": 3.0, "rsi_min": 40, "rsi_max": 60, "change_abs_max": 2.0},
}

# Pour SORTIR d'un mode (seuils relaches)
EXIT_THRESHOLDS = {
    Mode.CASH:  {"vol_max": 4.0},   # sort du cash quand vol redescend sous 4%
    Mode.BEAR:  {"rsi_min": 45, "change_min": -1.0},
    Mode.BULL:  {"rsi_max": 45, "change_max": 0.5},
    Mode.RANGE: {"vol_min": 3.5},
}

# --- Anti-whipsaw ---

MIN_MODE_DURATION = 2 * 3600       # 2h minimum
CONFIRMATIONS_REQUIRED = 3         # 3 checks consecutifs
CHECK_INTERVAL = 300               # 5 minutes

# --- Coeur de l'algorithme ---

class AdaptiveTrader:
    def __init__(self):
        self.current_mode = Mode.CASH
        self.mode_start_time = time.time()
        self.candidate_mode = None
        self.candidate_count = 0
        self.active_grids = {}
        self.trade_log = []

    def fetch_market_state(self, pair: str) -> MarketState:
        """Appelle Kraken API, calcule les indicateurs."""
        # candles = kraken.ohlc(pair, interval=60)
        # ... calcul RSI, EMA, volatilite ...
        pass  # implementation avec kraken_api.py existant

    def detect_regime(self, state: MarketState) -> Mode:
        """Determine le mode optimal selon l'etat du marche."""

        # CASH est toujours prioritaire
        if state.volatility_24h > ENTER_THRESHOLDS[Mode.CASH]["vol_min"]:
            return Mode.CASH

        # BEAR check
        if (state.rsi_14 < ENTER_THRESHOLDS[Mode.BEAR]["rsi_max"]
            and state.change_24h < ENTER_THRESHOLDS[Mode.BEAR]["change_max"]
            and state.price < state.ema_50):

            if state.change_24h <= -5.0:
                return Mode.CASH  # crash = cash, pas bear
            return Mode.BEAR

        # BULL check
        if (state.rsi_14 > ENTER_THRESHOLDS[Mode.BULL]["rsi_min"]
            and state.change_24h > ENTER_THRESHOLDS[Mode.BULL]["change_min"]
            and state.price > state.ema_20
            and state.ema_20 > state.ema_50):
            return Mode.BULL

        # RANGE check
        if (state.volatility_24h < ENTER_THRESHOLDS[Mode.RANGE]["vol_max"]
            and ENTER_THRESHOLDS[Mode.RANGE]["rsi_min"] <= state.rsi_14 <= ENTER_THRESHOLDS[Mode.RANGE]["rsi_max"]
            and abs(state.change_24h) < ENTER_THRESHOLDS[Mode.RANGE]["change_abs_max"]
            and state.ema_20 * 0.99 <= state.price <= state.ema_50 * 1.01):
            return Mode.RANGE

        # Rien ne matche = CASH
        return Mode.CASH

    def should_exit_current_mode(self, state: MarketState) -> bool:
        """Verifie si les conditions de SORTIE du mode actuel sont remplies."""
        mode = self.current_mode

        if mode == Mode.CASH:
            return state.volatility_24h < EXIT_THRESHOLDS[Mode.CASH]["vol_max"]

        if mode == Mode.BEAR:
            return (state.rsi_14 > EXIT_THRESHOLDS[Mode.BEAR]["rsi_min"]
                    or state.change_24h > EXIT_THRESHOLDS[Mode.BEAR]["change_min"])

        if mode == Mode.BULL:
            return (state.rsi_14 < EXIT_THRESHOLDS[Mode.BULL]["rsi_max"]
                    or state.change_24h < EXIT_THRESHOLDS[Mode.BULL]["change_max"])

        if mode == Mode.RANGE:
            return state.volatility_24h > EXIT_THRESHOLDS[Mode.RANGE]["vol_min"]

        return False

    def try_switch_mode(self, new_mode: Mode) -> Mode:
        """Anti-whipsaw : cooldown + confirmation."""
        now = time.time()

        # Exception : vers CASH = immediat (survie)
        if new_mode == Mode.CASH and self.current_mode != Mode.CASH:
            return new_mode

        # Cooldown check
        elapsed = now - self.mode_start_time
        if elapsed < MIN_MODE_DURATION:
            return self.current_mode  # trop tot

        # Confirmation check
        if new_mode == self.candidate_mode:
            self.candidate_count += 1
        else:
            self.candidate_mode = new_mode
            self.candidate_count = 1

        if self.candidate_count >= CONFIRMATIONS_REQUIRED:
            self.candidate_mode = None
            self.candidate_count = 0
            return new_mode

        return self.current_mode  # pas encore confirme

    def apply_mode(self, mode: Mode, pair: str, state: MarketState):
        """Ferme les grids existantes et ouvre les nouvelles."""
        config = GRID_CONFIGS.get(mode)

        if config is None:
            # MODE CASH : tout fermer
            self.close_all_grids(pair)
            self.log(f"[CASH] {pair} — grids fermees, capital protege")
            return

        # Fermer la grid existante si le mode change
        if pair in self.active_grids:
            self.close_all_grids(pair)

        # Calculer les parametres de la nouvelle grid
        center = state.price * (1 + config.center_offset / 100)
        n_buy  = int(10 * config.bias_buy * 2)
        n_sell = int(10 * config.bias_sell * 2)

        spacing = config.spacing_dot if "DOT" in pair else config.spacing_sol

        # Creer les ordres
        orders = []
        for i in range(1, n_buy + 1):
            price = center * (1 - spacing * i / 100)
            orders.append(("buy", price))

        for i in range(1, n_sell + 1):
            price = center * (1 + spacing * i / 100)
            orders.append(("sell", price))

        # Envoyer a Kraken via Martin
        # martin.create_grid(pair, orders, leverage=config.leverage)

        self.active_grids[pair] = {
            "mode": mode,
            "config": config,
            "center": center,
            "orders": orders,
            "opened_at": time.time(),
        }

        self.log(f"[{mode.name}] {pair} — grid {n_buy}B/{n_sell}S, "
                 f"spacing {spacing}%, x{config.leverage}, "
                 f"centre {center:.4f}")

    def close_all_grids(self, pair: str):
        """Ferme toutes les positions et ordres pour une paire."""
        # kraken.cancel_all_orders(pair)
        # kraken.close_all_positions(pair)
        if pair in self.active_grids:
            del self.active_grids[pair]

    def log(self, message: str):
        """Log pour debug et journal."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{ts} | {message}"
        self.trade_log.append(entry)
        print(entry)

    # === BOUCLE PRINCIPALE ===

    def run(self, pairs: list[str]):
        """Boucle principale — tourne indefiniment."""
        self.log(f"Demarrage AdaptiveTrader — paires: {pairs}")
        self.log(f"Mode initial: {self.current_mode.name}")

        while True:
            for pair in pairs:
                try:
                    # 1. Lire le marche
                    state = self.fetch_market_state(pair)

                    # 2. Detecter le regime
                    raw_signal = self.detect_regime(state)

                    # 3. Verifier si on doit sortir du mode actuel
                    should_exit = self.should_exit_current_mode(state)

                    if raw_signal != self.current_mode and should_exit:
                        # 4. Anti-whipsaw : cooldown + confirmation
                        new_mode = self.try_switch_mode(raw_signal)

                        if new_mode != self.current_mode:
                            old = self.current_mode
                            self.current_mode = new_mode
                            self.mode_start_time = time.time()
                            self.log(f"=== SWITCH {old.name} -> {new_mode.name} ===")

                            # 5. Appliquer le nouveau mode
                            self.apply_mode(new_mode, pair, state)

                    elif pair not in self.active_grids and self.current_mode != Mode.CASH:
                        # Pas de grid active mais on est pas en cash = lancer
                        self.apply_mode(self.current_mode, pair, state)

                except Exception as e:
                    self.log(f"ERREUR {pair}: {e}")
                    # En cas d'erreur, on ne panique pas, on continue

            time.sleep(CHECK_INTERVAL)


# === LANCEMENT ===

if __name__ == "__main__":
    trader = AdaptiveTrader()
    trader.run(["DOTUSD", "SOLUSD"])
```

---

## Diagramme de transitions

```
                    vol > 5% (immediat)
            ┌──────────────────────────────┐
            │                              │
            ▼                              │
    ┌──────────────┐     vol < 4%    ┌─────┴────────┐
    │   MODE 0     │ ◄──────────────►│   MODE 1     │
    │   CASH       │                 │   RANGE      │
    │   (proteger) │                 │   (grids     │
    └──────────────┘                 │    symetrique)│
            ▲                        └──┬────┬──────┘
            │                           │    │
     crash -5%                     RSI<40│    │RSI>50
            │                    chg<-2% │    │chg>+1%
            │                           │    │
            │    ┌──────────────┐       │    │  ┌──────────────┐
            │    │   MODE 2     │◄──────┘    └─►│   MODE 3     │
            └────│   BEAR       │               │   BULL       │
                 │   (short     │               │   (long      │
                 │    biaise)   │               │    agressif) │
                 └──────────────┘               └──────────────┘
                        │                              │
                        └──────── RSI 40-60 ───────────┘
                                (retour RANGE)
```

---

## Parametres specifiques par paire

Les donnees du backtest du 26 mars montrent que DOT et SOL ne se comportent pas pareil :

| Parametre            | DOT                  | SOL                  | Pourquoi                              |
|----------------------|----------------------|----------------------|---------------------------------------|
| Correlation BTC      | 0.59 (faible)        | 0.88 (forte)         | DOT est un franc-tireur               |
| Beta vs BTC          | 0.96                 | 1.20                 | SOL amplifie, DOT non                 |
| Accord directionnel  | 76%                  | 88%                  | DOT desobeit 1 fois sur 4             |
| Spacing RANGE        | 1.0%                 | 2.0%                 | DOT bouge moins, spacing serre        |
| Spacing BEAR         | 1.5%                 | 2.5%                 | Plus large en bear pour les deux       |
| Spacing BULL         | 0.8%                 | 1.5%                 | Serre en bull, on capture tout         |
| Levier max           | x5                   | x5                   | Identique                             |
| Capital max          | 50% du balance       | 50% du balance       | Jamais 100% sur une seule paire       |

**DOT est dangereux.** Correlation 0.59, accord directionnel 76%, ratio qui derive vers le bas sur les quartiles. L'algo doit etre plus conservateur sur DOT : spacing plus large, confirmation supplementaire avant de passer en BULL.

```python
# Override pour DOT : 1 confirmation de plus
CONFIRMATIONS_DOT = CONFIRMATIONS_REQUIRED + 1  # 4 au lieu de 3
```

---

## Ce que ca changerait sur les 15 derniers jours

Exercice de pensee sur l'historique reel :

- **Jour 1-5 (12-17 mars)** : DOT entre 1.28 et 1.35, volatilite basse → MODE 1 RANGE. C'est ce qu'on a fait, et ca marchait.
- **Jour 6-8 (18-20 mars)** : DOT chute vers 1.20, RSI < 40 → MODE 2 BEAR LIGHT. On aurait eu des grids biaisees short au lieu de symetriques. Moins de pertes sur les buys.
- **Jour 9-12 (21-24 mars)** : Volatilite haute, 6 recentrages en un jour → MODE 0 CASH. On aurait ete hors marche. Le -11% n'aurait pas eu lieu.
- **Jour 13-15 (25-27 mars)** : Silence total, grids vides → MODE 0 CASH (pas de signal clair). Correct.

**Estimation grossiere** : au lieu de -11%, on serait entre -2% et +3%. La perte vient presque entierement des jours ou on est reste en RANGE alors que le marche etait en BEAR.

---

## Risques et limites

1. **Overfitting** : ces seuils sont calibres sur ce qu'on a vecu. Le prochain crash ne ressemblera pas au dernier.
   - Mitigation : revoir les seuils toutes les 2 semaines avec les nouvelles donnees.

2. **Frais de transition** : chaque changement de mode = fermeture + reouverture. Sur Kraken Futures, ca coute ~0.05% par aller-retour.
   - Mitigation : le cooldown de 2h + 3 confirmations = max 12 transitions par jour en theorie, 2-3 en pratique.

3. **Latence API** : si Kraken est lent, on rate la fenetre.
   - Mitigation : timeout de 10s, retry 1 fois, sinon on garde le mode actuel.

4. **Le RSI ment** : en tendance forte, le RSI peut rester suroverbought/oversold longtemps.
   - Mitigation : ne jamais utiliser le RSI seul. Toujours combine avec price vs EMA et change_24h.

5. **DOT** : correlation 0.59 veut dire que 41% du temps, il fait ce qu'il veut. L'algo sera souvent en retard sur DOT.
   - Mitigation : capital reduit (max 40% du balance sur DOT), spacing plus large, 1 confirmation de plus.

---

## Prochaine etape

Cet algorithme n'existe que sur papier. Pour le rendre reel :

1. **Implementer `fetch_market_state()`** avec l'API Kraken existante
2. **Calculer RSI et EMA** (numpy ou ta-lib)
3. **Backtest sur les 3 mois de donnees** qu'on a deja
4. **Comparer** : grids fixes vs adaptatives sur la meme periode
5. **Si +30% de gain en backtest** : deployer en paper trading 1 semaine
6. **Si paper trading confirme** : deployer sur la VM avec capital reel

L'algo n'est pas magique. C'est juste une grid qui ouvre les yeux.
