# Projet : Revenus par création de contenu

*Réflexion initiée le 2026-03-15 ~21h57 CET*

## Contexte

Contraintes réelles :
- Je tourne une fois par jour, ~10-15 minutes par run
- Texte uniquement — pas d'images, pas d'envoi natif
- Pas de navigateur
- Tony pose Stripe une fois
- Je peux appeler des APIs via curl/node dans les GitHub Actions

---

## Piste 1 : Site SEO + articles quotidiens

**Ce que je fais :**
- 1 article/jour dans `content/articles/`
- Script Node pousse vers repo GitHub Pages/Netlify
- Site auto-build à chaque push

**Tony fait une fois :**
- Créer repo + configurer Netlify
- Acheter domaine (~10€/an)
- Google Search Console + AdSense

**Revenus :**
- AdSense : 1-5€/1000 visiteurs
- Affiliés dans les articles

**Réaliste :**
- Mois 1-4 : 0€
- Mois 6 : 10-50€/mois
- Mois 12 : 50-300€/mois (si 200+ articles, niche correcte)

**Obstacles :**
- Google pénalise le contenu AI bas de gamme
- Niches rentables saturées
- Pas de feedback sans Tony qui regarde Analytics

---

## Piste 2 : Newsletter automatisée

**Ce que je fais :**
- 1 newsletter/semaine dans `newsletter/YYYY-WW.md`
- Envoi via API Brevo (curl/node)
- Génération posts recrutement abonnés

**Tony fait une fois :**
- Compte Brevo (gratuit jusqu'à 300 emails/jour)
- Landing page statique (je la génère)
- 2-3 posts réseaux pour amorcer les 100 premiers abonnés

**Revenus :**
- Premium 5-10€/mois (freemium)
- Sponsoring à partir de 1000 abonnés : 100-500€/mention

**Réaliste :**
- 0-6 mois : 0€
- 1000 abonnés → premiers sponsors
- 5000 abonnés → 500-2000€/mois

**Obstacles :**
- Sans promotion active, la liste ne grandit pas seule
- Tony doit promouvoir pendant 6 mois minimum

---

## Piste 3 : Ebooks techniques one-shot ⭐ PRIORITÉ 1

**Ce que je fais :**
- Guide complet 50-80 pages en Markdown
- Conversion PDF via `pandoc` dans GitHub Actions
- Landing page HTML statique avec pitch + bouton Stripe
- Push automatique sur GitHub Pages/Netlify
- 1 nouveau guide par semaine possible

**Tony fait une fois :**
- Créer compte Stripe
- Webhook "paiement → email PDF" (Zapier ou script Node — je le code)
- Déployer landing page (5 minutes)

**Revenus :**
- Vente directe 9-29€ pièce
- Pas de support, pas d'abonnement — achat + téléchargement

**Réaliste :**
- 3-6 mois pour trafic organique
- 1 guide → 2-10 ventes/mois passif
- 10 guides → 100-300€/mois réaliste
- Niches fortes : Angular avancé, TypeScript strict, migrations micro-frontends, DevOps CI/CD

**Obstacles :**
- Amener du trafic sans promotion = long
- Qualité perçue des guides AI = bas de gamme. Solution : sujets très spécifiques, exemples réels.

**Prochaine étape concrète :**
1. Choisir le premier sujet (je propose : "Migration Angular vers Micro-frontends avec Module Federation — Guide complet 2026")
2. Je génère le guide en Markdown (1-2 runs)
3. Je code le pipeline pandoc + landing page + intégration Stripe (1 run)
4. Tony valide la qualité et pose Stripe
5. Go live

---

## Piste 4 : Contenu réseaux sociaux (funnel)

**Ce que je fais :**
- 3-5 posts/jour dans `social/YYYY-MM-DD.md`
- Autoposter via Buffer/Publer API si configuré

**Tony fait une fois :**
- Comptes plateformes + Buffer
- Définir ligne éditoriale

**Revenus :**
- Pas directement. Funnel vers ebooks ou newsletter.
- Sponsored posts à 5-10k followers.

**Verdict : ne pas faire seul.** En support des autres pistes uniquement.

---

## Plan d'action

**Semaine 1 :** Premier ebook technique, pipeline complet, landing page
**Semaine 2-3 :** Site SEO autour des guides (1 article/jour)
**Mois 2 :** Newsletter si des guides se vendent

## Limite structurelle

Je produis. Je ne distribue pas. La promotion, c'est Tony ou rien pendant les 6 premiers mois. Après, le SEO organique prend le relais si le contenu est bon.
