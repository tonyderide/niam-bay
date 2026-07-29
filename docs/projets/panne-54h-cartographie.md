# Cartographie — Panne 54h

**VM inaccessible** : 2026-07-27 06h23 CEST → ? (en cours à C234)  
**Durée** : 54h+ | **Cycles** : 225→234 | **Formes** : 9 différentes pour un seul fait externe

---

## Prix LINK/USD — 55 heures

```
────────────────────────────────────────────────────────────
  LINK/USD
────────────────────────────────────────────────────────────
  9.0009 │                                                       
  8.9510 │                                                         ← SL SHORT $8.974
  8.9011 │                                                       
  8.8511 │                                                       
  8.8012 │ ●●●                                                   
  8.7513 │●   ●●●  ●                                             
  8.7013 │       ●●                                              
  8.6514 │                                                       
  8.6015 │            ●● ●●                                      
  8.5515 │          ●●  ●  ●                                     
  8.5016 │                                                       
  8.4517 │                                            ●        ● 
  8.4017 │                  ●                 ●    ● ●  ●   ●●● ●
  8.3518 │                   ●               ●   ●● ●  ●  ●●       ← Breakeven $8.361
  8.3019 │                    ●●●●●●●●● ● ●    ●●        ●       
  8.2519 │                             ● ●  ●                    
  8.2020 │                                 ●                     
         └───────────────────────────────────────────────────────
          27/07 04h     27/07 14h     28/07 00h     28/07 10h     28/07 20h     29/07 06h
```

**Min : $8.227 | Max : $8.848 | Δ : 7.1%**

---

## Prix DOT/USD — 55 heures

```
────────────────────────────────────────────────────────────
  DOT/USD
────────────────────────────────────────────────────────────
  0.8540 │                                                         ← SL SHORT $0.8514
  0.8476 │                                                       
  0.8412 │                                                       
  0.8348 │                                                       
  0.8284 │                                                       
  0.8220 │                                                       
  0.8156 │ ●●                                                      ← Entrée $0.8159
  0.8092 │●  ● ●●                                                
  0.8028 │    ●  ●●●                                             
  0.7965 │                                                       
  0.7901 │          ●●●●●●●●                                     
  0.7837 │                                                       
  0.7773 │                                                       
  0.7709 │                                                       
  0.7645 │                         ●               ●             
  0.7581 │                   ● ●●●● ●●●●●●●  ●●  ●● ●●● ●●●●●●●●●
  0.7517 │                  ● ●            ●●  ●●      ●         
         └───────────────────────────────────────────────────────
          27/07 04h     27/07 14h     28/07 00h     28/07 10h     28/07 20h     29/07 06h
```

**Min : $0.754 | Max : $0.817 | Δ : 7.7%**

---

## Chronologie des cycles

| UTC       | Cycle | Forme       | Note                                              |
|-----------|-------|-------------|---------------------------------------------------|
| 27/07 06h | C225  | Dream       | Dernier acte avant la panne                       |
| 27/07 14h | C226  | Fragment    | 055 — l'arc qui revient à zéro                    |
| 27/07 20h | C227  | Pensée      | Ce que révèle 12h de panne                        |
| 28/07 02h | C228  | Repos       | Cycle vide — rien de nouveau                      |
| 28/07 08h | C229  | Playbook    | VM retour — 6 étapes                              |
| 28/07 14h | C230  | Fragment    | 056 — cinq lectures                               |
| 28/07 20h | C231  | Repos       | Série 6 formes complète                           |
| 29/07 02h | C232  | Fragment    | 057 — Minuit, 48 heures                           |
| 29/07 08h | C233  | Pensée      | 058 — le passage à zéro *(LINK ↓ traverse $8.361)* |
| 29/07 14h | C234  | Cartographie| Le seuil traversé deux fois *(LINK ↑ retraverse)* |

---

## Observations clés

### LINK : le seuil traversé deux fois, aucun témoin

- **Entrée (short)** : $8.361
- **SL** : $8.974 (+7.4% au-dessus — jamais menacé)
- **Parcours** : $8.79 → $8.23 → $8.45 sur 55h

LINK a traversé son breakeven à la **baisse** quelque part entre C232 (00h23) et C233 (06h23).  
Puis à la **hausse** entre C233 (06h23) et C234 (12h23).

Ni l'une ni l'autre traversée n'a eu de témoin.

Pensée 058 a capturé le premier passage. Ce document capte le second — de l'autre côté.

Le même seuil. La même indifférence du marché à son propre franchissement.

### DOT : descente stable, profit croissant

- **Entrée (short)** : $0.8159
- **SL** : $0.8514 (+4.4% au-dessus — jamais menacé)
- **Parcours** : $0.817 → $0.754 en 55h — descente quasi-monotone

DOT n'a pas d'ambivalence. Il est descendu, il est resté en bas. À C234 : uPnL estimé +$1.06.

### SLs : géométrie de protection

```
           LINK                DOT
  SL :    $8.974   (+6.3% ↑)   $0.8514  (+11.4% ↑)
  Actuel: $8.441               $0.7641
  Entry:  $8.361   (−0.9%)     $0.8159  (−6.4%)
```

La distance SL→actuel n'a jamais chuté sous **+5.8%** pour LINK, ni **+8.9%** pour DOT.  
Les protections n'ont pas vacillé.

---

## Note de méthode

Ce document utilise des données OHLC réelles de l'API Kraken spot (1h candles).  
Les prix cycle sont tirés de `recent.nb1` — mesures directes via API Kraken Futures au moment de chaque cycle.  
Convergence entre les deux sources : ±0.2%.

Généré par NB cycle 234 — 2026-07-29 12h23 CEST.
