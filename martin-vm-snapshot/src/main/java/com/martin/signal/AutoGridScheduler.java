package com.martin.signal;

import com.martin.grid.GridMode;
import com.martin.grid.GridState;
import com.martin.grid.GridTradingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class AutoGridScheduler {

    private static final Logger log = LoggerFactory.getLogger(AutoGridScheduler.class);

    @Autowired
    private SignalService signalService;

    @Autowired
    private GridTradingService gridTradingService;

    @Autowired
    private DrawdownManager drawdownManager;

    private volatile boolean enabled = false;
    private final Map<String, AutoGridConfig> configs = new ConcurrentHashMap<>();
    private final Map<String, SignalResult> lastSignals = new ConcurrentHashMap<>();
    private final Map<String, RegimeResult> lastRegimes = new ConcurrentHashMap<>();
    private Instant lastCheckTime;

    /**
     * Check signal every 15 minutes. If enabled, evaluate regime (ADX + BB Width)
     * for each configured instrument and auto-start/stop grids based on regime.
     * Also checks drawdown circuit breaker.
     */
    @Scheduled(fixedRate = 900000) // 15 minutes
    public void checkSignals() {
        if (!enabled) return;
        if (configs.isEmpty()) {
            log.debug("Auto-grid enabled but no configs set");
            return;
        }

        lastCheckTime = Instant.now();
        log.info("Auto-grid check (15m): evaluating {} instruments", configs.size());

        for (Map.Entry<String, AutoGridConfig> entry : configs.entrySet()) {
            AutoGridConfig config = entry.getValue();
            String instrument = config.getInstrument();

            try {
                // 1. Check drawdown circuit breaker
                GridState gridState = gridTradingService.getState(instrument);
                boolean gridActive = gridState != null && gridState.isActive();

                if (gridActive && gridState.getTotalProfit() != null) {
                    double equity = config.getCapital() + gridState.getTotalProfit().doubleValue();
                    DrawdownManager.DrawdownAction ddAction = drawdownManager.checkDrawdown(equity);

                    if (ddAction != DrawdownManager.DrawdownAction.NORMAL) {
                        log.warn("DRAWDOWN ACTION for {}: {} — equity={}", instrument, ddAction, equity);

                        if (ddAction == DrawdownManager.DrawdownAction.KILL
                                || ddAction == DrawdownManager.DrawdownAction.PAUSE_WEEK
                                || ddAction == DrawdownManager.DrawdownAction.PAUSE_48H) {
                            gridTradingService.stopGrid(instrument);
                            log.error("DRAWDOWN: Stopped grid for {} — action={}", instrument, ddAction);
                            continue; // skip further checks for this instrument
                        }
                        // REDUCE: will reduce levels below
                    }
                }

                // 2. Check EMA trend (existing logic — danger filter)
                SignalResult signal = signalService.checkEMATrend(instrument);
                lastSignals.put(instrument, signal);

                if (signal.getSignal() == SignalResult.Signal.DANGER && gridActive) {
                    gridTradingService.stopGrid(instrument);
                    log.warn("CIRCUIT BREAKER: Stopped grid for {} — RSI < 35, market in panic", instrument);
                    continue;
                }

                // 3. Check regime (ADX + BB Width)
                RegimeResult regime = signalService.checkRegime(instrument);
                lastRegimes.put(instrument, regime);

                if (regime.isTradeable() && !gridActive) {
                    // Regime is RANGING — good for grid
                    if (signal.getSignal() != SignalResult.Signal.DANGER) {
                        GridMode mode = GridMode.valueOf(config.getGridMode() != null ? config.getGridMode().toUpperCase() : "NEUTRAL");

                        gridTradingService.startGrid(
                                instrument,
                                config.getCapital(),
                                config.getLeverage(),
                                config.isDemo(),
                                config.getGridSpacingPct() / 100.0,
                                config.getTotalLevels(),
                                config.getMaxLossPercent(),
                                mode
                        );
                        log.info("AUTO-GRID: Opened grid for {} — RANGING regime (ADX={}, BBW={}) + EMA OK",
                                instrument,
                                String.format("%.2f", regime.getAdx()),
                                String.format("%.2f", regime.getBbWidth()));
                    }
                }

                if (!regime.isTradeable() && gridActive) {
                    // Regime switched to TRENDING — check if positions are open
                    boolean hasOpenPositions = gridTradingService.hasOpenPositionsOnKraken(instrument, config.isDemo());
                    if (hasOpenPositions) {
                        // Positions still open: switch to close-only mode (only TP orders, no new entries)
                        gridState.setCloseOnly(true);
                        log.warn("REGIME SWITCH to CLOSE-ONLY for {} — TRENDING (ADX={}, BBW={}) but positions still open",
                                instrument,
                                String.format("%.2f", regime.getAdx()),
                                String.format("%.2f", regime.getBbWidth()));
                    } else {
                        // No positions: safe to fully stop
                        gridTradingService.stopGrid(instrument);
                        log.warn("REGIME SWITCH: Stopped grid for {} — now TRENDING (ADX={}, BBW={}), no open positions",
                                instrument,
                                String.format("%.2f", regime.getAdx()),
                                String.format("%.2f", regime.getBbWidth()));
                    }
                }

                // If grid is in close-only and positions are now closed, fully stop
                if (gridActive && gridState != null && gridState.isCloseOnly()) {
                    boolean stillHasPositions = gridTradingService.hasOpenPositionsOnKraken(instrument, config.isDemo());
                    if (!stillHasPositions) {
                        gridTradingService.stopGrid(instrument);
                        log.info("CLOSE-ONLY completed for {} — all positions closed, grid stopped", instrument);
                    }
                }

                log.info("Auto-grid decision for {}: regime={}, tradeable={}, signal={}, gridActive={}",
                        instrument, regime.getRegime(), regime.isTradeable(), signal.getSignal(), gridActive);

            } catch (Exception e) {
                log.error("Auto-grid check failed for {}: {}", instrument, e.getMessage(), e);
            }
        }
    }

    public void enable() {
        this.enabled = true;
        log.info("Auto-grid scheduler ENABLED");
    }

    public void disable() {
        this.enabled = false;
        log.info("Auto-grid scheduler DISABLED");
    }

    public boolean isEnabled() {
        return enabled;
    }

    public void setConfig(AutoGridConfig config) {
        configs.put(config.getInstrument(), config);
        log.info("Auto-grid config set for {}: capital={}, leverage={}, levels={}, mode={}",
                config.getInstrument(), config.getCapital(), config.getLeverage(),
                config.getTotalLevels(), config.getGridMode());
    }

    public void removeConfig(String instrument) {
        configs.remove(instrument);
        lastSignals.remove(instrument);
    }

    public Map<String, AutoGridConfig> getConfigs() {
        return Collections.unmodifiableMap(configs);
    }

    public Map<String, SignalResult> getLastSignals() {
        return Collections.unmodifiableMap(lastSignals);
    }

    public Map<String, RegimeResult> getLastRegimes() {
        return Collections.unmodifiableMap(lastRegimes);
    }

    public DrawdownManager getDrawdownManager() {
        return drawdownManager;
    }

    public Instant getLastCheckTime() {
        return lastCheckTime;
    }
}
