# NiamBay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a recipe suggestion web app that finds recipes based on fridge/pantry contents, with glass morphism UI, cooking timers, and calorie tracking.

**Architecture:** Angular 19 SPA frontend communicating with a Node.js/Express API backend. Backend aggregates recipes from Spoonacular, Edamam, and social media scraping. LocalStorage for user data persistence. Docker Compose for deployment.

**Tech Stack:** Angular 19 (standalone), Node.js 20, Express, Axios, Cheerio, SCSS, Angular Material, Docker

---

### Task 1: Project scaffolding and Node.js setup

**Files:**
- Create: `backend/package.json`
- Create: `backend/tsconfig.json`
- Create: `backend/src/index.ts`
- Create: `backend/.env.example`

**Step 1: Switch to Node 20 and init backend**

```bash
cd /home/tony/projet/niam-bay
nvm use 20
mkdir -p backend
cd backend
npm init -y
npm install express cors dotenv axios cheerio
npm install -D typescript @types/express @types/cors @types/node ts-node nodemon
```

**Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"]
}
```

**Step 3: Create backend/src/index.ts**

```typescript
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`NiamBay API running on port ${PORT}`);
});
```

**Step 4: Create backend/.env.example**

```
PORT=3000
SPOONACULAR_API_KEY=your_key_here
EDAMAM_APP_ID=your_app_id_here
EDAMAM_APP_KEY=your_key_here
```

**Step 5: Add scripts to package.json**

Add to scripts:
```json
{
  "dev": "nodemon --exec ts-node src/index.ts",
  "build": "tsc",
  "start": "node dist/index.js"
}
```

**Step 6: Test that backend starts**

```bash
cp .env.example .env
npm run dev
# Expected: "NiamBay API running on port 3000"
# Ctrl+C to stop
```

**Step 7: Commit**

```bash
cd /home/tony/projet/niam-bay
git init
git add backend/
git commit -m "feat: scaffold backend with Express + TypeScript"
```

---

### Task 2: Angular frontend scaffolding

**Files:**
- Create: `frontend/` (Angular CLI generated)

**Step 1: Install Angular CLI and create project**

```bash
cd /home/tony/projet/niam-bay
nvm use 20
npx @angular/cli@19 new frontend --style=scss --routing=false --ssr=false --standalone
```

**Step 2: Add Angular Material**

```bash
cd frontend
npx ng add @angular/material --theme=custom --animations=enabled --typography=true
```

**Step 3: Verify it runs**

```bash
npx ng serve
# Expected: Angular app on http://localhost:4200
# Ctrl+C to stop
```

**Step 4: Add proxy config for backend**

Create `frontend/proxy.conf.json`:
```json
{
  "/api": {
    "target": "http://localhost:3000",
    "secure": false
  }
}
```

Update `angular.json` serve options to add `"proxyConfig": "proxy.conf.json"`.

**Step 5: Commit**

```bash
cd /home/tony/projet/niam-bay
git add frontend/
git commit -m "feat: scaffold Angular 19 frontend with Material"
```

---

### Task 3: Backend - Spoonacular recipe service

**Files:**
- Create: `backend/src/services/spoonacular.service.ts`
- Create: `backend/src/routes/recipes.routes.ts`
- Create: `backend/src/types/recipe.ts`

**Step 1: Define shared recipe types in backend/src/types/recipe.ts**

```typescript
export interface Recipe {
  id: string;
  title: string;
  image: string;
  source: 'spoonacular' | 'edamam' | 'tiktok' | 'instagram';
  sourceUrl: string;
  cookingMethod: 'stovetop' | 'oven' | 'airfryer' | 'other';
  totalTime: number; // minutes
  servings: number;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  cuisineType: string;
  ingredients: Ingredient[];
  steps: RecipeStep[];
}

export interface Ingredient {
  name: string;
  amount: number;
  unit: string;
}

