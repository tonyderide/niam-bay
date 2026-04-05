import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { GridState, GridLevel, GridFill } from '../../models/grid.model';
import { LogEntry } from '../../models/log-entry.model';
import { ScalpTick } from '../../models/scalp.model';
import { Subscription, interval } from 'rxjs';
import {
  createChart, IChartApi, ISeriesApi, LineSeries, LineData, Time,
  SeriesMarker, createSeriesMarkers, ISeriesMarkersPluginApi,
  IPriceLine
} from 'lightweight-charts';

@Component({
  selector: 'app-grid',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './grid.component.html',
  styleUrl: './grid.component.scss'
})
export class GridComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('chartContainer') chartContainer!: ElementRef<HTMLDivElement>;

  // Setup
  capital = 28.59;
  leverage = 3;
  gridSpacingPct = 0.7;
  totalLevels = 6;
  maxLossPercent = 50;
  demo = false;
  selectedInstrument = 'PF_ETHUSD';
  instruments = ['PF_XBTUSD', 'PF_ETHUSD'];

  // State
  gridState: GridState | null = null;
  loading = false;
  error: string | null = null;
  accountBalance: number | null = null;
  marketAnalysis: any = null;
  analyzingMarket = false;

  // Logs
  gridLogs: LogEntry[] = [];
  private maxLogs = 200;

  // Chart
  private chart?: IChartApi;
  private priceSeries?: ISeriesApi<'Line'>;
  private gridPriceLines: IPriceLine[] = [];
  private lineData: LineData<Time>[] = [];
  private knownFillCount = 0;
  private markersPlugin?: ISeriesMarkersPluginApi<Time>;

  // Subs
  private pollSub?: Subscription;
  private tickerSub?: Subscription;
  private logSub?: Subscription;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.pollStatus();
    this.pollSub = interval(5000).subscribe(() => this.pollStatus());
    this.connectLogs();
  }

  ngAfterViewInit(): void {
    this.initChart();
    this.loadPriceHistory();
    this.connectTicker();
    this.loadAccountBalance();
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
    this.tickerSub?.unsubscribe();
    this.logSub?.unsubscribe();
    this.chart?.remove();
  }

  // --- Chart ---

  private initChart(): void {
    if (!this.chartContainer) return;

    this.chart = createChart(this.chartContainer.nativeElement, {
      layout: {
        background: { color: '#0d1117' },
        textColor: '#64748b',
        fontFamily: "'JetBrains Mono', monospace",
      },
      grid: {
        vertLines: { color: 'rgba(30, 41, 59, 0.5)' },
        horzLines: { color: 'rgba(30, 41, 59, 0.5)' },
      },
      crosshair: {
        vertLine: { color: 'rgba(0, 255, 249, 0.3)', labelBackgroundColor: '#0d1117' },
        horzLine: { color: 'rgba(0, 255, 249, 0.3)', labelBackgroundColor: '#0d1117' },
      },
      timeScale: {
        borderColor: '#1e293b',
        timeVisible: true,
        secondsVisible: true,
      },
      rightPriceScale: { borderColor: '#1e293b' },
    });

    this.priceSeries = this.chart.addSeries(LineSeries, {
      color: '#00fff9',
      lineWidth: 2,
    });

    this.markersPlugin = createSeriesMarkers(this.priceSeries, []);

    this.handleResize();
  }

  private handleResize(): void {
    const resizeObserver = new ResizeObserver(entries => {
      if (this.chart && entries.length > 0) {
        const { width, height } = entries[0].contentRect;
        this.chart.applyOptions({ width, height });
      }
    });
    resizeObserver.observe(this.chartContainer.nativeElement);
  }

  private loadPriceHistory(): void {
    // Load 4h of 1m candles to show price context before grid construction
    this.api.getOhlc(this.selectedInstrument, 240).subscribe({
      next: (data: any) => {
        if (data?.candles?.length) {
          const historyData: LineData<Time>[] = data.candles.map((c: any) => ({
            time: Math.floor(c.time / 1000) as Time,
            value: parseFloat(c.close),
          }));
          // Sort by time ascending (required by lightweight-charts)
          historyData.sort((a, b) => (a.time as number) - (b.time as number));
          this.lineData = historyData;
          this.priceSeries?.setData(historyData);
          this.chart?.timeScale().fitContent();
        }
      },
      error: () => {}
    });
  }

  private loadAccountBalance(): void {
    this.api.getAccountBalance(this.demo).subscribe({
      next: (data: any) => {
        try {
          const flex = data?.accounts?.flex;
          if (flex) {
            const available = flex.availableMargin ?? flex.portfolioValue ?? null;
            this.accountBalance = available;
            // Auto-fill capital with real available balance
            if (available != null && available > 0) {
              this.capital = Math.floor(available * 100) / 100;
            }
          }
        } catch (e) {}
      },
      error: () => {}
    });
  }

  private connectTicker(): void {
    this.tickerSub?.unsubscribe();
    // Don't reset lineData — keep history loaded from OHLC

    this.tickerSub = this.api.streamScalpTicker(this.selectedInstrument, this.demo).subscribe({
      next: (tick) => this.onTick(tick),
      error: () => {
        setTimeout(() => this.connectTicker(), 3000);
      }
    });
  }

  private onTick(tick: ScalpTick): void {
    const timeSec = Math.floor(tick.time / 1000) as Time;
    const point: LineData<Time> = { time: timeSec, value: tick.price };
    this.lineData.push(point);
    if (this.lineData.length > 5000) this.lineData.shift();
    this.priceSeries?.update(point);
  }

  private updateGridLinesOnChart(): void {
    if (!this.priceSeries || !this.gridState) return;

    // Remove old price lines
    for (const line of this.gridPriceLines) {
      this.priceSeries.removePriceLine(line);
    }
    this.gridPriceLines = [];

    for (const level of this.gridState.levels) {
      const color = level.side === 'buy' ? '#39ff14' : '#ff3366';
      const priceLine = this.priceSeries.createPriceLine({
        price: level.price,
        color,
        lineWidth: 1,
        lineStyle: 2, // dashed
        axisLabelVisible: true,
        title: level.side === 'buy' ? 'B' : 'S',
      });
      this.gridPriceLines.push(priceLine);
    }
  }

  private updateFillMarkers(): void {
    if (!this.markersPlugin || !this.gridState?.fills?.length) return;
    if (this.gridState.fills.length === this.knownFillCount) return;

    this.knownFillCount = this.gridState.fills.length;

    const markers: SeriesMarker<Time>[] = this.gridState.fills
      .filter(f => f.filledAt)
      .map(f => {
        const timeSec = Math.floor(new Date(f.filledAt).getTime() / 1000) as Time;
        const isBuy = f.side === 'buy';
        return {
          time: timeSec,
          position: isBuy ? 'belowBar' as const : 'aboveBar' as const,
          color: isBuy ? '#39ff14' : '#ff3366',
          shape: isBuy ? 'arrowUp' as const : 'arrowDown' as const,
          text: isBuy ? `B $${f.price.toFixed(1)}` : `S $${f.price.toFixed(1)}`,
        };
      })
      .sort((a, b) => (a.time as number) - (b.time as number));

    this.markersPlugin.setMarkers(markers);
  }

  // --- Logs ---

  private connectLogs(): void {
    this.logSub = this.api.streamLogs().subscribe({
      next: (entry) => {
        this.gridLogs.push(entry);
        if (this.gridLogs.length > this.maxLogs) {
          this.gridLogs = this.gridLogs.slice(-this.maxLogs);
        }
      },
      error: () => {
        setTimeout(() => this.connectLogs(), 3000);
      }
    });
  }

  getLogClass(log: LogEntry): string {
    return 'level-' + log.level.toLowerCase();
  }

  // --- Grid control ---

  private pollStatus(): void {
    this.api.getGridStatus(this.selectedInstrument).subscribe({
      next: (state) => {
        if (state && state.active) {
          this.gridState = state;
          this.updateGridLinesOnChart();
          this.updateFillMarkers();
        } else if (this.gridState?.instrument === this.selectedInstrument) {
          this.gridState = null;
        }
      },
      error: () => {}
    });
  }

  analyzeMarket(): void {
    this.analyzingMarket = true;
    this.marketAnalysis = null;
    this.api.analyzeMarket(this.selectedInstrument, this.demo).subscribe({
      next: (data) => {
        this.marketAnalysis = data;
        this.analyzingMarket = false;
      },
      error: (err) => {
        this.marketAnalysis = {
          signal: 'WAIT',
          recommendation: 'Erreur de connexion au backend',
          error: err.message || 'Backend inaccessible'
        };
        this.analyzingMarket = false;
      }
    });
  }

  syncGrid(): void {
    this.loading = true;
    this.error = null;
    this.api.syncGrid(this.selectedInstrument, this.capital, this.leverage, this.demo,
      this.gridSpacingPct, this.totalLevels, this.maxLossPercent).subscribe({
      next: (state) => {
        this.gridState = state;
        this.loading = false;
        setTimeout(() => this.updateGridLinesOnChart(), 500);
      },
      error: (err) => {
        this.error = err.error?.error || 'No grid orders found on Kraken';
        this.loading = false;
      }
    });
  }

  startGrid(): void {
    this.loading = true;
    this.error = null;
    this.api.startGrid(this.selectedInstrument, this.capital, this.leverage, this.demo,
      this.gridSpacingPct, this.totalLevels, this.maxLossPercent).subscribe({
      next: (state) => {
        this.gridState = state;
        this.loading = false;
        setTimeout(() => this.updateGridLinesOnChart(), 500);
      },
      error: (err) => {
        this.error = err.error?.error || 'Failed to start grid';
        this.loading = false;
      }
    });
  }

  stopGrid(): void {
    if (!this.gridState) return;
    this.loading = true;
    this.api.stopGrid(this.gridState.instrument).subscribe({
      next: () => {
        this.gridState = null;
        this.loading = false;
        this.knownFillCount = 0;
        if (this.priceSeries) {
          for (const line of this.gridPriceLines) {
            this.priceSeries.removePriceLine(line);
          }
          this.gridPriceLines = [];
        }
        this.markersPlugin?.setMarkers([]);
      },
      error: () => { this.loading = false; }
    });
  }

  onInstrumentChange(): void {
    this.gridState = null;
    this.knownFillCount = 0;
    this.lineData = [];
    this.marketAnalysis = null;
    this.pollStatus();
    this.loadPriceHistory();
    this.connectTicker();
    this.loadAccountBalance();
  }

  getLevelClass(level: GridLevel): string {
    if (level.status === 'FILLED') return 'level-filled';
    if (level.status === 'PLACED') return level.side === 'buy' ? 'level-buy' : 'level-sell';
    return 'level-waiting';
  }
}
