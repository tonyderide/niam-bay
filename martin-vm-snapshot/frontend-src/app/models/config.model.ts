export interface BotConfig {
  id?: number;
  instrument: string;
  initialStake: number;
  maxDoublings: number;
  takeProfitPct: number;
  stopLossPct: number;
  leverage: number;
  signalStrategy: string;
  active: boolean;
  demo?: boolean;
}
