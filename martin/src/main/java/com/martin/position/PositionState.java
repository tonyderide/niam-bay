package com.martin.position;

import lombok.Data;
import java.time.Instant;

@Data
public class PositionState {
    private String instrument;
    private boolean active;
    private String direction; // "SHORT" or "LONG"
    private double entryPrice;
    private double size;        // in BTC
    private double capital;     // in USD
    private int leverage;
    private double slPrice;
    private double tpPrice;
    private double slPct;
    private double tpPct;
    private String entryOrderId;
    private String slOrderId;
    private String tpOrderId;
    private double realizedPnl;
    private String status;      // OPENING, OPEN, CLOSING, CLOSED
    private Instant startedAt;
    private String demo;

    public boolean isDemo() { return "true".equals(demo); }
}
