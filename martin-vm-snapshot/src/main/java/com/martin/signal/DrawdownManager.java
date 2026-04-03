package com.martin.signal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.Instant;

@Component
public class DrawdownManager {

    private static final Logger log = LoggerFactory.getLogger(DrawdownManager.class);

    public enum DrawdownAction {
        NORMAL,      // no drawdown issue
        REDUCE,      // >= 10% DD — reduce to 2 levels instead of 6
        PAUSE_48H,   // >= 20% DD — pause for 48 hours
        PAUSE_WEEK,  // >= 30% DD — pause for 1 week
        KILL         // >= 40% DD — permanent stop
    }

    private double peakEquity = 0;
    private double initialCapital = 136.0;
    private boolean killed = false;
    private Instant pauseUntil = null;

    /**
     * Called every 15 minutes to evaluate drawdown status.
     */
    public DrawdownAction checkDrawdown(double currentEquity) {
        if (killed) {
            log.warn("DRAWDOWN: System is KILLED — permanent stop active. Equity={}", currentEquity);
            return DrawdownAction.KILL;
        }

        // Check if we are in a pause period
        if (pauseUntil != null && Instant.now().isBefore(pauseUntil)) {
            log.info("DRAWDOWN: Paused until {} — current equity={}", pauseUntil, currentEquity);
            return DrawdownAction.PAUSE_48H; // still paused
        } else if (pauseUntil != null) {
            log.info("DRAWDOWN: Pause period ended, resuming checks");
            pauseUntil = null;
        }

        // Update peak equity
        if (currentEquity > peakEquity) {
            peakEquity = currentEquity;
        }

        // Initialize peak from initial capital if never set
        if (peakEquity <= 0) {
            peakEquity = initialCapital;
        }

        double ddPct = (peakEquity - currentEquity) / peakEquity * 100;

        if (ddPct >= 40) {
            killed = true;
            log.error("DRAWDOWN KILL: {}% drawdown (peak={}, current={}). PERMANENT STOP.",
                    String.format("%.2f", ddPct), peakEquity, currentEquity);
            return DrawdownAction.KILL;
        }

        if (ddPct >= 30) {
            pauseUntil = Instant.now().plusSeconds(7 * 24 * 3600); // 1 week
            log.error("DRAWDOWN PAUSE_WEEK: {}% drawdown (peak={}, current={}). Paused until {}",
                    String.format("%.2f", ddPct), peakEquity, currentEquity, pauseUntil);
            return DrawdownAction.PAUSE_WEEK;
        }

        if (ddPct >= 20) {
            pauseUntil = Instant.now().plusSeconds(48 * 3600); // 48 hours
            log.warn("DRAWDOWN PAUSE_48H: {}% drawdown (peak={}, current={}). Paused until {}",
                    String.format("%.2f", ddPct), peakEquity, currentEquity, pauseUntil);
            return DrawdownAction.PAUSE_48H;
        }

        if (ddPct >= 10) {
            log.warn("DRAWDOWN REDUCE: {}% drawdown (peak={}, current={}). Reducing grid to 2 levels.",
                    String.format("%.2f", ddPct), peakEquity, currentEquity);
            return DrawdownAction.REDUCE;
        }

        return DrawdownAction.NORMAL;
    }

    public double getPeakEquity() {
        return peakEquity;
    }

    public void setPeakEquity(double peakEquity) {
        this.peakEquity = peakEquity;
    }

    public double getInitialCapital() {
        return initialCapital;
    }

    public void setInitialCapital(double initialCapital) {
        this.initialCapital = initialCapital;
    }

    public boolean isKilled() {
        return killed;
    }

    public Instant getPauseUntil() {
        return pauseUntil;
    }

    /**
     * Reset the kill switch (manual override).
     */
    public void resetKill() {
        this.killed = false;
        this.pauseUntil = null;
        log.info("DRAWDOWN: Kill switch RESET manually");
    }
}