export interface RecipeStep {
  number: number;
  description: string;
  timerMinutes: number | null; // null = no timer needed
}
```

**Step 2: Create backend/src/services/spoonacular.service.ts**

```typescript
import axios from 'axios';
import { Recipe, RecipeStep } from '../types/recipe';

const BASE_URL = 'https://api.spoonacular.com';

function detectCookingMethod(instructions: string): Recipe['cookingMethod'] {
  const lower = instructions.toLowerCase();
  if (lower.includes('air fryer') || lower.includes('airfryer')) return 'airfryer';
  if (lower.includes('oven') || lower.includes('bake') || lower.includes('roast') || lower.includes('four')) return 'oven';
  if (lower.includes('pan') || lower.includes('skillet') || lower.includes('poêle') || lower.includes('casserole') || lower.includes('sauté') || lower.includes('boil') || lower.includes('simmer')) return 'stovetop';
  return 'other';
}

function extractTimerFromStep(step: string): number | null {
  const match = step.match(/(\d+)\s*(minutes?|mins?|hours?|hrs?)/i);
  if (!match) return null;
  const value = parseInt(match[1]);
  if (match[2].startsWith('h')) return value * 60;
  return value;
}

export async function searchByIngredients(ingredients: string[]): Promise<Recipe[]> {
  const apiKey = process.env.SPOONACULAR_API_KEY;
  if (!apiKey) return [];

  const { data: results } = await axios.get(`${BASE_URL}/recipes/findByIngredients`, {
    params: {
      apiKey,
      ingredients: ingredients.join(','),
      number: 10,
      ranking: 1,
      ignorePantry: true,
    },
  });

  const recipes: Recipe[] = [];

  for (const result of results) {
    try {
      const { data: detail } = await axios.get(`${BASE_URL}/recipes/${result.id}/information`, {
        params: { apiKey, includeNutrition: true },
      });

      const allInstructions = (detail.analyzedInstructions?.[0]?.steps || [])
        .map((s: any) => s.step)
        .join(' ');

      const steps: RecipeStep[] = (detail.analyzedInstructions?.[0]?.steps || []).map((s: any) => ({
        number: s.number,
        description: s.step,
        timerMinutes: extractTimerFromStep(s.step),
      }));

      const nutrients = detail.nutrition?.nutrients || [];
      const findNutrient = (name: string) => nutrients.find((n: any) => n.name === name)?.amount || 0;

      recipes.push({
        id: `spoonacular-${detail.id}`,
        title: detail.title,
        image: detail.image,
        source: 'spoonacular',
        sourceUrl: detail.sourceUrl || detail.spoonacularSourceUrl,
        cookingMethod: detectCookingMethod(allInstructions),
        totalTime: detail.readyInMinutes || 0,
        servings: detail.servings || 1,
        calories: Math.round(findNutrient('Calories')),
        protein: Math.round(findNutrient('Protein')),
        carbs: Math.round(findNutrient('Carbohydrates')),
        fat: Math.round(findNutrient('Fat')),
        cuisineType: detail.cuisines?.[0] || 'International',
        ingredients: (detail.extendedIngredients || []).map((i: any) => ({
          name: i.name,
          amount: i.amount,
          unit: i.unit,
        })),
        steps,
      });
    } catch {
      // Skip recipes that fail to load details
    }
  }

  return recipes;
}
```

**Step 3: Create backend/src/routes/recipes.routes.ts**

```typescript
import { Router, Request, Response } from 'express';
import { searchByIngredients as spoonacularSearch } from '../services/spoonacular.service';

const router = Router();

router.post('/search', async (req: Request, res: Response) => {
  const { ingredients } = req.body;

  if (!ingredients || !Array.isArray(ingredients) || ingredients.length === 0) {
    res.status(400).json({ error: 'ingredients array required' });
    return;
  }

  try {
    const recipes = await spoonacularSearch(ingredients);
    res.json({ recipes });
  } catch (error) {
    console.error('Recipe search error:', error);
    res.status(500).json({ error: 'Failed to search recipes' });
  }
});

