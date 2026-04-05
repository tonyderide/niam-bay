package com.martin.signal;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class SignalResult {

    public enum EmaStatus { UPTREND, DOWNTREND }
    public enum Signal { OPEN, WAIT, DANGER }

    private String instrument;
    private double price;
    private EmaStatus emaStatus;
    private double ema50;
    private double ema200;
    private double rsi;
    private double volatilityPct;
    private Signal signal;
    private String reason;
    private Instant timestamp;
}
