export interface Trade {
  id: number;
  instrument: string;
  direction: string;
  status: string;
  source: string;
  stake: number;
  leverage: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  fees: number;
  doublingStep: number;
  openedAt: string;
  closedAt: string;
}

export interface TradeStats {
  totalTrades: number;
  totalPnl: number;
  wins: number;
  losses: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  bestTrade: number;
  worstTrade: number;
  profitFactor: number;
  maxDrawdown: number;
  totalFees: number;
  equityCurve: EquityPoint[];
}

export interface EquityPoint {
  time: number;
  value: number;
}
