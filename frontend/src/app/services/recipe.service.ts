import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Recipe } from '../models/recipe.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class RecipeService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  searchRecipes(ingredients: string[]): Observable<Recipe[]> {
    return this.http
      .post<{ recipes: Recipe[] }>(`${this.apiUrl}/api/recipes/search`, { ingredients })
      .pipe(map(res => res.recipes));
  }
}
