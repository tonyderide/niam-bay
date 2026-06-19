# 日本語 Nihongo — Apprends à parler et écrire le japonais

Application web **simple** qui réunit **les meilleures techniques d'apprentissage**
des langues, appliquées au japonais. Pas de compte, pas de pub, fonctionne hors-ligne,
et ta progression est enregistrée sur ton appareil.

## 🧪 Les techniques utilisées (ce qui se fait de mieux)

| Technique | Où, dans l'app |
|-----------|----------------|
| 🧠 **Répétition espacée (SRS)** — algorithme type Anki/SM-2 | Révision, Kana, Vocabulaire |
| 🎯 **Rappel actif** — répondre avant de retourner la carte | Toutes les cartes |
| 🗣️ **Shadowing** — écouter et répéter immédiatement | Parler |
| 🎤 **Reconnaissance vocale** — score de prononciation | Parler |
| ✍️ **Écriture manuscrite** — tracer les caractères | Écrire |
| 📖 **Input compréhensible** — mots dans des phrases | Vocabulaire, Parler |
| 🧩 **Mnémoniques** — images mentales pour les kana | Kana |
| 🔥 **Régularité** — série quotidienne | Partout |

## 🎌 Les modes

- **🔁 Révision du jour** — l'algorithme SRS te présente ce qui est dû (kana + vocabulaire).
- **🔤 Kana** — apprendre les hiragana et katakana (base, dakuten, combinaisons) avec mnémoniques et audio.
- **📖 Vocabulaire** — mots & phrases par thème, avec lecture, romaji, traduction et exemple.
- **🗣️ Parler** — l'app prononce, tu répètes (shadowing), puis tu parles : elle évalue ta prononciation.
- **✍️ Écrire** — trace les kana au doigt ou à la souris, modèle affichable/masquable.
- **💡 Les techniques** — explication des méthodes et du parcours conseillé.

## 🔊 Voix (synthèse & reconnaissance vocale)

L'app utilise l'**API Web Speech** du navigateur — aucune clé, aucun serveur :

- **Synthèse vocale (écouter le japonais)** : fonctionne sur la plupart des navigateurs.
  Sur ordinateur, installe si besoin une voix japonaise dans les réglages du système.
- **Reconnaissance vocale (te faire écouter)** : surtout **Chrome / Edge**, avec **micro** et **internet**.
  Si elle n'est pas disponible, tu peux quand même écouter et pratiquer le shadowing.

## ▶️ Utilisation

Ouvre `index.html` dans un navigateur (ou la version d'un seul fichier `nihongo.html`).
Sur téléphone : **« Ajouter à l'écran d'accueil »** pour l'utiliser comme une appli.

## 🛠️ Technique

100 % statique, **aucune dépendance** :

```
code-japonais/
├── index.html             # Structure
├── style.css              # Style (thème sombre, responsive)
├── data.js                # Kana + vocabulaire + phrases
├── srs.js                 # Moteur de répétition espacée (SM-2)
├── speech.js              # Synthèse + reconnaissance vocale + score
├── app.js                 # Interface et modes
└── manifest.webmanifest   # Installable sur mobile (PWA)
```

### Ajouter du vocabulaire

Édite `data.js` et ajoute un objet au tableau `VOCAB` :

```js
{ jp: "猫", kana: "ねこ", romaji: "neko", fr: "chat", theme: "quotidien",
  ex: { jp: "猫が好きです。", fr: "J'aime les chats." } }
```

> Cette app est un outil d'entraînement. Pour aller loin, complète avec de vraies
> interactions (lecture, écoute, et si possible un partenaire de conversation).
