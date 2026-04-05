export interface Dashboard {
  instrument: string;
  botActive: boolean;
  currentDirection: string;
  currentStake: number;
  currentDoubling: number;
  totalPnl: number;
  totalTrades: number;
  wins: number;
  losses: number;
  currentPrice: number | null;
  entryPrice: number | null;
  takeProfitPrice: number | null;
  stopLossPrice: number | null;
  winRate: number | null;
  unrealizedPnl: number | null;
}
