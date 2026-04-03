package com.martin.auto;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.List;

@Data
@Builder
public class AutoBotState {
    private String instrument;
    private boolean active;
    private boolean demo;
    private double capital;
    private double leverage;
    private String direction; // LONG / SHORT / FLAT
    private double entryPrice;
    private double currentPrice;
    private double stopLoss;
    private double takeProfit;
    private double trailingTpHighest; // tracks highest price for trailing TP
    private int safetyOrderCount; // how many DCA safety orders filled
    private double averageEntryPrice; // DCA average
    private double positionSize;
    private double unrealizedPnl;
    private double realizedPnl;
    private Instant startedAt;
    private Instant lastSignalAt;
    private String lastSignalReason;
    private int totalTrades;
    private int wins;
    private int losses;
    private double winRate;
    private Instant cooldownUntil;
    private Instant lastTradeAt;
    private Instant lastSafetyOrderAt;
    private List<AutoBotTrade> recentTrades;
}
