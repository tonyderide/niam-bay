export interface AutoBotState {
  instrument: string;
  active: boolean;
  demo: boolean;
  capital: number;
  leverage: number;
  direction: string;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  trailingTpHighest: number;
  safetyOrderCount: number;
  averageEntryPrice: number;
  positionSize: number;
  unrealizedPnl: number;
  realizedPnl: number;
  startedAt: string;
  lastSignalAt: string;
  lastSignalReason: string;
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  recentTrades: AutoBotTrade[];
}

export interface AutoBotTrade {
  direction: string;
  instrument: string;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  size: number;
  openedAt: string;
  closedAt: string;
}
