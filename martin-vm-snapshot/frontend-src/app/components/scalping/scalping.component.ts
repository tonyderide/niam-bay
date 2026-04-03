import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ScalpTick, ScalpBotState, ScalpBotTrade } from '../../models/scalp.model';
import { Subscription, interval, forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import {
  createChart, IChartApi, ISeriesApi,
  CandlestickSeries, CandlestickData, LineSeries, LineData, Time
} from 'lightweight-charts';

@Component({
  selector: 'app-scalping',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './scalping.component.html',
  styleUrl: './scalping.component.scss'
})
export class ScalpingComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('chartContainer') chartContainer!: ElementRef<HTMLDivElement>;

  instruments = ['PF_XBTUSD', 'PF_ETHUSD'];
  selectedInstrument = 'PF_ETHUSD';
  demo = false;
  capital = 50;
  leverage = 10;
  tradingHoursEnabled = true;
  loading = false;
  initialLoading = true;
  error = '';
  accountBalance: number | null = null;

  botState: ScalpBotState | null = null;

  private chart?: IChartApi;
  private candleSeries?: ISeriesApi<'Candlestick'>;
  private bbUpperLine?: ISeriesApi<'Line'>;
  private bbMiddleLine?: ISeriesApi<'Line'>;
  private bbLowerLine?: ISeriesApi<'Line'>;
  private entryLine?: ISeriesApi<'Line'>;
  private tpLine?: ISeriesApi<'Line'>;
  private slLine?: ISeriesApi<'Line'>;

  private tickerSub?: Subscription;
  private statusPollSub?: Subscription;

  // Candle aggregation from ticks
  private currentCandle?: { open: number; high: number; low: number; close: number; time: number };
  private candleBuffer: CandlestickData<Time>[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.initialLoading = true;
    forkJoin({
      balance: this.api.getAccountBalance(this.demo).pipe(catchError(() => of(null))),
      status: this.api.getScalpBotStatus(this.selectedInstrument).pipe(catchError(() => of(null)))
    }).subscribe({
      next: ({ balance, status }) => {
        if (balance?.accounts) {
          const flex = Object.values(balance.accounts).find((a: any) => a.type === 'cashAccount') as any;
          if (flex) this.accountBalance = flex.balances?.availableMargin || flex.auxiliary?.af;
        }
        if (status && status.active) {
          this.botState = status;
          this.tradingHoursEnabled = status.tradingHoursEnabled;
        }
        this.initialLoading = false;
      },
      error: () => {
        this.initialLoading = false;
      }
    });

    this.statusPollSub = interval(3000).subscribe(() => {
      if (this.botState && this.botState.active) {
        this.pollStatus();
      }
    });
  }

  ngAfterViewInit(): void {
    this.initChart();
    this.loadOhlcHistory();
    this.connectTicker();
  }

  ngOnDestroy(): void {
    this.tickerSub?.unsubscribe();
    this.statusPollSub?.unsubscribe();
    this.chart?.remove();
  }

  // ─── Chart setup ──────────────────────────────────────────────

  private initChart(): void {
    if (!this.chartContainer) return;

    this.chart = createChart(this.chartContainer.nativeElement, {
      layout: {
        background: { color: '#0a0e17' },
        textColor: '#64748b',
        fontFamily: "'JetBrains Mono', monospace",
      },
      grid: {
        vertLines: { color: 'rgba(30, 41, 59, 0.3)' },
        horzLines: { color: 'rgba(30, 41, 59, 0.3)' },
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

    this.candleSeries = this.chart.addSeries(CandlestickSeries, {
      upColor: '#39ff14',
      downColor: '#ff3366',
      borderUpColor: '#39ff14',
      borderDownColor: '#ff3366',
      wickUpColor: '#39ff1488',
      wickDownColor: '#ff336688',
    });

    // BB lines
    this.bbUpperLine = this.chart.addSeries(LineSeries, {
      color: 'rgba(255, 184, 0, 0.4)',
      lineWidth: 1,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    this.bbMiddleLine = this.chart.addSeries(LineSeries, {
      color: 'rgba(255, 184, 0, 0.2)',
      lineWidth: 1,
      lineStyle: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    this.bbLowerLine = this.chart.addSeries(LineSeries, {
      color: 'rgba(255, 184, 0, 0.4)',
      lineWidth: 1,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });

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

  private loadOhlcHistory(): void {
    this.api.getOhlc(this.selectedInstrument, 240).subscribe({
      next: (data: any) => {
        if (data?.candles) {
          const candles: CandlestickData<Time>[] = data.candles.map((c: any) => ({
            time: (Math.floor(c.time / 60000) * 60) as Time,
            open: parseFloat(c.open),
            high: parseFloat(c.high),
            low: parseFloat(c.low),
            close: parseFloat(c.close),
          }));
          candles.sort((a: any, b: any) => (a.time as number) - (b.time as number));
          this.candleBuffer = candles;
          this.candleSeries?.setData(candles);
          this.chart?.timeScale().fitContent();
        }
      }
    });
  }

  private connectTicker(): void {
    this.tickerSub?.unsubscribe();
    this.tickerSub = this.api.streamScalpTicker(this.selectedInstrument, this.demo).subscribe({
      next: (tick: ScalpTick) => this.onTick(tick),
      error: () => setTimeout(() => this.connectTicker(), 3000)
    });
  }

  private onTick(tick: ScalpTick): void {
    const timeSec = Math.floor(tick.time / 60000) * 60; // 1-min candle

    if (!this.currentCandle || this.currentCandle.time !== timeSec) {
      this.currentCandle = { open: tick.price, high: tick.price, low: tick.price, close: tick.price, time: timeSec };
    } else {
      this.currentCandle.high = Math.max(this.currentCandle.high, tick.price);
      this.currentCandle.low = Math.min(this.currentCandle.low, tick.price);
      this.currentCandle.close = tick.price;
    }

    this.candleSeries?.update({
      time: this.currentCandle.time as Time,
      open: this.currentCandle.open,
      high: this.currentCandle.high,
      low: this.currentCandle.low,
      close: this.currentCandle.close,
    });

    // Update price lines if in position
    this.updatePriceLines();
  }

  private updatePriceLines(): void {
    if (!this.botState || !this.chart) return;

    // Remove old lines
    if (this.entryLine) { this.chart.removeSeries(this.entryLine); this.entryLine = undefined; }
    if (this.tpLine) { this.chart.removeSeries(this.tpLine); this.tpLine = undefined; }
    if (this.slLine) { this.chart.removeSeries(this.slLine); this.slLine = undefined; }

    if (this.botState.phase === 'IN_POSITION' || this.botState.phase === 'ENTRY_PENDING') {
      if (this.botState.entryPrice > 0) {
        this.entryLine = this.chart.addSeries(LineSeries, {
          color: '#00fff9',
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: true,
        });
        const now = Math.floor(Date.now() / 60000) * 60;
        this.entryLine.setData([
          { time: (now - 7200) as Time, value: this.botState.entryPrice },
          { time: now as Time, value: this.botState.entryPrice }
        ]);
      }
      if (this.botState.takeProfit > 0) {
        this.tpLine = this.chart.addSeries(LineSeries, {
          color: '#39ff14',
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: true,
        });
        const now = Math.floor(Date.now() / 60000) * 60;
        this.tpLine.setData([
          { time: (now - 7200) as Time, value: this.botState.takeProfit },
          { time: now as Time, value: this.botState.takeProfit }
        ]);
      }
      if (this.botState.stopLoss > 0) {
        this.slLine = this.chart.addSeries(LineSeries, {
          color: '#ff3366',
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
          lastValueVisible: true,
        });
        const now = Math.floor(Date.now() / 60000) * 60;
        this.slLine.setData([
          { time: (now - 7200) as Time, value: this.botState.stopLoss },
          { time: now as Time, value: this.botState.stopLoss }
        ]);
      }
    }
  }

  // ─── Bot controls ─────────────────────────────────────────────

  startBot(): void {
    this.loading = true;
    this.error = '';
    this.api.startScalpBot(this.selectedInstrument, this.capital, this.leverage, this.demo, this.tradingHoursEnabled).subscribe({
      next: (state) => {
        this.botState = state;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.message || err.message || 'Start failed';
        this.loading = false;
      }
    });
  }

  stopBot(): void {
    this.loading = true;
    this.api.stopScalpBot(this.selectedInstrument).subscribe({
      next: () => {
        this.botState = null;
        this.loading = false;
        this.clearPriceLines();
      },
      error: (err) => {
        this.error = err.error?.message || err.message || 'Stop failed';
        this.loading = false;
      }
    });
  }

  private pollStatus(): void {
    this.api.getScalpBotStatus(this.selectedInstrument).subscribe({
      next: (state) => { this.botState = state; },
      error: () => { this.botState = null; }
    });
  }

  private checkExistingBot(): void {
    this.api.getScalpBotStatus(this.selectedInstrument).subscribe({
      next: (state) => { if (state && state.active) this.botState = state; },
      error: () => {}
    });
  }

  private clearPriceLines(): void {
    if (this.chart) {
      if (this.entryLine) { this.chart.removeSeries(this.entryLine); this.entryLine = undefined; }
      if (this.tpLine) { this.chart.removeSeries(this.tpLine); this.tpLine = undefined; }
      if (this.slLine) { this.chart.removeSeries(this.slLine); this.slLine = undefined; }
    }
  }

  toggleTradingHours(): void {
    if (this.botState && this.botState.active) {
      this.api.setScalpTradingHours(this.selectedInstrument, this.tradingHoursEnabled).subscribe();
    }
  }

  onInstrumentChange(): void {
    this.botState = null;
    this.clearPriceLines();
    this.loadOhlcHistory();
    this.connectTicker();
    this.checkExistingBot();
  }

  // ─── Template helpers ─────────────────────────────────────────

  getPhaseClass(phase: string): string {
    switch (phase) {
      case 'FLAT': return 'phase-flat';
      case 'ENTRY_PENDING': return 'phase-pending';
      case 'IN_POSITION': return 'phase-position';
      case 'COOLDOWN': return 'phase-cooldown';
      default: return '';
    }
  }

  getPhaseLabel(phase: string): string {
    switch (phase) {
      case 'FLAT': return 'SCANNING';
      case 'ENTRY_PENDING': return 'ENTRY PENDING';
      case 'IN_POSITION': return 'IN POSITION';
      case 'COOLDOWN': return 'COOLDOWN';
      default: return phase;
    }
  }

  getPnlClass(val: number): string {
    return val > 0 ? 'positive' : val < 0 ? 'negative' : '';
  }

  getDirectionClass(dir: string): string {
    return dir === 'LONG' ? 'long' : dir === 'SHORT' ? 'short' : '';
  }
}
