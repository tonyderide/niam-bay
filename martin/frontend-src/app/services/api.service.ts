import { Injectable, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BotConfig } from '../models/config.model';
import { Trade, TradeStats } from '../models/trade.model';
import { Dashboard } from '../models/dashboard.model';
import { KrakenPosition } from '../models/position.model';
import { LogEntry } from '../models/log-entry.model';
import { OpenOrder } from '../models/open-order.model';
import { ScalpTick, ScalpOrderRequest, ScalpOrderResponse, ScalpBotState } from '../models/scalp.model';
import { GridState } from '../models/grid.model';
import { AutoBotState } from '../models/auto.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = '/api';

  constructor(private http: HttpClient, private zone: NgZone) {}

  getConfigs(): Observable<BotConfig[]> {
    return this.http.get<BotConfig[]>(`${this.baseUrl}/config`);
  }

  saveConfig(config: BotConfig): Observable<BotConfig> {
    return this.http.post<BotConfig>(`${this.baseUrl}/config`, config);
  }

  startBot(configId: number): Observable<string> {
    return this.http.post(`${this.baseUrl}/bot/start/${configId}`, null, { responseType: 'text' });
  }

  stopBot(instrument: string): Observable<string> {
    return this.http.post(`${this.baseUrl}/bot/stop/${instrument}`, null, { responseType: 'text' });
  }

  forceDirection(configId: number, direction: string): Observable<string> {
    return this.http.post(`${this.baseUrl}/bot/force-direction/${configId}?direction=${direction}`, null, { responseType: 'text' });
  }

  getDashboard(instrument: string): Observable<Dashboard> {
    return this.http.get<Dashboard>(`${this.baseUrl}/bot/dashboard/${instrument}`);
  }

  getTrades(instrument: string): Observable<Trade[]> {
    return this.http.get<Trade[]>(`${this.baseUrl}/trades/${instrument}`);
  }

  getAllTrades(): Observable<Trade[]> {
    return this.http.get<Trade[]>(`${this.baseUrl}/trades/all`);
  }

  getTradeStats(instrument?: string): Observable<TradeStats> {
    const param = instrument && instrument !== 'ALL' ? `?instrument=${instrument}` : '';
    return this.http.get<TradeStats>(`${this.baseUrl}/trades/stats${param}`);
  }

  syncFills(demo: boolean = false): Observable<any> {
    return this.http.post(`${this.baseUrl}/trades/sync?demo=${demo}`, null);
  }

  deleteAllTrades(): Observable<string> {
    return this.http.delete(`${this.baseUrl}/trades`, { responseType: 'text' });
  }

  deleteAllConfigs(): Observable<string> {
    return this.http.delete(`${this.baseUrl}/config`, { responseType: 'text' });
  }

  deleteConfig(id: number): Observable<string> {
    return this.http.delete(`${this.baseUrl}/config/${id}`, { responseType: 'text' });
  }

  getOpenPositions(): Observable<KrakenPosition[]> {
    return this.http.get<KrakenPosition[]>(`${this.baseUrl}/bot/positions`);
  }

  getOpenOrders(): Observable<OpenOrder[]> {
    return this.http.get<OpenOrder[]>(`${this.baseUrl}/bot/orders`);
  }

  getPriceHistory(instrument: string, limit = 100): Observable<number[]> {
    return this.http.get<number[]>(`${this.baseUrl}/bot/prices/${instrument}?limit=${limit}`);
  }

  streamLogs(): Observable<LogEntry> {
    return new Observable<LogEntry>(observer => {
      const url = `${this.baseUrl}/sse/logs`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        this.zone.run(() => {
          try {
            const entry: LogEntry = JSON.parse(event.data);
            observer.next(entry);
          } catch (e) {
            // Ignore parse errors
          }
        });
      };

      eventSource.onerror = () => {
        this.zone.run(() => {
          observer.error('SSE log connection error');
        });
      };

      return () => {
        eventSource.close();
      };
    });
  }

  streamScalpTicker(instrument: string, demo: boolean): Observable<ScalpTick> {
    return new Observable<ScalpTick>(observer => {
      const url = `${this.baseUrl}/sse/scalp-ticker/${instrument}?demo=${demo}`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        this.zone.run(() => {
          try {
            const tick: ScalpTick = JSON.parse(event.data);
            observer.next(tick);
          } catch (e) {
            // Ignore parse errors
          }
        });
      };

      eventSource.onerror = () => {
        this.zone.run(() => {
          observer.error('SSE scalp ticker connection error');
        });
      };

      return () => {
        eventSource.close();
      };
    });
  }

  startGrid(instrument: string, capital: number, leverage: number, demo: boolean,
            gridSpacingPct: number = 0.7, totalLevels: number = 6, maxLossPercent: number = 50): Observable<GridState> {
    return this.http.post<GridState>(
      `${this.baseUrl}/grid/start?instrument=${instrument}&capital=${capital}&leverage=${leverage}&demo=${demo}&gridSpacingPct=${gridSpacingPct}&totalLevels=${totalLevels}&maxLossPercent=${maxLossPercent}`, null
    );
  }

  syncGrid(instrument: string, capital: number, leverage: number, demo: boolean,
           gridSpacingPct: number = 0.7, totalLevels: number = 6, maxLossPercent: number = 50): Observable<GridState> {
    return this.http.post<GridState>(
      `${this.baseUrl}/grid/sync?instrument=${instrument}&capital=${capital}&leverage=${leverage}&demo=${demo}&gridSpacingPct=${gridSpacingPct}&totalLevels=${totalLevels}&maxLossPercent=${maxLossPercent}`, null
    );
  }

  analyzeMarket(instrument: string, demo: boolean = false): Observable<any> {
    return this.http.get(`${this.baseUrl}/grid/analyze/${instrument}?demo=${demo}`);
  }

  stopGrid(instrument: string): Observable<string> {
    return this.http.post(`${this.baseUrl}/grid/stop/${instrument}`, null, { responseType: 'text' });
  }

  getGridStatus(instrument: string): Observable<GridState> {
    return this.http.get<GridState>(`${this.baseUrl}/grid/status/${instrument}`);
  }

  getActiveGrids(): Observable<string[]> {
    return this.http.get<string[]>(`${this.baseUrl}/grid/active`);
  }

  placeScalpOrder(request: ScalpOrderRequest): Observable<ScalpOrderResponse> {
    return this.http.post<ScalpOrderResponse>(`${this.baseUrl}/scalp/order`, request);
  }

  getScalpPositions(demo: boolean): Observable<any> {
    return this.http.get(`${this.baseUrl}/scalp/positions?demo=${demo}`);
  }

  startScalpBot(instrument: string, capital: number, leverage: number, demo: boolean, tradingHoursEnabled: boolean = true): Observable<ScalpBotState> {
    return this.http.post<ScalpBotState>(
      `${this.baseUrl}/scalp/bot/start?instrument=${instrument}&capital=${capital}&leverage=${leverage}&demo=${demo}&tradingHoursEnabled=${tradingHoursEnabled}`, null
    );
  }

  setScalpTradingHours(instrument: string, enabled: boolean): Observable<string> {
    return this.http.post(`${this.baseUrl}/scalp/bot/trading-hours/${instrument}?enabled=${enabled}`, null, { responseType: 'text' });
  }

  stopScalpBot(instrument: string): Observable<string> {
    return this.http.post(`${this.baseUrl}/scalp/bot/stop/${instrument}`, null, { responseType: 'text' });
  }

  getScalpBotStatus(instrument: string): Observable<ScalpBotState> {
    return this.http.get<ScalpBotState>(`${this.baseUrl}/scalp/bot/status/${instrument}`);
  }

  getAccountBalance(demo: boolean = false): Observable<any> {
    return this.http.get(`${this.baseUrl}/bot/balance?demo=${demo}`);
  }

  getOhlc(instrument: string, minutes: number = 60): Observable<any> {
    return this.http.get(`${this.baseUrl}/bot/ohlc/${instrument}?minutes=${minutes}`);
  }

  // --- Auto Bot ---

  startAutoBot(instrument: string, capital: number, leverage: number, demo: boolean): Observable<AutoBotState> {
    return this.http.post<AutoBotState>(
      `${this.baseUrl}/auto/start?instrument=${instrument}&capital=${capital}&leverage=${leverage}&demo=${demo}`, null
    );
  }

  stopAutoBot(instrument: string): Observable<string> {
    return this.http.post(`${this.baseUrl}/auto/stop/${instrument}`, null, { responseType: 'text' });
  }

  getAutoBotStatus(instrument: string): Observable<AutoBotState> {
    return this.http.get<AutoBotState>(`${this.baseUrl}/auto/status/${instrument}`);
  }

  streamDashboard(instrument: string): Observable<Dashboard> {
    return new Observable<Dashboard>(observer => {
      const url = `${this.baseUrl}/sse/dashboard/${instrument}`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        this.zone.run(() => {
          try {
            const dashboard: Dashboard = JSON.parse(event.data);
            observer.next(dashboard);
          } catch (e) {
            // Ignore parse errors
          }
        });
      };

      eventSource.onerror = () => {
        this.zone.run(() => {
          observer.error('SSE connection error');
        });
      };

      return () => {
        eventSource.close();
      };
    });
  }
}
