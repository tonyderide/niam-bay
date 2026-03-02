import { Router, Request, Response } from 'express';
import { searchByIngredients as spoonacularSearch } from '../services/spoonacular.service';
import { searchByIngredients as edamamSearch } from '../services/edamam.service';

const router = Router();

router.post('/search', async (req: Request, res: Response) => {
  const { ingredients } = req.body;

  if (!ingredients || !Array.isArray(ingredients) || ingredients.length === 0) {
    res.status(400).json({ error: 'ingredients array required' });
    return;
  }

  try {
    const [spoonacularResults, edamamResults] = await Promise.all([
      spoonacularSearch(ingredients),
      edamamSearch(ingredients),
    ]);
    const recipes = [...spoonacularResults, ...edamamResults];
    res.json({ recipes });
  } catch (error) {
    console.error('Recipe search error:', error);
    res.status(500).json({ error: 'Failed to search recipes' });
  }
});

export default router;
