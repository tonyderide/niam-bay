import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Trade, TradeStats } from '../../models/trade.model';
import { createChart, IChartApi, ISeriesApi, AreaSeries, AreaData, Time } from 'lightweight-charts';

@Component({
  selector: 'app-trades',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './trades.component.html',
  styleUrl: './trades.component.scss'
})
export class TradesComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('equityChart') chartRef!: ElementRef;

  instruments = ['ALL', 'PF_XBTUSD', 'PF_ETHUSD'];
  selectedInstrument = 'ALL';
  statusFilter = 'ALL';
  directionFilter = 'ALL';
  allTrades: Trade[] = [];
  stats: TradeStats | null = null;
  syncing = false;
  syncMessage = '';

  private chart: IChartApi | null = null;
  private areaSeries: ISeriesApi<'Area'> | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadData();
  }

  ngAfterViewInit(): void {
    this.initChart();
  }

  ngOnDestroy(): void {
    this.chart?.remove();
  }

  onInstrumentChange(): void {
    this.loadData();
  }

  loadData(): void {
    if (this.selectedInstrument === 'ALL') {
      this.api.getAllTrades().subscribe({
        next: (trades) => {
          this.allTrades = trades.sort((a, b) =>
            new Date(b.closedAt || b.openedAt).getTime() - new Date(a.closedAt || a.openedAt).getTime()
          );
        },
        error: () => this.allTrades = []
      });
    } else {
      this.api.getTrades(this.selectedInstrument).subscribe({
        next: (trades) => this.allTrades = trades,
        error: () => this.allTrades = []
      });
    }

    this.api.getTradeStats(this.selectedInstrument).subscribe({
      next: (stats) => {
        this.stats = stats;
        this.updateChart();
      },
      error: () => this.stats = null
    });
  }

  syncFromKraken(demo: boolean): void {
    this.syncing = true;
    this.syncMessage = '';
    this.api.syncFills(demo).subscribe({
      next: (res) => {
        this.syncMessage = res.message || `${res.synced} fills imported`;
        this.syncing = false;
        this.loadData();
      },
      error: (err) => {
        this.syncMessage = 'Sync error: ' + (err.error?.message || err.message);
        this.syncing = false;
      }
    });
  }

  get filteredTrades(): Trade[] {
    return this.allTrades.filter(t => {
      if (this.statusFilter !== 'ALL' && t.status !== this.statusFilter) return false;
      if (this.directionFilter !== 'ALL' && t.direction !== this.directionFilter) return false;
      return true;
    });
  }

  get totalPnl(): number {
    return this.filteredTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
  }

  get winCount(): number {
    return this.filteredTrades.filter(t => t.status === 'WON').length;
  }

  get lossCount(): number {
    return this.filteredTrades.filter(t => t.status === 'LOST').length;
  }

  getPnlClass(val: number): string {
    if (val > 0) return 'positive';
    if (val < 0) return 'negative';
    return '';
  }

  clearTrades(): void {
    if (confirm('Supprimer tout l\'historique des trades ?')) {
      this.api.deleteAllTrades().subscribe({
        next: () => {
          this.allTrades = [];
          this.stats = null;
          this.updateChart();
        },
        error: () => alert('Erreur lors de la suppression')
      });
    }
  }

  private initChart(): void {
    if (!this.chartRef?.nativeElement) return;

    this.chart = createChart(this.chartRef.nativeElement, {
      width: this.chartRef.nativeElement.clientWidth,
      height: 250,
      layout: {
        background: { color: 'transparent' } as any,
        textColor: '#64748b',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.03)' },
        horzLines: { color: 'rgba(255,255,255,0.03)' },
      },
      crosshair: {
        horzLine: { color: 'rgba(0,255,249,0.3)' },
        vertLine: { color: 'rgba(0,255,249,0.3)' },
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.06)',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.06)',
      },
    });

    this.areaSeries = this.chart.addSeries(AreaSeries, {
      lineColor: '#00fff9',
      topColor: 'rgba(0, 255, 249, 0.2)',
      bottomColor: 'rgba(0, 255, 249, 0.01)',
      lineWidth: 2,
    });

    const ro = new ResizeObserver(() => {
      if (this.chart && this.chartRef?.nativeElement) {
        this.chart.applyOptions({ width: this.chartRef.nativeElement.clientWidth });
      }
    });
    ro.observe(this.chartRef.nativeElement);
  }

  private updateChart(): void {
    if (!this.areaSeries || !this.stats?.equityCurve) return;

    const data: AreaData<Time>[] = this.stats.equityCurve.map(p => ({
      time: p.time as Time,
      value: p.value,
    }));

    this.areaSeries.setData(data);

    if (this.stats.totalPnl >= 0) {
      this.areaSeries.applyOptions({
        lineColor: '#39ff14',
        topColor: 'rgba(57, 255, 20, 0.2)',
        bottomColor: 'rgba(57, 255, 20, 0.01)',
      });
    } else {
      this.areaSeries.applyOptions({
        lineColor: '#ff3366',
        topColor: 'rgba(255, 51, 102, 0.2)',
        bottomColor: 'rgba(255, 51, 102, 0.01)',
      });
    }

    this.chart?.timeScale().fitContent();
  }
}