export default router;
```

**Step 4: Wire routes into index.ts**

Add to `backend/src/index.ts`:
```typescript
import recipesRoutes from './routes/recipes.routes';
app.use('/api/recipes', recipesRoutes);
```

**Step 5: Test manually**

```bash
cd /home/tony/projet/niam-bay/backend
npm run dev &
curl -X POST http://localhost:3000/api/recipes/search \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["chicken", "rice", "garlic"]}'
# Expected: JSON with recipes array (empty if no API key set, populated if key is valid)
kill %1
```

**Step 6: Commit**

```bash
cd /home/tony/projet/niam-bay
git add backend/
git commit -m "feat: add Spoonacular recipe search service"
```

---

### Task 4: Backend - Edamam recipe service

**Files:**
- Create: `backend/src/services/edamam.service.ts`
- Modify: `backend/src/routes/recipes.routes.ts`

**Step 1: Create backend/src/services/edamam.service.ts**

```typescript
import axios from 'axios';
import { Recipe, RecipeStep } from '../types/recipe';

const BASE_URL = 'https://api.edamam.com/api/recipes/v2';

function detectCookingMethod(labels: string[], instructions: string): Recipe['cookingMethod'] {
  const combined = [...labels, instructions].join(' ').toLowerCase();
  if (combined.includes('air fr')) return 'airfryer';
  if (combined.includes('oven') || combined.includes('bak') || combined.includes('roast')) return 'oven';
  return 'stovetop';
}

function parseStepsFromText(text: string): RecipeStep[] {
  if (!text) return [{ number: 1, description: 'See original recipe for instructions', timerMinutes: null }];
  const lines = text.split(/\n|\.(?=\s)/).filter(l => l.trim().length > 10);
  return lines.map((line, i) => {
    const timerMatch = line.match(/(\d+)\s*(minutes?|mins?|hours?|hrs?)/i);
    let timer: number | null = null;
    if (timerMatch) {
      timer = parseInt(timerMatch[1]);
      if (timerMatch[2].startsWith('h')) timer *= 60;
    }
    return { number: i + 1, description: line.trim(), timerMinutes: timer };
  });
}

export async function searchByIngredients(ingredients: string[]): Promise<Recipe[]> {
  const appId = process.env.EDAMAM_APP_ID;
  const appKey = process.env.EDAMAM_APP_KEY;
  if (!appId || !appKey) return [];

  try {
    const { data } = await axios.get(BASE_URL, {
      params: {
        type: 'public',
        q: ingredients.join(' '),
        app_id: appId,
        app_key: appKey,
        from: 0,
        to: 10,
      },
    });

    return (data.hits || []).map((hit: any) => {
      const r = hit.recipe;
      const nutrients = r.totalNutrients || {};
      const servings = r.yield || 1;

      return {
        id: `edamam-${encodeURIComponent(r.uri)}`,
        title: r.label,
        image: r.image,
        source: 'edamam' as const,
        sourceUrl: r.url,
        cookingMethod: detectCookingMethod(r.dishType || [], r.label),
        totalTime: r.totalTime || 0,
        servings,
        calories: Math.round((r.calories || 0) / servings),
        protein: Math.round((nutrients.PROCNT?.quantity || 0) / servings),
        carbs: Math.round((nutrients.CHOCDF?.quantity || 0) / servings),
        fat: Math.round((nutrients.FAT?.quantity || 0) / servings),
        cuisineType: r.cuisineType?.[0] || 'International',
        ingredients: (r.ingredientLines || []).map((line: string, i: number) => ({
          name: line,
          amount: 0,
          unit: '',
        })),
        steps: parseStepsFromText(''),
      };
    });
  } catch (error) {
    console.error('Edamam search error:', error);
    return [];
  }
}
```

**Step 2: Update recipes.routes.ts to aggregate both sources**

```typescript
import { searchByIngredients as edamamSearch } from '../services/edamam.service';

