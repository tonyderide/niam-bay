"""Arena — evaluate agents on historical OHLC candles.

Fees realistic Kraken Futures: 0.06% per side (mix maker/taker) + 0.02% slippage = 0.08% per fill.
Round-trip cost = 0.16%. To disable fees (legacy mode), pass fee_pct=0.
"""


class Arena:
    def __init__(self, candles: list[dict], initial_capital: float = 100.0,
                 fee_pct: float = 0.0008, slippage_pct: float = 0.0002):
        self.candles = candles
        self.initial_capital = initial_capital
        # Cost per fill (buy or sell): fee + slippage. Applied as price markup on buy + markdown on sell.
        self.cost_per_fill = fee_pct + slippage_pct  # 0.0010 = 0.10% per side

    def evaluate(self, agents: list) -> dict[str, float]:
        results = {}
        for agent in agents:
            pnl = self._run_agent(agent)
            agent.fitness = pnl
            results[agent.agent_id] = pnl
        return results

    def _run_agent(self, agent) -> float:
        capital = self.initial_capital
        position = None
        agent.history = []
        trade_count = 0

        for i in range(1, len(self.candles)):
            candle = self.candles[i]
            prev = self.candles[i - 1]
            action = agent.decide(candle, prev, position)
            agent.history.append(action)

            if action == "buy" and position is None:
                effective_entry = candle["close"] * (1 + self.cost_per_fill)
                size = capital / effective_entry
                position = {"entry": candle["close"], "size": size, "peak": candle["close"]}
                capital = 0
                trade_count += 1

            elif action == "sell" and position is not None:
                effective_exit = candle["close"] * (1 - self.cost_per_fill)
                capital = position["size"] * effective_exit
                position = None
                trade_count += 1

            elif position is not None:
                if candle["close"] > position["peak"]:
                    position["peak"] = candle["close"]

        if position is not None:
            effective_exit = self.candles[-1]["close"] * (1 - self.cost_per_fill)
            capital = position["size"] * effective_exit

        agent.trade_count = trade_count
        return round(capital - self.initial_capital, 4)
