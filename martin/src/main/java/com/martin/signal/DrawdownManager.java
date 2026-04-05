package com.martin.signal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class DrawdownManager {

    private static final Logger log = LoggerFactory.getLogger(DrawdownManager.class);

    public enum DrawdownAction {
        NORMAL,
        REDUCE,      // >= 10% DD
        PAUSE_48H,   // >= 20% DD
        PAUSE_WEEK,  // >= 30% DD
        KILL         // >= 40% DD
    }

    private final Map<String, Double> peakEquityMap = new ConcurrentHashMap<>();
    private double initialCapital = 144.0;
    private boolean killed = false;
    private Instant pauseUntil = null;

    public DrawdownAction checkDrawdown(String instrument, double currentEquity) {
        if (killed) {
            log.warn("DRAWDOWN: System is KILLED. Equity={}", currentEquity);
            return DrawdownAction.KILL;
        }

        if (pauseUntil != null && Instant.now().isBefore(pauseUntil)) {
            log.info("DRAWDOWN: Paused until {} equity={}", pauseUntil, currentEquity);
            return DrawdownAction.PAUSE_48H;
        } else if (pauseUntil != null) {
            log.info("DRAWDOWN: Pause ended, resuming");
            pauseUntil = null;
        }

        double peak = peakEquityMap.getOrDefault(instrument, currentEquity);
        if (currentEquity > peak) {
            peak = currentEquity;
        }
        peakEquityMap.put(instrument, peak);

        double ddPct = (peak - currentEquity) / peak * 100;

        if (ddPct >= 40) {
            killed = true;
            log.error("DRAWDOWN KILL: {}% for {} (peak={}, current={})",
                    String.format("%.2f", ddPct), instrument, peak, currentEquity);
            return DrawdownAction.KILL;
        }
        if (ddPct >= 30) {
            pauseUntil = Instant.now().plusSeconds(7 * 24 * 3600);
            log.error("DRAWDOWN PAUSE_WEEK: {}% for {} (peak={}, current={})",
                    String.format("%.2f", ddPct), instrument, peak, currentEquity);
            return DrawdownAction.PAUSE_WEEK;
        }
        if (ddPct >= 20) {
            pauseUntil = Instant.now().plusSeconds(48 * 3600);
            log.warn("DRAWDOWN PAUSE_48H: {}% for {} (peak={}, current={})",
                    String.format("%.2f", ddPct), instrument, peak, currentEquity);
            return DrawdownAction.PAUSE_48H;
        }
        if (ddPct >= 10) {
            log.warn("DRAWDOWN REDUCE: {}% for {} (peak={}, current={})",
                    String.format("%.2f", ddPct), instrument, peak, currentEquity);
            return DrawdownAction.REDUCE;
        }

        return DrawdownAction.NORMAL;
    }

    public DrawdownAction checkDrawdown(double currentEquity) {
        return checkDrawdown("GLOBAL", currentEquity);
    }

    public void resetPeak(String instrument, double newPeak) {
        peakEquityMap.put(instrument, newPeak);
        log.info("DRAWDOWN: Peak reset for {} to {}", instrument, newPeak);
    }

    public Map<String, Double> getPeakEquityMap() { return peakEquityMap; }
    public double getPeakEquity() { return peakEquityMap.values().stream().mapToDouble(d -> d).max().orElse(0); }
    public void setPeakEquity(double v) { /* legacy compat */ }
    public double getInitialCapital() { return initialCapital; }
    public void setInitialCapital(double v) { this.initialCapital = v; }
    public boolean isKilled() { return killed; }
    public Instant getPauseUntil() { return pauseUntil; }

    public void resetKill() {
        this.killed = false;
        this.pauseUntil = null;
        this.peakEquityMap.clear();
        log.info("DRAWDOWN: Kill switch RESET");
    }
}
