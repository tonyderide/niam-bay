import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ConfigComponent } from './components/config/config.component';
import { TradesComponent } from './components/trades/trades.component';
import { LogPanelComponent } from './components/log-panel/log-panel.component';
import { ScalpingComponent } from './components/scalping/scalping.component';
import { GridComponent } from './components/grid/grid.component';
import { AutoComponent } from './components/auto/auto.component';
import { ApiService } from './services/api.service';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, DashboardComponent, ConfigComponent, TradesComponent, LogPanelComponent, ScalpingComponent, GridComponent, AutoComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'MARTINBOT';
  activeTab: 'dashboard' | 'scalping' | 'grid' | 'auto' | 'trades' | 'config' = 'dashboard';
  instruments = ['PF_XBTUSD', 'PF_ETHUSD'];
  botStates: Map<string, string> = new Map();
  private subs: Subscription[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.pollBotStates();
    this.subs.push(
      interval(3000).subscribe(() => this.pollBotStates())
    );
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  private pollBotStates(): void {
    this.instruments.forEach(instrument => {
      this.api.getDashboard(instrument).subscribe({
        next: (d) => {
          if (d.botActive) {
            this.botStates.set(instrument, 'active');
          } else {
            this.botStates.set(instrument, 'stopped');
          }
        },
        error: () => this.botStates.set(instrument, 'stopped')
      });
    });
  }

  getBotState(instrument: string): string {
    return this.botStates.get(instrument) || 'stopped';
  }

  getShortName(instrument: string): string {
    return instrument.replace('PF_', '').replace('USD', '');
  }
}
