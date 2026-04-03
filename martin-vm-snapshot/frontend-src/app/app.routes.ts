import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ConfigComponent } from './components/config/config.component';
import { TradesComponent } from './components/trades/trades.component';

export const routes: Routes = [
  { path: 'dashboard', component: DashboardComponent },
  { path: 'config', component: ConfigComponent },
  { path: 'trades', component: TradesComponent },
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' }
];
