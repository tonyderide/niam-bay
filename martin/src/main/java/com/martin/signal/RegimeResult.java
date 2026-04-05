package com.martin.signal;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class RegimeResult {

    public enum Regime { RANGING, TRENDING }

    private String instrument;
    private Regime regime;
    private double adx;
    private double bbWidth;
    private boolean tradeable; // ADX < 25 AND bbWidth < 4.0
    private Instant timestamp;
}
