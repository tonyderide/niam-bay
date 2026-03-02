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
