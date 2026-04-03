package com.martin.auto;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class AutoBotTrade {
    private String direction;
    private String instrument;
    private double entryPrice;
    private double exitPrice;
    private double pnl;
    private double size;
    private Instant openedAt;
    private Instant closedAt;
}