// In the /search handler, add:
const [spoonacularResults, edamamResults] = await Promise.all([
  spoonacularSearch(ingredients),
  edamamSearch(ingredients),
]);
const recipes = [...spoonacularResults, ...edamamResults];
res.json({ recipes });
```

**Step 3: Test and commit**

```bash
cd /home/tony/projet/niam-bay
git add backend/
git commit -m "feat: add Edamam recipe service and aggregate results"
```

---

### Task 5: Backend - Social media scraping (TikTok/Instagram)

**Files:**
- Create: `backend/src/services/social-scraper.service.ts`
- Modify: `backend/src/routes/recipes.routes.ts`

**Step 1: Create backend/src/services/social-scraper.service.ts**

```typescript
import axios from 'axios';
import * as cheerio from 'cheerio';
import { Recipe, RecipeStep } from '../types/recipe';

function extractTimerFromStep(step: string): number | null {
  const match = step.match(/(\d+)\s*(minutes?|mins?|hours?|hrs?|min)/i);
  if (!match) return null;
  const value = parseInt(match[1]);
  if (match[2].startsWith('h')) return value * 60;
  return value;
}

export async function searchTikTok(ingredients: string[]): Promise<Recipe[]> {
  try {
    const query = encodeURIComponent(`recipe ${ingredients.slice(0, 3).join(' ')}`);
    const { data } = await axios.get(`https://www.tiktok.com/api/search/general/full/?keyword=${query}&search_id=0`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
      timeout: 5000,
    });

    // TikTok API responses are unstable - best effort parsing
    const items = data?.data || [];
    return items.slice(0, 5).map((item: any, idx: number) => ({
      id: `tiktok-${item.id || idx}`,
      title: item.desc || `TikTok recipe ${idx + 1}`,
      image: item.video?.cover || '',
      source: 'tiktok' as const,
      sourceUrl: `https://www.tiktok.com/@${item.author?.uniqueId}/video/${item.id}`,
      cookingMethod: 'other' as const,
      totalTime: 0,
      servings: 1,
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0,
      cuisineType: 'International',
      ingredients: ingredients.map(i => ({ name: i, amount: 0, unit: '' })),
      steps: [{ number: 1, description: 'Watch the video for full instructions', timerMinutes: null }],
    }));
  } catch {
    return [];
  }
}

export async function searchInstagram(ingredients: string[]): Promise<Recipe[]> {
  try {
    const query = encodeURIComponent(`${ingredients.slice(0, 2).join('')}recipe`);
    const { data } = await axios.get(`https://www.instagram.com/explore/tags/${query}/`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
      timeout: 5000,
    });

    const $ = cheerio.load(data);
    // Instagram structure changes frequently - best effort
    const scriptData = $('script[type="application/ld+json"]').text();
    if (!scriptData) return [];

    return [];
  } catch {
    return [];
  }
}

export async function searchSocial(ingredients: string[]): Promise<Recipe[]> {
  const [tiktok, instagram] = await Promise.allSettled([
    searchTikTok(ingredients),
    searchInstagram(ingredients),
  ]);

  return [
    ...(tiktok.status === 'fulfilled' ? tiktok.value : []),
    ...(instagram.status === 'fulfilled' ? instagram.value : []),
  ];
}
```

**Step 2: Add social scraper to recipe routes aggregation**

Add to imports and Promise.all in recipes.routes.ts:
```typescript
import { searchSocial } from '../services/social-scraper.service';

// Update the handler:
const [spoonacularResults, edamamResults, socialResults] = await Promise.all([
  spoonacularSearch(ingredients),
  edamamSearch(ingredients),
  searchSocial(ingredients),
]);
const recipes = [...spoonacularResults, ...edamamResults, ...socialResults];
```

**Step 3: Commit**

```bash
cd /home/tony/projet/niam-bay
git add backend/
git commit -m "feat: add social media recipe scraping (TikTok/Instagram)"
```

---

### Task 6: Angular - Glass morphism theme and layout

**Files:**
- Modify: `frontend/src/styles.scss`
- Modify: `frontend/src/app/app.component.ts`
- Modify: `frontend/src/app/app.component.scss`
- Modify: `frontend/src/app/app.component.html`

**Step 1: Set up global glass morphism styles in styles.scss**

```scss
@use '@angular/material' as mat;

