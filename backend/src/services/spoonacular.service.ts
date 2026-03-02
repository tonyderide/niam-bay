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
  if (!apiKey || apiKey === 'your_key_here') return [];

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
