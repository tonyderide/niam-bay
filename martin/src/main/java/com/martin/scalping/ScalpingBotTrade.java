package com.martin.scalping;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class ScalpingBotTrade {
    private String direction;
    private String instrument;
    private double entryPrice;
    private double exitPrice;
    private double size;
    private double pnl;
    private double pnlPercent;
    private double fees;
    private String exitReason; // TP, SL, TIMEOUT, MANUAL
    private Instant openedAt;
    private Instant closedAt;
    private long durationSeconds;
}