:root {
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-border: rgba(255, 255, 255, 0.2);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  --glass-blur: blur(20px);
  --accent: #ff6b35;
  --accent-light: #ff8c5a;
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --bg-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-gradient);
  min-height: 100vh;
  color: var(--text-primary);
  overflow-x: hidden;
}

.glass-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  box-shadow: var(--glass-shadow);
  padding: 24px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  }
}

.glass-button {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: var(--glass-blur);

  &:hover {
    background: var(--accent-light);
    transform: scale(1.02);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.glass-input {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  padding: 12px 16px;
  color: var(--text-primary);
  font-size: 16px;
  width: 100%;
  outline: none;
  transition: border-color 0.3s;

  &::placeholder {
    color: var(--text-secondary);
  }

  &:focus {
    border-color: var(--accent);
  }
}

.glass-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: default;

  .remove-btn {
    cursor: pointer;
    opacity: 0.7;
    &:hover { opacity: 1; }
  }
}
```

**Step 2: Create the main layout in app.component.html**

```html
<div class="app-container">
  <header class="glass-card app-header">
    <h1>NiamBay</h1>
    <p>Des recettes du monde entier avec ce que tu as dans ton frigo</p>
  </header>

  <main>
    <app-pantry (searchRecipes)="onSearch($event)"></app-pantry>
    <app-recipe-results
      [recipes]="recipes"
      [loading]="loading"
      (openRecipe)="onOpenRecipe($event)">
    </app-recipe-results>
  </main>

  <app-recipe-detail
    *ngIf="selectedRecipe"
    [recipe]="selectedRecipe"
    (close)="selectedRecipe = null">
  </app-recipe-detail>
</div>
```

**Step 3: Style app.component.scss**

```scss
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
}

.app-header {
  text-align: center;
  margin-bottom: 32px;

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent), #ffd700);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }

  p {
    color: var(--text-secondary);
    font-size: 1.1rem;
  }
}
```

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: glass morphism theme and app layout"
```

---

### Task 7: Angular - Pantry/Fridge component

**Files:**
- Create: `frontend/src/app/components/pantry/pantry.component.ts`
- Create: `frontend/src/app/components/pantry/pantry.component.html`
- Create: `frontend/src/app/components/pantry/pantry.component.scss`
- Create: `frontend/src/app/services/storage.service.ts`

**Step 1: Create storage service**

```typescript
// frontend/src/app/services/storage.service.ts
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class StorageService {
  private PANTRY_KEY = 'niambay_pantry';
  private FRIDGE_KEY = 'niambay_fridge';

  getPantry(): string[] {
    return JSON.parse(localStorage.getItem(this.PANTRY_KEY) || '[]');
  }

  savePantry(items: string[]): void {
    localStorage.setItem(this.PANTRY_KEY, JSON.stringify(items));
  }

  getFridge(): string[] {
    return JSON.parse(localStorage.getItem(this.FRIDGE_KEY) || '[]');
  }

  saveFridge(items: string[]): void {
    localStorage.setItem(this.FRIDGE_KEY, JSON.stringify(items));
  }
}
```

**Step 2: Create pantry component with two zones (placard persistent, frigo session)**

Template shows two glass-card zones side by side, each with an input + chip list. A big "Trouver des recettes" button at the bottom combines both lists and emits the search event.

Common ingredients autocomplete list built-in: sel, poivre, huile d'olive, farine, sucre, beurre, ail, oignon, etc.

**Step 3: Commit**

```bash
git add frontend/
git commit -m "feat: pantry/fridge component with localStorage persistence"
```

---

### Task 8: Angular - Recipe service and results component

