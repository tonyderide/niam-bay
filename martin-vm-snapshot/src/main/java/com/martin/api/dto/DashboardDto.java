package com.martin.api.dto;

import lombok.*;
import java.math.BigDecimal;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class DashboardDto {
    private String instrument;
    private boolean botActive;
    private String currentDirection;
    private BigDecimal currentStake;
    private int currentDoubling;
    private BigDecimal totalPnl;
    private int totalTrades;
    private int wins;
    private int losses;
    private BigDecimal currentPrice;
    private BigDecimal entryPrice;
    private BigDecimal takeProfitPrice;
    private BigDecimal stopLossPrice;
    private BigDecimal winRate;
    private BigDecimal unrealizedPnl;
}
