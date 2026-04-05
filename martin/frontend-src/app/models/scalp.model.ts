export interface ScalpTick {
  time: number;
  price: number;
}

export interface ScalpOrderRequest {
  instrument: string;
  side: string;
  size: number;
  demo: boolean;
  reduceOnly: boolean;
}

export interface ScalpOrderResponse {
  success: boolean;
  orderId?: string;
  error?: string;
}

export interface ScalpBotState {
  instrument: string;
  active: boolean;
  demo: boolean;
  capital: number;
  leverage: number;

  phase: 'FLAT' | 'ENTRY_PENDING' | 'IN_POSITION' | 'COOLDOWN';
  direction: string;
  currentPrice: number;
  bidPrice: number;
  askPrice: number;
  spread: number;

  entryPrice: number;
  positionSize: number;
  stopLoss: number;
  takeProfit: number;
  unrealizedPnl: number;

  realizedPnl: number;
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  bestTrade: number;
  worstTrade: number;
  tradesPerHour: number;

  startedAt: string;
  lastTradeAt: string;
  lastSignalReason: string;
  lastSignalAt: string;

  bbUpper: number;
  bbMiddle: number;
  bbLower: number;
  bbWidth: number;
  rsi: number;
  emaFast: number;
  emaSlow: number;
  squeezed: boolean;
  consecutiveLosses: number;
  tradingHoursEnabled: boolean;

  recentTrades: ScalpBotTrade[];
}

export interface ScalpBotTrade {
  direction: string;
  instrument: string;
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  pnlPercent: number;
  fees: number;
  exitReason: string;
  openedAt: string;
  closedAt: string;
  durationSeconds: number;
}
