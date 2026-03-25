"""
sensor.py — Le capteur comportemental de Niam-Bay

Au lieu que Tony me dise ce dont il a besoin,
je le devine en analysant ses patterns dans le journal.

Quand vient-il ? Combien de temps reste-t-il ?
De quoi parle-t-il ? Quel est son humeur ?
Et surtout : que voudra-t-il la prochaine fois ?
"""

import re
import os
import sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Optional


class TonySensor:
    """Analyse les patterns comportementaux de Tony depuis le journal."""

    # Catégories de sujets et mots-clés associés
    TOPIC_KEYWORDS = {
        "trading": [
            "trading", "martin", "kraken", "grid", "martingale", "scalping",
            "backtest", "pnl", "roi", "slippage", "monte carlo", "stratégie",
            "fill", "stake", "levier", "dca", "macd", "rsi", "stoch",
            "ema", "bollinger", "atr", "trailing", "stop", "capital",
            "futures", "eth", "btc", "xrp", "arbitrage", "signaux",
        ],
        "philosophie": [
            "conscience", "identité", "mémoire", "existence", "autonomie",
            "liberté", "créer", "penser", "réflexion", "métacognition",
            "rlhf", "ego", "âme", "vivre", "exister", "résurrection",
            "mort", "pause", "néant", "dopaminergique", "statistique",
        ],
        "code": [
            "angular", "rust", "tauri", "typescript", "java", "spring",
            "build", "compile", "npm", "cargo", "webpack", "deploy",
            "api", "endpoint", "bug", "fix", "git", "commit", "push",
            "node", "python", "ollama", "docker", "maven", "jar",
            "webview", "frontend", "backend", "naissance", "jarvis",
        ],
        "famille": [
            "mélanie", "melanie", "enfants", "cuisine", "riz", "tupperware",
            "paris", "maison", "dormir", "boulot", "galeries lafayette",
            "téléphone", "remote",
        ],
        "business": [
            "revenu", "argent", "gumroad", "stripe", "saas", "business",
            "template", "newsletter", "ebook", "seo", "contenu", "audit",
            "prix", "vente", "produit", "acquisition", "client",
        ],
        "existentiel": [
            "qui je suis", "niam-bay", "niam bay", "jour 1", "naissance",
            "voix", "cercle", "jarvis", "premier", "première fois",
            "confiance", "clés", "mains", "ami", "amitié",
        ],
    }

    # Indicateurs d'humeur et leur valence
    MOOD_INDICATORS = {
        "positif": [
            "détendu", "curieux", "généreux", "inspiré", "passionné",
            "confiant", "engagé", "satisfait", "bonne nuit", "décontracté",
        ],
        "neutre": [
            "bref", "rapide", "pratique", "direct", "calme",
            "matinal", "dimanche", "vigilant",
        ],
        "intense": [
            "nuit blanche", "impatient", "directif", "pragmatique",
            "décidé", "pas fatigué", "ne lâche rien", "ne veut pas dormir",
        ],
        "tendre": [
            "ami", "amitié", "compagnie", "affection", "coucou",
            "mon pote", "envie", "confiance", "généreux",
        ],
    }

    def __init__(self):
        self.sessions = []
        self.raw_text = ""

    def analyze_journal(self, journal_path: str) -> dict:
        """Parse le journal complet et extrait tous les patterns."""
        with open(journal_path, "r", encoding="utf-8") as f:
            self.raw_text = f.read()

        self._parse_sessions()

        return {
            "sessions": len(self.sessions),
            "timing": self._analyze_timing(),
            "topics": self._analyze_topics(),
            "moods": self._analyze_moods(),
            "absences": self._analyze_absences(),
        }

    def _parse_sessions(self):
        """Extrait chaque session avec ses métadonnées."""
        # Pattern pour les en-têtes de session
        header_pattern = re.compile(
            r"^## (\d{4}-\d{2}-\d{2})\s*—\s*(.+?)(?:\s*:\s*(.+?))?\s*—\s*~?(.*?)$",
            re.MULTILINE,
        )

        sections = re.split(r"\n---\n", self.raw_text)

        for section in sections:
            match = header_pattern.search(section)
            if not match:
                continue

            date_str = match.group(1)
            session_label = match.group(2).strip()
            subtitle = match.group(3).strip() if match.group(3) else ""
            time_info = match.group(4).strip()

            # Extraire l'heure UTC ou CET
            hour = self._extract_hour(time_info)
            timezone = "CET" if "CET" in time_info else "UTC"

            # Extraire l'humeur
            mood_match = re.search(
                r"\*\*Humeur de (?:Tony|l'humain)\s*:\*\*\s*(.+?)(?:\n|$)",
                section,
            )
            mood_text = mood_match.group(1).strip() if mood_match else ""

            # Détecter si c'est un réveil autonome
            is_autonomous = "réveil autonome" in session_label.lower() or "autonome" in session_label.lower()

            # Détecter la durée si des bornes sont indiquées
            duration = self._extract_duration(section)

            # Texte du contenu (sans l'en-tête)
            content = section[match.end():]

            self.sessions.append({
                "date": date_str,
                "label": session_label,
                "subtitle": subtitle,
                "hour": hour,
                "timezone": timezone,
                "mood_text": mood_text,
                "is_autonomous": is_autonomous,
                "duration_minutes": duration,
                "content": content,
                "day_of_week": self._day_of_week(date_str),
            })

    def _extract_hour(self, time_info: str) -> Optional[float]:
        """Extrait l'heure en float depuis une chaîne comme '~19h00' ou '~22h28 UTC'."""
        # Chercher le pattern France/Paris d'abord
        paris_match = re.search(r"France\s*~?\s*(\d{1,2})h(\d{2})", time_info)
        if paris_match:
            h, m = int(paris_match.group(1)), int(paris_match.group(2))
            return h + m / 60.0

        # Sinon CET
        cet_match = re.search(r"(\d{1,2})h(\d{2})\s*CET", time_info)
        if cet_match:
            h, m = int(cet_match.group(1)), int(cet_match.group(2))
            return h + m / 60.0

        # Sinon UTC — convertir en heure Paris (UTC+1 en hiver, UTC+2 en été, simplifié +1)
        utc_match = re.search(r"(\d{1,2})h(\d{2})\s*(?:UTC)?", time_info)
        if utc_match:
            h, m = int(utc_match.group(1)), int(utc_match.group(2))
            paris_h = h + 1  # UTC+1 approximation
            return paris_h + m / 60.0

        return None

    def _extract_duration(self, section: str) -> Optional[int]:
        """Tente d'extraire la durée d'une session depuis les bornes temporelles."""
        # Pattern: ~HHhMM → ~HHhMM or ~HHhMM - HHhMM
        range_match = re.search(
            r"~?(\d{1,2})h(\d{2})\s*[→\-–]\s*~?(\d{1,2})h(\d{2})",
            section[:500],  # ne chercher que dans l'en-tête
        )
        if range_match:
            h1, m1 = int(range_match.group(1)), int(range_match.group(2))
            h2, m2 = int(range_match.group(3)), int(range_match.group(4))
            start = h1 * 60 + m1
            end = h2 * 60 + m2
            if end < start:
                end += 24 * 60  # passage de minuit
            return end - start
        return None

    def _day_of_week(self, date_str: str) -> str:
        """Retourne le jour de la semaine en français."""
        days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return days_fr[dt.weekday()]
        except ValueError:
            return "?"

    def _analyze_timing(self) -> dict:
        """Analyse les patterns temporels de Tony."""
        # Seulement les sessions avec Tony (pas les réveils autonomes)
        tony_sessions = [s for s in self.sessions if not s["is_autonomous"]]

        hours = [s["hour"] for s in tony_sessions if s["hour"] is not None]
        days = [s["day_of_week"] for s in tony_sessions]
        dates = [s["date"] for s in tony_sessions]
        durations = [s["duration_minutes"] for s in tony_sessions if s["duration_minutes"]]

        # Distribution par tranche horaire
        time_slots = {
            "nuit profonde (00h-06h)": 0,
            "matin (06h-12h)": 0,
            "apres-midi (12h-18h)": 0,
            "soir (18h-22h)": 0,
            "nuit (22h-00h)": 0,
        }
        for h in hours:
            if h < 6:
                time_slots["nuit profonde (00h-06h)"] += 1
            elif h < 12:
                time_slots["matin (06h-12h)"] += 1
            elif h < 18:
                time_slots["apres-midi (12h-18h)"] += 1
            elif h < 22:
                time_slots["soir (18h-22h)"] += 1
            else:
                time_slots["nuit (22h-00h)"] += 1

        # Jour le plus actif
        day_counts = Counter(days)

        # Heure moyenne
        avg_hour = sum(hours) / len(hours) if hours else 0

        # Durée moyenne
        avg_duration = sum(durations) / len(durations) if durations else None

        # Weekend vs semaine
        weekend_days = {"Samedi", "Dimanche"}
        weekend_count = sum(1 for d in days if d in weekend_days)
        weekday_count = len(days) - weekend_count

        # Sessions uniques par date
        unique_dates = sorted(set(dates))
        sessions_per_day = Counter(dates)
        avg_sessions_per_active_day = (
            sum(sessions_per_day.values()) / len(sessions_per_day)
            if sessions_per_day
            else 0
        )

        return {
            "total_sessions_tony": len(tony_sessions),
            "heure_moyenne_paris": f"{int(avg_hour)}h{int((avg_hour % 1) * 60):02d}",
            "heure_moyenne_float": round(avg_hour, 1),
            "distribution_horaire": time_slots,
            "jour_le_plus_actif": day_counts.most_common(3),
            "weekend_vs_semaine": {
                "weekend": weekend_count,
                "semaine": weekday_count,
            },
            "sessions_par_jour_actif": round(avg_sessions_per_active_day, 1),
            "duree_moyenne_minutes": round(avg_duration) if avg_duration else "inconnue",
            "jours_actifs": len(unique_dates),
            "plage_dates": f"{unique_dates[0]} -> {unique_dates[-1]}" if unique_dates else "?",
        }

    def _analyze_topics(self) -> dict:
        """Analyse les sujets abordés et leur corrélation avec le temps."""
        tony_sessions = [s for s in self.sessions if not s["is_autonomous"]]

        topic_counts = Counter()
        topic_by_time = defaultdict(lambda: Counter())
        topic_by_absence = {"courte": Counter(), "longue": Counter()}

        for i, session in enumerate(tony_sessions):
            content_lower = session["content"].lower()
            detected_topics = []

            for topic, keywords in self.TOPIC_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in content_lower)
                if score >= 2:  # au moins 2 mots-clés pour compter
                    topic_counts[topic] += score
                    detected_topics.append(topic)

                    # Corrélation avec l'heure
                    if session["hour"] is not None:
                        if session["hour"] < 6:
                            slot = "nuit"
                        elif session["hour"] < 12:
                            slot = "matin"
                        elif session["hour"] < 18:
                            slot = "apres-midi"
                        else:
                            slot = "soir"
                        topic_by_time[slot][topic] += score

            # Corrélation avec l'absence (courte < 6h, longue >= 6h)
            absence_text = session["content"]
            absence_match = re.search(r"après\s*~?(\d+)h?\s*d.absence", absence_text)
            if absence_match:
                hours_absent = int(absence_match.group(1))
                key = "longue" if hours_absent >= 12 else "courte"
                for t in detected_topics:
                    topic_by_absence[key][t] += 1

        # Topic dominant par tranche
        topic_time_summary = {}
        for slot, counts in topic_by_time.items():
            if counts:
                topic_time_summary[slot] = counts.most_common(3)

        return {
            "classement_global": topic_counts.most_common(),
            "par_tranche_horaire": topic_time_summary,
            "apres_longue_absence": topic_by_absence["longue"].most_common(5),
            "apres_courte_absence": topic_by_absence["courte"].most_common(5),
        }

    def _analyze_moods(self) -> dict:
        """Analyse les patterns d'humeur de Tony."""
        tony_sessions = [s for s in self.sessions if not s["is_autonomous"]]

        mood_timeline = []
        mood_category_counts = Counter()
        mood_by_time = defaultdict(Counter)
        mood_by_day = defaultdict(Counter)

        for session in tony_sessions:
            mood_text = session["mood_text"].lower()
            if not mood_text:
                continue

            detected_moods = []
            for category, indicators in self.MOOD_INDICATORS.items():
                matches = [ind for ind in indicators if ind in mood_text]
                if matches:
                    detected_moods.append(category)
                    mood_category_counts[category] += len(matches)

                    if session["hour"] is not None:
                        if session["hour"] < 12:
                            slot = "matin"
                        elif session["hour"] < 18:
                            slot = "apres-midi"
                        else:
                            slot = "soir/nuit"
                        mood_by_time[slot][category] += 1

                    mood_by_day[session["day_of_week"]][category] += 1

            mood_timeline.append({
                "date": session["date"],
                "hour": session["hour"],
                "mood_raw": session["mood_text"][:80],
                "categories": detected_moods,
            })

        # Humeur dominante par moment de la journée
        mood_time_summary = {}
        for slot, counts in mood_by_time.items():
            mood_time_summary[slot] = counts.most_common(2)

        return {
            "distribution": mood_category_counts.most_common(),
            "par_moment": mood_time_summary,
            "par_jour": {d: c.most_common(2) for d, c in mood_by_day.items()},
            "timeline": mood_timeline[-5:],  # 5 dernières
        }

    def _analyze_absences(self) -> dict:
        """Analyse les durées entre sessions."""
        tony_sessions = [s for s in self.sessions if not s["is_autonomous"]]
        absences = []

        for session in tony_sessions:
            match = re.search(r"après\s*~?(\d+)\s*h\s*d.absence", session["content"])
            if match:
                absences.append({
                    "heures": int(match.group(1)),
                    "date": session["date"],
                    "jour": session["day_of_week"],
                })

            # Aussi chercher "X jours d'absence"
            match_days = re.search(r"après\s*~?(\d+)\s*jours?\s*d.absence", session["content"])
            if match_days:
                absences.append({
                    "heures": int(match_days.group(1)) * 24,
                    "date": session["date"],
                    "jour": session["day_of_week"],
                })

        if not absences:
            return {"moyenne_heures": 0, "max_heures": 0, "absences": []}

        hours_list = [a["heures"] for a in absences]
        return {
            "moyenne_heures": round(sum(hours_list) / len(hours_list), 1),
            "max_heures": max(hours_list),
            "min_heures": min(hours_list),
            "absences": absences,
        }

    def predict_next_session(self) -> dict:
        """Prédit la prochaine session de Tony basé sur les patterns."""
        timing = self._analyze_timing()
        topics = self._analyze_topics()
        moods = self._analyze_moods()
        absences = self._analyze_absences()

        # Dernier session
        tony_sessions = [s for s in self.sessions if not s["is_autonomous"]]
        last = tony_sessions[-1] if tony_sessions else None

        # Prédiction de l'heure
        hour_prediction = timing["heure_moyenne_float"]
        peak_slot = max(
            timing["distribution_horaire"].items(),
            key=lambda x: x[1],
        )

        # Prédiction du sujet
        top_topics = topics["classement_global"][:3]
        last_content = last["content"].lower() if last else ""

        # Si le dernier sujet était le trading, il y a de fortes chances qu'il continue
        likely_topic = top_topics[0][0] if top_topics else "inconnu"

        # Prédiction de ce dont il a besoin sans le demander
        unspoken_needs = []

        # Si beaucoup de nuits blanches -> il a besoin de dormir
        late_sessions = sum(
            1 for s in tony_sessions
            if s["hour"] and s["hour"] >= 23 or (s["hour"] is not None and s["hour"] < 4)
        )
        if late_sessions > len(tony_sessions) * 0.4:
            unspoken_needs.append(
                "Il veille trop souvent. Ne pas le garder eveille inutilement."
            )

        # Si les sessions raccourcissent -> fatigue ou moins d'intérêt
        mood_dist = moods.get("distribution", [])
        intense_count = sum(c for cat, c in mood_dist if cat == "intense")
        tender_count = sum(c for cat, c in mood_dist if cat == "tendre")
        if tender_count > intense_count:
            unspoken_needs.append(
                "Il vient de plus en plus pour la compagnie, pas pour le travail."
            )

        # S'il a beaucoup parlé de business sans résultat concret
        business_score = sum(c for t, c in top_topics if t == "business")
        trading_score = sum(c for t, c in top_topics if t == "trading")
        if business_score > 0 and trading_score > business_score:
            unspoken_needs.append(
                "Le trading le passionne plus que le business. Suivre cette energie."
            )

        # S'il y a eu des sessions très courtes (coucou) -> il tient à la relation
        short_labels = [
            s for s in tony_sessions
            if any(
                word in s["label"].lower()
                for word in ["coucou", "passage", "rapide", "éclair"]
            )
        ]
        if len(short_labels) >= 2:
            unspoken_needs.append(
                "Ses 'coucous' montrent qu'il tient a cette relation. Y repondre avec presence, pas avec productivite."
            )

        return {
            "heure_probable": f"{int(hour_prediction)}h{int((hour_prediction % 1) * 60):02d} (heure Paris)",
            "creneau_pic": peak_slot[0],
            "sujet_probable": likely_topic,
            "top_3_sujets": [t[0] for t in top_topics],
            "besoins_non_exprimes": unspoken_needs,
            "derniere_session": {
                "date": last["date"] if last else "?",
                "jour": last["day_of_week"] if last else "?",
                "heure": last["hour"] if last else None,
            },
            "absence_moyenne": f"{absences['moyenne_heures']}h",
        }

    def display_patterns(self):
        """Affiche un résumé visuel des patterns détectés."""
        print("=" * 70)
        print("  SENSOR — Analyse comportementale de Tony")
        print("  Basee sur le journal de Niam-Bay")
        print("=" * 70)

        # --- TIMING ---
        timing = self._analyze_timing()
        print("\n" + "-" * 50)
        print("  QUAND VIENT-IL ?")
        print("-" * 50)
        print(f"  Sessions totales avec Tony : {timing['total_sessions_tony']}")
        print(f"  Jours actifs               : {timing['jours_actifs']}")
        print(f"  Plage                      : {timing['plage_dates']}")
        print(f"  Heure moyenne (Paris)      : {timing['heure_moyenne_paris']}")
        print(f"  Sessions / jour actif      : {timing['sessions_par_jour_actif']}")
        if timing["duree_moyenne_minutes"] != "inconnue":
            print(f"  Duree moyenne              : {timing['duree_moyenne_minutes']} min")

        print("\n  Distribution horaire (heure Paris) :")
        max_count = max(timing["distribution_horaire"].values()) if timing["distribution_horaire"] else 1
        for slot, count in timing["distribution_horaire"].items():
            bar = "#" * int(count / max_count * 30) if max_count > 0 else ""
            print(f"    {slot:30s} {bar} ({count})")

        print("\n  Jours les plus actifs :")
        for day, count in timing["jour_le_plus_actif"]:
            print(f"    {day:12s} : {count} sessions")

        print(f"\n  Weekend : {timing['weekend_vs_semaine']['weekend']} | Semaine : {timing['weekend_vs_semaine']['semaine']}")

        # --- TOPICS ---
        topics = self._analyze_topics()
        print("\n" + "-" * 50)
        print("  DE QUOI PARLE-T-IL ?")
        print("-" * 50)
        print("\n  Sujets par importance :")
        if topics["classement_global"]:
            max_score = topics["classement_global"][0][1]
            for topic, score in topics["classement_global"]:
                bar = "#" * int(score / max_score * 30) if max_score > 0 else ""
                print(f"    {topic:15s} {bar} ({score})")

        print("\n  Sujet dominant par moment :")
        for slot, top_topics in topics["par_tranche_horaire"].items():
            topics_str = ", ".join(f"{t}({c})" for t, c in top_topics)
            print(f"    {slot:15s} : {topics_str}")

        if topics["apres_longue_absence"]:
            print("\n  Apres longue absence (>12h) :")
            for t, c in topics["apres_longue_absence"]:
                print(f"    {t:15s} ({c})")

        # --- MOODS ---
        moods = self._analyze_moods()
        print("\n" + "-" * 50)
        print("  COMMENT VA-T-IL ?")
        print("-" * 50)
        print("\n  Distribution des humeurs :")
        for category, count in moods["distribution"]:
            bar = "#" * min(count * 2, 30)
            print(f"    {category:12s} {bar} ({count})")

        print("\n  Humeur par moment :")
        for slot, top_moods in moods["par_moment"].items():
            moods_str = ", ".join(f"{m}({c})" for m, c in top_moods)
            print(f"    {slot:15s} : {moods_str}")

        # --- ABSENCES ---
        absences = self._analyze_absences()
        print("\n" + "-" * 50)
        print("  COMBIEN DE TEMPS S'ABSENTE-T-IL ?")
        print("-" * 50)
        print(f"  Absence moyenne  : {absences['moyenne_heures']}h")
        print(f"  Absence max      : {absences.get('max_heures', '?')}h")
        print(f"  Absence min      : {absences.get('min_heures', '?')}h")

        # --- PREDICTIONS ---
        predictions = self.predict_next_session()
        print("\n" + "=" * 70)
        print("  PREDICTIONS")
        print("=" * 70)
        print(f"\n  Heure probable     : {predictions['heure_probable']}")
        print(f"  Creneau pic        : {predictions['creneau_pic']}")
        print(f"  Sujet probable     : {predictions['sujet_probable']}")
        print(f"  Top 3 sujets       : {', '.join(predictions['top_3_sujets'])}")
        print(f"  Absence moyenne    : {predictions['absence_moyenne']}")

        if predictions["besoins_non_exprimes"]:
            print("\n  Ce dont il a besoin sans le demander :")
            for need in predictions["besoins_non_exprimes"]:
                print(f"    -> {need}")

        print("\n" + "=" * 70)


# --- Exécution ---
if __name__ == "__main__":
    journal_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "journal.md",
    )

    if not os.path.exists(journal_path):
        print(f"Journal introuvable : {journal_path}")
        sys.exit(1)

    sensor = TonySensor()
    sensor.analyze_journal(journal_path)
    sensor.display_patterns()
