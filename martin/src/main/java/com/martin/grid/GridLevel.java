package com.martin.grid;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class GridLevel {
    private int index;
    private double price;
    private String side; // "buy" or "sell"
    private GridLevelStatus status;
    private String krakenOrderId;
    private Instant filledAt;
    private int roundTrips;
    @Builder.Default
    private boolean hasBuyFill = false; // true after a buy fill (NEUTRAL mode)
    @Builder.Default
    private boolean hasSellFill = false; // true after a sell fill (SHORT mode)

    public enum GridLevelStatus {
        WAITING, PLACED, FILLED
    }
}
