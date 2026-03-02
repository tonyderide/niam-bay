import axios from 'axios';
import * as cheerio from 'cheerio';
import { Recipe } from '../types/recipe';

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
