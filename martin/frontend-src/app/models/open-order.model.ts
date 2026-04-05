export interface OpenOrder {
  orderId: string;
  symbol: string;
  side: string;
  orderType: string;
  quantity: number;
  filled: number;
  limitPrice: number;
  stopPrice: number;
  reduceOnly: boolean;
  status: string;
}
