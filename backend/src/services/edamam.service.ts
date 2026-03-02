import axios from 'axios';
import { Recipe, RecipeStep } from '../types/recipe';

const BASE_URL = 'https://api.edamam.com/api/recipes/v2';

function detectCookingMethod(labels: string[], title: string): Recipe['cookingMethod'] {
  const combined = [...labels, title].join(' ').toLowerCase();
  if (combined.includes('air fr')) return 'airfryer';
  if (combined.includes('oven') || combined.includes('bak') || combined.includes('roast')) return 'oven';
  return 'stovetop';
}

export async function searchByIngredients(ingredients: string[]): Promise<Recipe[]> {
  const appId = process.env.EDAMAM_APP_ID;
  const appKey = process.env.EDAMAM_APP_KEY;
  if (!appId || !appKey || appId === 'your_app_id_here') return [];

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
        id: `edamam-${Buffer.from(r.uri).toString('base64').slice(0, 20)}`,
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
        ingredients: (r.ingredientLines || []).map((line: string) => ({
          name: line,
          amount: 0,
          unit: '',
        })),
        steps: [{ number: 1, description: 'See original recipe for full instructions', timerMinutes: null }],
      };
    });
  } catch (error) {
    console.error('Edamam search error:', error);
    return [];
  }
}
