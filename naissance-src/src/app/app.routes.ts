import { Routes } from '@angular/router';
import { CircleComponent } from './circle/circle.component';
import { PanelPageComponent } from './panel/panel-page.component';

export const routes: Routes = [
  { path: '', component: CircleComponent },
  { path: 'panel', component: PanelPageComponent },
];
