package com.martin.signal;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AutoGridConfig {
    private String instrument;
    private double capital;
    private int leverage;
    private boolean demo;
    private double gridSpacingPct; // e.g. 0.7 for 0.7%
    private int totalLevels;
    private double maxLossPercent;
    private String gridMode; // NEUTRAL, LONG, SHORT
}
