export interface Recipe {
  id: string;
  title: string;
  image: string;
  source: 'spoonacular' | 'edamam' | 'tiktok' | 'instagram';
  sourceUrl: string;
  cookingMethod: 'stovetop' | 'oven' | 'airfryer' | 'other';
  totalTime: number;
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
  timerMinutes: number | null;
}
