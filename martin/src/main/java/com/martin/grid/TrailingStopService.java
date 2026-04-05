package com.martin.grid;

import lombok.Data;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class TrailingStopService {

    private static final Logger log = LoggerFactory.getLogger(TrailingStopService.class);

    @Autowired
    private GridTradingService gridTradingService;

    private final Map<String, TrailingState> states = new ConcurrentHashMap<>();

    @Data
    public static class TrailingState {
        private String instrument;
        private double highWaterMark;
        private double trailAmount;  // default $0.30
        private double minProfit;    // default $0.20
        private boolean activated;
        private Instant enabledAt;
        private Instant activatedAt;
        private Instant lastCheckedAt;
    }

    /**
     * Check trailing stops every 10 seconds.
     * Monitors profit of active grids and triggers stop if profit drops
     * below highWaterMark - trailAmount after activation.
     */
    @Scheduled(fixedRate = 10000)
    public void checkTrailingStops() {
        if (states.isEmpty()) return;

        for (Map.Entry<String, TrailingState> entry : states.entrySet()) {
            String instrument = entry.getKey();
            TrailingState ts = entry.getValue();

            try {
                GridState grid = gridTradingService.getState(instrument);
                if (grid == null || !grid.isActive()) continue;

                BigDecimal totalProfit = grid.getTotalProfit();
                if (totalProfit == null) continue;

                double profit = totalProfit.doubleValue();
                ts.setLastCheckedAt(Instant.now());

                // Update high water mark
                if (profit > ts.highWaterMark) {
                    ts.highWaterMark = profit;
                }

                // Activate trailing stop when minimum profit threshold is reached
                if (!ts.activated && profit >= ts.minProfit) {
                    ts.activated = true;
                    ts.activatedAt = Instant.now();
                    log.info("Trailing stop ACTIVATED for {} at profit ${}", instrument, String.format("%.4f", profit));
                }

                // Trigger stop if profit drops below trail threshold
                if (ts.activated && profit < ts.highWaterMark - ts.trailAmount) {
                    log.warn("TRAILING STOP triggered for {} — profit dropped from ${} to ${}",
                            instrument,
                            String.format("%.4f", ts.highWaterMark),
                            String.format("%.4f", profit));

                    gridTradingService.stopGrid(instrument);
                    states.remove(instrument);
                    // TODO: send Telegram notification
                }

            } catch (Exception e) {
                log.error("Trailing stop check failed for {}: {}", instrument, e.getMessage());
            }
        }
    }

    /**
     * Enable trailing stop for an instrument.
     */
    public void enable(String instrument, double trailAmount, double minProfit) {
        TrailingState ts = new TrailingState();
        ts.setInstrument(instrument);
        ts.setTrailAmount(trailAmount);
        ts.setMinProfit(minProfit);
        ts.setHighWaterMark(0.0);
        ts.setActivated(false);
        ts.setEnabledAt(Instant.now());

        states.put(instrument, ts);
        log.info("Trailing stop ENABLED for {} — trail=${}, minProfit=${}", instrument, trailAmount, minProfit);
    }

    /**
     * Disable trailing stop for an instrument.
     */
    public void disable(String instrument) {
        TrailingState removed = states.remove(instrument);
        if (removed != null) {
            log.info("Trailing stop DISABLED for {}", instrument);
        }
    }

    /**
     * Get all trailing stop states.
     */
    public Map<String, TrailingState> getAll() {
        return Collections.unmodifiableMap(states);
    }

    /**
     * Get trailing stop state for a specific instrument.
     */
    public TrailingState getState(String instrument) {
        return states.get(instrument);
    }
}
