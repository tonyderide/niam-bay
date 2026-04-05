export interface GridLevel {
  index: number;
  price: number;
  side: string;
  status: string;
  krakenOrderId: string | null;
  filledAt: string | null;
  roundTrips: number;
}

export interface GridFill {
  side: string;
  price: number;
  filledAt: string;
  profit: number;
}

export interface GridState {
  instrument: string;
  active: boolean;
  demo: boolean;
  centerPrice: number;
  upperBound: number;
  lowerBound: number;
  gridSpacing: number;
  totalLevels: number;
  leverage: number;
  amountPerLevel: number;
  levels: GridLevel[];
  fills: GridFill[];
  totalProfit: number;
  completedRoundTrips: number;
  startedAt: string;
  krakenRealizedPnl: number | null;
  krakenUnrealizedPnl: number | null;
  krakenTotalPnl: number | null;
}
