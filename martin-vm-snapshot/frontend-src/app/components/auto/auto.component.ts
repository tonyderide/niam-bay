import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AutoBotState, AutoBotTrade } from '../../models/auto.model';
import { ScalpTick } from '../../models/scalp.model';
import { Subscription, interval } from 'rxjs';
import {
  createChart, IChartApi, ISeriesApi, LineSeries, LineData, Time,
  SeriesMarker, createSeriesMarkers, ISeriesMarkersPluginApi,
  IPriceLine
} from 'lightweight-charts';

@Component({
  selector: 'app-auto',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auto.component.html',
  styleUrl: './auto.component.scss'
})
export class AutoComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('chartContainer') chartContainer!: ElementRef<HTMLDivElement>;

  // Setup
  capital = 28.59;
  leverage = 3;
  demo = false;
  selectedInstrument = 'PF_ETHUSD';
  instruments = ['PF_XBTUSD', 'PF_ETHUSD'];

  // State
  botState: AutoBotState | null = null;
  loading = false;
  error: string | null = null;
  accountBalance: number | null = null;

  // Chart
  private chart?: IChartApi;
  private priceSeries?: ISeriesApi<'Line'>;
  private lineData: LineData<Time>[] = [];
  private markersPlugin?: ISeriesMarkersPluginApi<Time>;
  private entryLine?: IPriceLine;
  private slLine?: IPriceLine;
  private tpLine?: IPriceLine;
  private knownTradeCount = 0;

  // Subs
  private pollSub?: Subscription;
  private tickerSub?: Subscription;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.pollStatus();
    this.pollSub = interval(5000).subscribe(() => this.pollStatus());
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
    this.api.getOhlc(this.selectedInstrument, 240).subscribe({
      next: (data: any) => {
        if (data?.candles?.length) {
          const historyData: LineData<Time>[] = data.candles.map((c: any) => ({
            time: Math.floor(c.time / 1000) as Time,
            value: parseFloat(c.close),
          }));
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

  private updatePriceLines(): void {
    if (!this.priceSeries || !this.botState) return;

    // Remove old lines
    if (this.entryLine) { this.priceSeries.removePriceLine(this.entryLine); this.entryLine = undefined; }
    if (this.slLine) { this.priceSeries.removePriceLine(this.slLine); this.slLine = undefined; }
    if (this.tpLine) { this.priceSeries.removePriceLine(this.tpLine); this.tpLine = undefined; }

    if (!this.botState.active || !this.botState.entryPrice) return;

    // Entry line
    if (this.botState.entryPrice > 0) {
      this.entryLine = this.priceSeries.createPriceLine({
        price: this.botState.averageEntryPrice || this.botState.entryPrice,
        color: '#00fff9',
        lineWidth: 1,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'ENTRY',
      });
    }

    // Stop Loss line
    if (this.botState.stopLoss > 0) {
      this.slLine = this.priceSeries.createPriceLine({
        price: this.botState.stopLoss,
        color: '#ff3366',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'SL',
      });
    }

    // Take Profit line
    if (this.botState.takeProfit > 0) {
      this.tpLine = this.priceSeries.createPriceLine({
        price: this.botState.takeProfit,
        color: '#39ff14',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'TP',
      });
    }
  }

  private updateTradeMarkers(): void {
    if (!this.markersPlugin || !this.botState?.recentTrades?.length) return;
    if (this.botState.recentTrades.length === this.knownTradeCount) return;

    this.knownTradeCount = this.botState.recentTrades.length;

    const markers: SeriesMarker<Time>[] = [];

    for (const trade of this.botState.recentTrades) {
      // Entry marker
      if (trade.openedAt && trade.entryPrice > 0) {
        const entryTime = Math.floor(new Date(trade.openedAt).getTime() / 1000) as Time;
        const isLong = trade.direction === 'LONG' || trade.direction === 'long';
        markers.push({
          time: entryTime,
          position: isLong ? 'belowBar' as const : 'aboveBar' as const,
          color: isLong ? '#39ff14' : '#ff3366',
          shape: isLong ? 'arrowUp' as const : 'arrowDown' as const,
          text: isLong ? `L $${trade.entryPrice.toFixed(1)}` : `S $${trade.entryPrice.toFixed(1)}`,
        });
      }

      // Exit marker
      if (trade.closedAt && trade.exitPrice > 0) {
        const exitTime = Math.floor(new Date(trade.closedAt).getTime() / 1000) as Time;
        markers.push({
          time: exitTime,
          position: 'inBar' as const,
          color: '#ffaa00',
          shape: 'circle' as const,
          text: `X $${trade.exitPrice.toFixed(1)}`,
        });
      }
    }

    markers.sort((a, b) => (a.time as number) - (b.time as number));
    this.markersPlugin.setMarkers(markers);
  }

  // --- Bot control ---

  private pollStatus(): void {
    this.api.getAutoBotStatus(this.selectedInstrument).subscribe({
      next: (state) => {
        if (state && state.active) {
          this.botState = state;
          this.updatePriceLines();
          this.updateTradeMarkers();
        } else if (state) {
          // Bot exists but inactive - still show last state for realized P&L etc.
          this.botState = state;
          this.updatePriceLines();
          this.updateTradeMarkers();
        } else if (this.botState?.instrument === this.selectedInstrument) {
          this.botState = null;
        }
      },
      error: () => {}
    });
  }

  startBot(): void {
    this.loading = true;
    this.error = null;
    this.api.startAutoBot(this.selectedInstrument, this.capital, this.leverage, this.demo).subscribe({
      next: (state) => {
        this.botState = state;
        this.loading = false;
        setTimeout(() => this.updatePriceLines(), 500);
      },
      error: (err) => {
        this.error = err.error?.error || err.error || 'Failed to start auto bot';
        this.loading = false;
      }
    });
  }

  stopBot(): void {
    this.loading = true;
    this.error = null;
    this.api.stopAutoBot(this.selectedInstrument).subscribe({
      next: () => {
        this.loading = false;
        this.knownTradeCount = 0;
        if (this.priceSeries) {
          if (this.entryLine) { this.priceSeries.removePriceLine(this.entryLine); this.entryLine = undefined; }
          if (this.slLine) { this.priceSeries.removePriceLine(this.slLine); this.slLine = undefined; }
          if (this.tpLine) { this.priceSeries.removePriceLine(this.tpLine); this.tpLine = undefined; }
        }
        this.markersPlugin?.setMarkers([]);
        this.pollStatus();
      },
      error: (err) => {
        this.error = err.error?.error || err.error || 'Failed to stop auto bot';
        this.loading = false;
      }
    });
  }

  onInstrumentChange(): void {
    this.botState = null;
    this.knownTradeCount = 0;
    this.lineData = [];
    this.pollStatus();
    this.loadPriceHistory();
    this.connectTicker();
    this.loadAccountBalance();
  }

  // --- Helpers ---

  getPnlClass(value: number | null | undefined): string {
    if (value == null) return '';
    return value > 0 ? 'positive' : value < 0 ? 'negative' : '';
  }

  getDirectionClass(direction: string | null | undefined): string {
    if (!direction) return '';
    const d = direction.toUpperCase();
    return d === 'LONG' ? 'direction-long' : d === 'SHORT' ? 'direction-short' : '';
  }
}
