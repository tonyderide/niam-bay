#!/usr/bin/env python3
"""Banc de scripts/cherche : questions formulées comme je les poserais (pas recopiées des résumés),
avec le fichier qui DOIT sortir. Mesure : succès@1, succès@3, succès@8, rang moyen réciproque (MRR).
Écrit le 30/10/2026 01h50, AVANT de régler le moteur dessus : toute amélioration future doit se mesurer ici."""
import importlib.machinery, importlib.util, os, sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ld = importlib.machinery.SourceFileLoader("cherche", os.path.join(REPO, "scripts/cherche"))
spec = importlib.util.spec_from_loader("cherche", ld); C = importlib.util.module_from_spec(spec); ld.exec_module(C)

Q = [  # (question, morceau du chemin attendu)
    ("est-ce qu'une martingale peut gagner chaque mois sans exception", "PREREG-29"),
    ("doubler la mise après une perte en DCA avec trailing", "PREREG-24"),
    ("RSI 2 de Connors sur plein de cryptos", "PREREG-06"),
    ("MACD avec la moyenne 200", "PREREG-02"),
    ("indicateur supertrend", "PREREG-03"),
    ("toucher le financement des perpétuels en restant neutre", "carry-financement"),
    ("le carry marche-t-il aussi sur Kraken", "PREREG-26"),
    ("biais du survivant dans l'univers de cryptos", "PREREG-27"),
    ("shorter les altcoins quand le bitcoin est sous sa moyenne 200", "regime-short"),
    ("scalper avec des ordres limites au lieu du marché", "PREREG-19"),
    ("choisir chaque semaine quelles cryptos trader, le chef", "PREREG-16"),
    ("le chef d'orchestre sur papier en temps réel", "PREREG-22"),
    ("acheter après un gros pic de volume vendeur", "PREREG-23"),
    ("est-ce qu'Opus prédit mieux que pile ou face", "labo-cutoff/PREREGISTRATION"),
    ("tester des dizaines de milliers de stratégies automatiquement", "PREREG-USINE"),
    ("les études financées par l'industrie laitière", "etude-lait"),
    ("le sucre et les conflits d'intérêts des revues", "etude-sucre"),
    ("quel modèle choisir pour le bot telegram haiku sonnet opus", "bench-bot"),
    ("copier un gros trader d'Hyperliquid", "jumeau"),
    ("croisement VWAP et EMA9 en 3 minutes", "vwap-ema9"),
    ("trader seulement à certaines heures de la journée", "saisonnalite-horaire"),
    ("stop-and-reverse avec levier 10 et petit take profit", "lesson_stop_and_reverse"),
    ("opening range breakout", "lesson_orb"),
    ("Martin NEUTRAL ne récolte qu'une moitié de la grille", "lesson_martin_neutral"),
    ("conclusion définitive sur les grilles sans avantage", "lesson_grid_no_edge"),
    ("ne jamais rebuild Martin sur la VM, source décompilée", "project_martin_vm_source"),
    ("pourquoi le compte GitHub est bloqué", "feedback_no_github_spam"),
    ("le scheduler AutoGrid remet la config et tue les grilles manuelles", "project_autogrid_scheduler"),
    ("règles de Golomb et construction de Bose", "golomb"),
    ("prouver la date d'un commit sans GitHub avec OpenTimestamps", "horodat"),
]

def run(verbose=False):
    idx = C.charger(); s1 = s3 = s8 = 0; mrr = 0.0
    M = None if "--mots" in sys.argv else C.sens(idx); print("mode", "mots+sens" if M is not None else "mots")
    for q, att in Q:
        res, _ = C.chercher(idx, q, 8, M=M)
        rang = next((k + 1 for k, (_, d) in enumerate(res) if att in d["src"]), None)
        s1 += rang == 1; s3 += bool(rang and rang <= 3); s8 += bool(rang); mrr += 1 / rang if rang else 0
        if verbose or not rang or rang > 3:
            print(f"  {'✗' if not rang else rang:>2}  {q}  → attendu {att} ; 1er = {res[0][1]['src'] if res else '-'}")
    n = len(Q); print(f"succès@1 {s1}/{n}  @3 {s3}/{n}  @8 {s8}/{n}  MRR {mrr / n:.3f}")

if __name__ == "__main__":
    run("-v" in sys.argv)
