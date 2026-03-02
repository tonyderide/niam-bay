import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PantryComponent } from './components/pantry/pantry.component';
import { RecipeResultsComponent } from './components/recipe-results/recipe-results.component';
import { RecipeDetailComponent } from './components/recipe-detail/recipe-detail.component';
import { RecipeService } from './services/recipe.service';
import { Recipe } from './models/recipe.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, PantryComponent, RecipeResultsComponent, RecipeDetailComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  recipes: Recipe[] = [];
  loading = false;
  selectedRecipe: Recipe | null = null;

  constructor(private recipeService: RecipeService) {}

  onSearch(ingredients: string[]): void {
    this.loading = true;
    this.recipes = [];
    this.recipeService.searchRecipes(ingredients).subscribe({
      next: (recipes) => {
        this.recipes = recipes;
        this.loading = false;
      },
      error: (err) => {
        console.error('Search failed:', err);
        this.loading = false;
      }
    });
  }

  onOpenRecipe(recipe: Recipe): void {
    this.selectedRecipe = recipe;
  }

  onCloseRecipe(): void {
    this.selectedRecipe = null;
  }
}
