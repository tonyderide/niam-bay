package com.martin.scalping;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.List;

@Data
@Builder
public class ScalpingBotState {

    public enum Phase {
        FLAT,           // Looking for signals
        ENTRY_PENDING,  // Limit entry order placed, waiting for fill
        IN_POSITION,    // Position open, TP/SL orders active
        COOLDOWN        // Waiting after a trade before next entry
    }

    private String instrument;
    private boolean active;
    private boolean demo;
    private double capital;
    private double leverage;

    // Current state
    private Phase phase;
    private String direction; // LONG, SHORT, or FLAT
    private double currentPrice;
    private double bidPrice;
    private double askPrice;
    private double spread;

    // Position
    private double entryPrice;
    private double positionSize;
    private double stopLoss;
    private double takeProfit;
    private double unrealizedPnl;

    // Entry order tracking
    private String entryOrderId;
    private Instant entryOrderTime;

    // TP/SL order tracking
    private String tpOrderId;
    private String slOrderId;

    // Stats
    private double realizedPnl;
    private int totalTrades;
    private int wins;
    private int losses;
    private double winRate;
    private double bestTrade;
    private double worstTrade;
    private int tradesPerHour;

    // Timing
    private Instant startedAt;
    private Instant lastTradeAt;
    private Instant cooldownUntil;
    private Instant positionOpenedAt;

    // Signal info
    private String lastSignalReason;
    private Instant lastSignalAt;

    // Consecutive losses (for progressive cooldown)
    private int consecutiveLosses;

    // Indicators snapshot
    private double bbUpper;
    private double bbMiddle;
    private double bbLower;
    private double bbWidth; // BB squeeze detection
    private double rsi;
    private double emaFast;
    private double emaSlow;
    private boolean squeezed; // BB squeeze active

    // Trailing stop
    private double trailingStopPrice;
    private boolean trailingActivated;

    // Settings
    private boolean tradingHoursEnabled;

    // Recent trades
    private List<ScalpingBotTrade> recentTrades;
}
