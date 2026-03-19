import { Component } from '@angular/core';
import { PanelComponent } from './panel.component';

@Component({
  selector: 'app-panel-page',
  standalone: true,
  imports: [PanelComponent],
  template: `<app-panel />`,
  styles: `:host { display: block; width: 100vw; height: 100vh; background: transparent; }`
})
export class PanelPageComponent {}
