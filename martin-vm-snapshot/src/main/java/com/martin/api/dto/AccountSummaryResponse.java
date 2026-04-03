package com.martin.api.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AccountSummaryResponse {
    private double balance;
    private double availableMargin;
    private double initialMargin;
    private double unrealizedPnl;
    private double pnl24h;
    private int openPositionsCount;
    private long lastUpdatedAt;
    private boolean error;
    private String errorMessage;
    private int openPositions;
    private String currency;
}
