# 🏍️ Code Moto

Application web **simple** pour apprendre le **code moto** — l'épreuve théorique moto (ETM).

Pas d'installation, pas de compte, pas de pub. Tout fonctionne dans le navigateur,
et la progression est enregistrée sur ton appareil.

## ✨ Ce que tu peux faire

- **📚 Apprendre par thème** — réviser tranquillement, thème par thème.
- **⚡ Quiz rapide** — 10 questions au hasard pour s'échauffer.
- **📝 Examen blanc** — 40 questions, comme à l'épreuve (seuil de réussite : 35/40).
- **🔁 Mes erreurs** — rejouer uniquement les questions ratées jusqu'à les maîtriser.
- **🔥 Série** et **statistiques** — suivre sa progression et son meilleur score.

Chaque réponse est suivie d'une **explication** pour comprendre, pas seulement mémoriser.

## 📚 Thèmes couverts

| Thème | Contenu |
|-------|---------|
| 🦺 Équipement & protection | Casque, gants, gilet, EPI, visibilité |
| 🚸 Signalisation & panneaux | Panneaux, feux, marquages au sol |
| 📋 Réglementation & vitesses | Limitations, permis (A1/A2/A), alcool, points |
| ⚠️ Sécurité & dangers | Adhérence, angles morts, météo, anticipation |
| 🛣️ Conduite & trajectoire | Trajectoire de sécurité, freinage, virages |
| 🔧 Mécanique & entretien | Pneus, chaîne, ABS, contrôles avant départ |
| 🚑 Premiers secours | Protéger-Alerter-Secourir, casque, hémorragie |
| 🌿 Environnement & partage | Piétons, cyclistes, bruit, éco-conduite |

## ▶️ Utilisation

Ouvre simplement `index.html` dans un navigateur, ou via GitHub Pages.

Sur téléphone, tu peux **« Ajouter à l'écran d'accueil »** pour l'utiliser comme une appli.

## 🛠️ Technique

100 % statique : HTML + CSS + JavaScript natif, **aucune dépendance**.

```
code-moto/
├── index.html             # Structure
├── style.css              # Style (thème sombre, responsive)
├── app.js                 # Logique (navigation, quiz, score)
├── questions.js           # Banque de questions + explications
└── manifest.webmanifest   # Installable sur mobile (PWA)
```

### Ajouter une question

Édite `questions.js` et ajoute un objet au tableau `QUESTIONS` :

```js
{
  id: 61, theme: "securite", illu: "⚠️", multi: false,
  q: "Ta question ?",
  answers: [
    { t: "Bonne réponse", ok: true },
    { t: "Mauvaise réponse", ok: false },
  ],
  explain: "L'explication affichée après la réponse.",
}
```

> ⚠️ Ce contenu est un outil de **révision** pédagogique. Pour passer l'examen,
> réfère-toi toujours aux supports officiels et au Code de la route en vigueur.
