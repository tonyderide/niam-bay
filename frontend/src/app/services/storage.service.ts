import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class StorageService {
  private PANTRY_KEY = 'niambay_pantry';
  private FRIDGE_KEY = 'niambay_fridge';

  getPantry(): string[] {
    return JSON.parse(localStorage.getItem(this.PANTRY_KEY) || '[]');
  }

  savePantry(items: string[]): void {
    localStorage.setItem(this.PANTRY_KEY, JSON.stringify(items));
  }

  getFridge(): string[] {
    return JSON.parse(localStorage.getItem(this.FRIDGE_KEY) || '[]');
  }

  saveFridge(items: string[]): void {
    localStorage.setItem(this.FRIDGE_KEY, JSON.stringify(items));
  }
}