**Files:**
- Create: `frontend/src/app/services/recipe.service.ts`
- Create: `frontend/src/app/models/recipe.model.ts`
- Create: `frontend/src/app/components/recipe-results/recipe-results.component.ts`
- Create: `frontend/src/app/components/recipe-results/recipe-results.component.html`
- Create: `frontend/src/app/components/recipe-results/recipe-results.component.scss`

**Step 1: Create recipe model (mirrors backend types)**

**Step 2: Create recipe service that calls POST /api/recipes/search**

**Step 3: Create recipe-results component with 3 tabs**

- Tab 1: Plaque (stovetop) - casserole/poêle icon
- Tab 2: Four (oven) - oven icon
- Tab 3: Air Fryer - air fryer icon

Each tab shows a grid of glass-card recipe cards filtered by cookingMethod. Cards show: image, title, calories badge, time badge, cuisine tag, source tag.

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: recipe service and results component with cooking method tabs"
```

---

### Task 9: Angular - Recipe detail modal with steps and timers

**Files:**
- Create: `frontend/src/app/components/recipe-detail/recipe-detail.component.ts`
- Create: `frontend/src/app/components/recipe-detail/recipe-detail.component.html`
- Create: `frontend/src/app/components/recipe-detail/recipe-detail.component.scss`
- Create: `frontend/src/app/services/timer.service.ts`

**Step 1: Create timer service**

Simple countdown service using `setInterval`. Emits ticks, plays a sound (Web Audio API beep) when reaching 0.

**Step 2: Create recipe-detail component**

Glass morphism modal overlay with:
- Recipe title, image, source link
- Nutrition bar: calories, protein, carbs, fat
- Ingredient list
- Steps list:
  - Each step has number, description, timer button (if timerMinutes !== null)
  - Click on step checkbox → greyed out + strikethrough, auto-scroll to next
  - Active step highlighted with accent border
  - Countdown timer inline with mm:ss display, start/pause/reset controls
  - Sound notification when timer ends
- Close button

**Step 3: Commit**

```bash
git add frontend/
git commit -m "feat: recipe detail modal with step tracking and cooking timers"
```

---

### Task 10: Wire everything together in app.component

**Files:**
- Modify: `frontend/src/app/app.component.ts`

**Step 1: Import all components, wire up the search flow**

- On search: call RecipeService, set loading state, populate recipes array
- On openRecipe: set selectedRecipe
- On close: clear selectedRecipe

**Step 2: Test full flow end-to-end**

```bash
# Terminal 1: Backend
cd /home/tony/projet/niam-bay/backend && npm run dev

# Terminal 2: Frontend
cd /home/tony/projet/niam-bay/frontend && npx ng serve --proxy-config proxy.conf.json
```

Open http://localhost:4200, add ingredients, search, verify results show in tabs, open a recipe, test step tracking and timers.

**Step 3: Commit**

```bash
git add .
git commit -m "feat: wire up full recipe search flow end-to-end"
```

---

### Task 11: Docker setup

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `frontend/nginx.conf`

**Step 1: Create backend Dockerfile**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Step 2: Create frontend Dockerfile**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx ng build --configuration=production

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
EXPOSE 80
```

**Step 3: Create nginx.conf with /api proxy to backend**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api {
        proxy_pass http://backend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Step 4: Create docker-compose.yml**

```yaml
services:
  backend:
    build: ./backend
    env_file: ./backend/.env
    ports:
      - "3000:3000"

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend
```

**Step 5: Test docker build and run**

```bash
cd /home/tony/projet/niam-bay
docker compose up --build
# Expected: App accessible at http://localhost:8080
```

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add Docker setup with nginx and docker-compose"
```

---

### Task 12: Final polish and README

**Files:**
- Create: `.gitignore`

**Step 1: Create .gitignore**

```
node_modules/
dist/
.env
.angular/
```

**Step 2: Final test of the complete application**

Run docker compose, test the full flow, verify glass morphism looks right, timers work, steps grey out.

**Step 3: Final commit**

```bash
git add .
git commit -m "chore: add gitignore and finalize project"
```
