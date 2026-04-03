package com.martin.grid;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

@Data
@Builder
public class GridState {
    private String instrument;
    private boolean active;
    private boolean demo;
    private double centerPrice;
    private double upperBound;
    private double lowerBound;
    private double gridSpacing;
    private int totalLevels;
    private int leverage;
    private double amountPerLevel;
    private List<GridLevel> levels;
    private BigDecimal totalProfit;
    private int completedRoundTrips;
    private Instant startedAt;
    private List<GridFill> fills;
    private double maxLossPercent; // % of capital, e.g. 50 = stop if loss > 50% of capital
    private double capital;
    @Builder.Default
    private GridMode gridMode = GridMode.NEUTRAL;

    /** Close-only mode: grid stays active but only places TP orders (sell for NEUTRAL, buy for SHORT), no new entries */
    @Builder.Default
    private boolean closeOnly = false;

    // Real P&L from Kraken API (enriched on getState)
    private BigDecimal krakenRealizedPnl;
    private BigDecimal krakenUnrealizedPnl;
    private BigDecimal krakenTotalPnl;
}
