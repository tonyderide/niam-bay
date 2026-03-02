# NiamBay - Design Document

## Overview

Recipe suggestion app based on fridge/pantry contents. Single-page Angular frontend with glass morphism design, Node.js/Express backend aggregating recipes from Spoonacular, Edamam, and social media scraping.

## Architecture

```
Angular SPA (port 4200) → Node.js API (port 3000) → Spoonacular / Edamam / TikTok-Insta scraping
```

- Front: Angular 19 standalone, single page, glass morphism, LocalStorage for persistence
- Back: Node.js 20 + Express, proxy APIs + scraping
- Deploy: Docker Compose (nginx + node)

## UI Sections (single page)

### 1. Mon Frigo & Placard
- Placard (persistent LocalStorage): staples like salt, oil, flour
- Frigo (session): current ingredients, easy add/remove
- Autocomplete ingredient names
- "Trouver des recettes" button

### 2. Résultats par méthode de cuisson
- 3 tabs: Plaque (casserole/poêle), Four, Air Fryer
- Glass morphism recipe cards: photo, name, calories, time, cuisine origin, source
- Click opens recipe detail

### 3. Détail recette (modal/expansion)
- Numbered steps with:
  - Description, estimated time
  - Built-in countdown timer with sound notification when cooking time specified
  - Checkbox: click greys out step, auto-scrolls to next
- Nutrition: calories, protein, carbs, fat
- Link to original source

## Data Sources

| Source | Method | Data |
|--------|--------|------|
| Spoonacular | REST API (key) | Structured recipes, nutrition, worldwide |
| Edamam | REST API (key) | Detailed nutrition, cuisine filters |
| TikTok | Unofficial search scraping | Recipe videos, embed link |
| Instagram | Hashtag scraping | Recipe posts, link |

Social scraping is best-effort; APIs are the reliable fallback.

## Calorie Calculation
- Spoonacular/Edamam provide nutrition data directly
- Scraped recipes: estimate via Spoonacular Nutrition API based on detected ingredients
- Display: total calories + per serving

## Tech Stack
- Front: Angular 19, SCSS, Angular Material, CSS glass morphism animations
- Back: Node.js 20, Express, Axios, Cheerio
- Docker: Nginx (front) + Node (back), docker-compose
- No database: LocalStorage client-side only
