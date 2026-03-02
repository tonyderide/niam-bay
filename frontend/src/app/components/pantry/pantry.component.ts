import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StorageService } from '../../services/storage.service';

@Component({
  selector: 'app-pantry',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './pantry.component.html',
  styleUrl: './pantry.component.scss'
})
export class PantryComponent implements OnInit {
  @Output() searchRecipes = new EventEmitter<string[]>();

  pantryItems: string[] = [];
  fridgeItems: string[] = [];
  pantryInput = '';
  fridgeInput = '';

  commonIngredients = [
    'sel', 'poivre', 'huile d\'olive', 'farine', 'sucre', 'beurre',
    'ail', 'oignon', 'lait', 'oeufs', 'riz', 'pâtes',
    'sauce soja', 'vinaigre', 'moutarde', 'crème fraîche',
    'tomates en conserve', 'bouillon cube', 'herbes de Provence', 'curry',
    'paprika', 'cumin', 'gingembre', 'citron'
  ];

  filteredSuggestions: string[] = [];
  activeSuggestionTarget: 'pantry' | 'fridge' | null = null;

  constructor(private storage: StorageService) {}

  ngOnInit(): void {
    this.pantryItems = this.storage.getPantry();
    this.fridgeItems = this.storage.getFridge();
  }

  onPantryInputChange(): void {
    this.activeSuggestionTarget = 'pantry';
    this.filterSuggestions(this.pantryInput, this.pantryItems);
  }

  onFridgeInputChange(): void {
    this.activeSuggestionTarget = 'fridge';
    this.filterSuggestions(this.fridgeInput, this.fridgeItems);
  }

  private filterSuggestions(input: string, existing: string[]): void {
    if (input.length < 1) {
      this.filteredSuggestions = [];
      return;
    }
    const lower = input.toLowerCase();
    this.filteredSuggestions = this.commonIngredients
      .filter(item => item.toLowerCase().includes(lower) && !existing.includes(item))
      .slice(0, 5);
  }

  selectSuggestion(item: string): void {
    if (this.activeSuggestionTarget === 'pantry') {
      this.addToPantry(item);
      this.pantryInput = '';
    } else {
      this.addToFridge(item);
      this.fridgeInput = '';
    }
    this.filteredSuggestions = [];
    this.activeSuggestionTarget = null;
  }

  addToPantry(item?: string): void {
    const value = (item || this.pantryInput).trim().toLowerCase();
    if (value && !this.pantryItems.includes(value)) {
      this.pantryItems.push(value);
      this.storage.savePantry(this.pantryItems);
    }
    this.pantryInput = '';
    this.filteredSuggestions = [];
  }

  addToFridge(item?: string): void {
    const value = (item || this.fridgeInput).trim().toLowerCase();
    if (value && !this.fridgeItems.includes(value)) {
      this.fridgeItems.push(value);
      this.storage.saveFridge(this.fridgeItems);
    }
    this.fridgeInput = '';
    this.filteredSuggestions = [];
  }

  removePantryItem(index: number): void {
    this.pantryItems.splice(index, 1);
    this.storage.savePantry(this.pantryItems);
  }

  removeFridgeItem(index: number): void {
    this.fridgeItems.splice(index, 1);
    this.storage.saveFridge(this.fridgeItems);
  }

  onSearch(): void {
    const allIngredients = [...this.pantryItems, ...this.fridgeItems];
    if (allIngredients.length > 0) {
      this.searchRecipes.emit(allIngredients);
    }
  }

  onPantryKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.addToPantry();
    }
  }

  onFridgeKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.addToFridge();
    }
  }
}
