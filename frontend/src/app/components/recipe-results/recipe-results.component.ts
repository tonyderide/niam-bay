import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Recipe } from '../../models/recipe.model';

type CookingTab = 'stovetop' | 'oven' | 'airfryer';

@Component({
  selector: 'app-recipe-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './recipe-results.component.html',
  styleUrl: './recipe-results.component.scss'
})
export class RecipeResultsComponent {
  @Input() recipes: Recipe[] = [];
  @Input() loading = false;
  @Output() openRecipe = new EventEmitter<Recipe>();

  activeTab: CookingTab = 'stovetop';

  tabs: { key: CookingTab; label: string; icon: string }[] = [
    { key: 'stovetop', label: 'Plaque', icon: '🍳' },
    { key: 'oven', label: 'Four', icon: '🔥' },
    { key: 'airfryer', label: 'Air Fryer', icon: '🌀' },
  ];

  get filteredRecipes(): Recipe[] {
    return this.recipes.filter(r => r.cookingMethod === this.activeTab);
  }

  get otherRecipes(): Recipe[] {
    return this.recipes.filter(r => r.cookingMethod === 'other');
  }

  getCountForTab(key: CookingTab): number {
    return this.recipes.filter(r => r.cookingMethod === key).length;
  }

  setTab(tab: CookingTab): void {
    this.activeTab = tab;
  }

  onOpenRecipe(recipe: Recipe): void {
    this.openRecipe.emit(recipe);
  }

  getSourceBadge(source: string): string {
    const badges: Record<string, string> = {
      spoonacular: '🥄 Spoonacular',
      edamam: '🍏 Edamam',
      tiktok: '🎵 TikTok',
      instagram: '📷 Instagram',
    };
    return badges[source] || source;
  }
}
