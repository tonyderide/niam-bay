import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { Dashboard } from '../../models/dashboard.model';
import { BotConfig } from '../../models/config.model';
import { KrakenPosition } from '../../models/position.model';
import { OpenOrder } from '../../models/open-order.model';
import { SparklineComponent } from '../sparkline/sparkline.component';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, SparklineComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, OnDestroy {
  instruments = ['PF_XBTUSD', 'PF_ETHUSD'];
  dashboards: Map<string, Dashboard> = new Map();
  configs: BotConfig[] = [];
  positions: KrakenPosition[] = [];
  openOrders: OpenOrder[] = [];
  priceHistories: Map<string, number[]> = new Map();
  private previousPrices: Map<string, number> = new Map();
  private pollSub?: Subscription;
  private sseSubs: Map<string, Subscription> = new Map();

  loadingAction: Map<string, string> = new Map();
  flashState: Map<string, string> = new Map();

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadConfigs();
    this.loadPositions();
    this.loadOpenOrders();
    this.loadPriceHistories();
    this.instruments.forEach(instrument => this.connectSse(instrument));
    this.pollSub = interval(5000).subscribe(() => this.loadData());
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
    this.sseSubs.forEach(sub => sub.unsubscribe());
    this.sseSubs.clear();
  }

  private connectSse(instrument: string): void {
    const sub = this.api.streamDashboard(instrument).subscribe({
      next: (dashboard) => {
        const prev = this.dashboards.get(instrument);
        if (prev?.currentPrice != null) {
          this.previousPrices.set(instrument, prev.currentPrice);
        }
        this.dashboards.set(instrument, dashboard);
      },
      error: () => {}
    });
    this.sseSubs.set(instrument, sub);
  }

  loadConfigs(): void {
    this.api.getConfigs().subscribe(configs => this.configs = configs);
  }

  loadPositions(): void {
    this.api.getOpenPositions().subscribe({
      next: (pos) => this.positions = pos,
      error: () => this.positions = []
    });
  }

  loadPriceHistories(): void {
    this.instruments.forEach(instrument => {
      this.api.getPriceHistory(instrument, 100).subscribe({
        next: (prices) => this.priceHistories.set(instrument, prices),
        error: () => {}
      });
    });
  }

  getPosition(instrument: string): KrakenPosition | undefined {
    return this.positions.find(p => p.symbol === instrument);
  }

  getPriceHistory(instrument: string): number[] {
    return this.priceHistories.get(instrument) || [];
  }

  loadOpenOrders(): void {
    this.api.getOpenOrders().subscribe({
      next: (orders) => this.openOrders = orders,
      error: () => this.openOrders = []
    });
  }

  getOrders(instrument: string): OpenOrder[] {
    return this.openOrders.filter(o => o.symbol === instrument);
  }

  getOrderTypeLabel(orderType: string): string {
    if (orderType === 'take_profit') return 'TAKE PROFIT';
    if (orderType === 'stop' || orderType === 'stp') return 'STOP LOSS';
    return orderType.toUpperCase();
  }

  loadData(): void {
    this.loadConfigs();
    this.loadPositions();
    this.loadOpenOrders();
    this.loadPriceHistories();
    this.instruments.forEach(instrument => {
      this.api.getDashboard(instrument).subscribe({
        next: (d) => this.dashboards.set(instrument, d),
        error: () => {}
      });
    });
  }

  getDashboard(instrument: string): Dashboard | undefined {
    return this.dashboards.get(instrument);
  }

  getConfigId(instrument: string): number | undefined {
    const config = this.configs.find(c => c.instrument === instrument);
    return config?.id;
  }

  stopBot(instrument: string): void {
    this.loadingAction.set(instrument, 'stop');
    this.api.stopBot(instrument).subscribe({
      next: () => {
        this.triggerFlash(instrument, 'error');
        this.loadData();
      },
      error: () => {
        this.triggerFlash(instrument, 'error');
        this.loadingAction.delete(instrument);
      }
    });
  }

  forceDirection(instrument: string, direction: string): void {
    const configId = this.getConfigId(instrument);
    if (configId) {
      this.loadingAction.set(instrument, 'force');
      this.api.forceDirection(configId, direction).subscribe({
        next: () => {
          this.triggerFlash(instrument, 'success');
          this.loadData();
        },
        error: () => {
          this.triggerFlash(instrument, 'error');
          this.loadingAction.delete(instrument);
        }
      });
    }
  }

  startBot(instrument: string): void {
    const configId = this.getConfigId(instrument);
    if (configId) {
      this.loadingAction.set(instrument, 'start');
      this.api.startBot(configId).subscribe({
        next: () => {
          this.triggerFlash(instrument, 'success');
          this.loadData();
        },
        error: () => {
          this.triggerFlash(instrument, 'error');
          this.loadingAction.delete(instrument);
        }
      });
    }
  }

  quickStart(instrument: string): void {
    const existing = this.configs.find(c => c.instrument === instrument);
    this.loadingAction.set(instrument, 'auto');
    if (existing?.id) {
      this.api.startBot(existing.id).subscribe({
        next: () => {
          this.triggerFlash(instrument, 'success');
          this.loadData();
        },
        error: () => {
          this.triggerFlash(instrument, 'error');
          this.loadingAction.delete(instrument);
        }
      });
    } else {
      const config: BotConfig = {
        instrument,
        initialStake: 5,
        maxDoublings: 3,
        takeProfitPct: 1.5,
        stopLossPct: 1.0,
        leverage: 2,
        signalStrategy: 'RSI_EMA',
        active: true
      };
      this.api.saveConfig(config).subscribe(saved => {
        this.loadConfigs();
        if (saved.id) {
          this.api.startBot(saved.id).subscribe({
            next: () => {
              this.triggerFlash(instrument, 'success');
              this.loadData();
            },
            error: () => {
              this.triggerFlash(instrument, 'error');
              this.loadingAction.delete(instrument);
            }
          });
        }
      });
    }
  }

  private triggerFlash(instrument: string, state: string): void {
    this.flashState.set(instrument, state);
    this.loadingAction.delete(instrument);
    setTimeout(() => this.flashState.delete(instrument), 600);
  }

  isPriceUp(instrument: string): boolean {
    const dash = this.dashboards.get(instrument);
    const prev = this.previousPrices.get(instrument);
    if (!dash?.currentPrice || prev == null) return true;
    return dash.currentPrice >= prev;
  }

  getProgressPercent(dash: Dashboard): number {
    if (!dash.currentPrice || !dash.stopLossPrice || !dash.takeProfitPrice) return 50;
    const range = dash.takeProfitPrice - dash.stopLossPrice;
    if (range === 0) return 50;
    const progress = (dash.currentPrice - dash.stopLossPrice) / range * 100;
    return Math.max(0, Math.min(100, progress));
  }
}
