package com.martin.signal;

import com.martin.grid.GridMode;
import com.martin.grid.GridState;
import com.martin.grid.GridTradingService;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenOrderRequest;
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

    private static final double WINNING_SL_PCT = 0.006;
    private static final double WINNING_TP_PCT = 0.025;
    private static final double LOSING_SL_PCT = 0.030;
    private static final double LOSING_TP_PCT = 0.002;

    @Autowired
    private SignalService signalService;

    @Autowired
    private GridTradingService gridTradingService;

    @Autowired
    private KrakenFuturesRestClient krakenClient;

    @Autowired
    private DrawdownManager drawdownManager;

    /**
     * Trading hours: 08:00 - 02:00 UTC. Night (02:00-08:00 UTC) = observe only.
     */
    private boolean isWithinTradingHours() {
        int hour = java.time.ZonedDateTime.now(java.time.ZoneOffset.UTC).getHour();
        return hour >= 8 || hour < 2;
    }

    private volatile boolean enabled = false;
    private final Map<String, AutoGridConfig> configs = new ConcurrentHashMap<>();
    private final Map<String, SignalResult> lastSignals = new ConcurrentHashMap<>();
    private final Map<String, RegimeResult> lastRegimes = new ConcurrentHashMap<>();
    private Instant lastCheckTime;

    @Scheduled(fixedRate = 900000)
    public void checkSignals() {
        if (!enabled) return;
        if (configs.isEmpty()) return;

        lastCheckTime = Instant.now();
        log.info("Auto-grid check (15m): evaluating {} instruments", configs.size());

        for (Map.Entry<String, AutoGridConfig> entry : configs.entrySet()) {
            AutoGridConfig config = entry.getValue();
            String instrument = config.getInstrument();

            try {
                GridState gridState = gridTradingService.getState(instrument);
                boolean gridActive = gridState != null && gridState.isActive();

                // 1. Drawdown check (per-instrument)
                if (gridActive && gridState.getTotalProfit() != null) {
                    double equity = config.getCapital() + gridState.getTotalProfit().doubleValue();
                    DrawdownManager.DrawdownAction ddAction = drawdownManager.checkDrawdown(instrument, equity);

                    if (ddAction == DrawdownManager.DrawdownAction.KILL
                            || ddAction == DrawdownManager.DrawdownAction.PAUSE_WEEK
                            || ddAction == DrawdownManager.DrawdownAction.PAUSE_48H) {
                        gridTradingService.stopGrid(instrument);
                        log.error("DRAWDOWN: Stopped grid for {} action={}", instrument, ddAction);
                        continue;
                    }

                    // FIX 3: REDUCE implemented - restart with 2 levels
                    if (ddAction == DrawdownManager.DrawdownAction.REDUCE) {
                        int currentLevels = gridState.getLevels().size();
                        if (currentLevels > 2) {
                            log.warn("DRAWDOWN REDUCE: Restarting {} with 2 levels (was {})", instrument, currentLevels);
                            gridTradingService.stopGrid(instrument);
                            GridMode mode = GridMode.valueOf(config.getGridMode() != null ? config.getGridMode().toUpperCase() : "NEUTRAL");
                            gridTradingService.startGrid(instrument, config.getCapital(), config.getLeverage(),
                                    config.isDemo(), config.getGridSpacingPct() / 100.0, 2, config.getMaxLossPercent(), mode);
                        }
                    }
                }

                // 2. Signal + regime checks — ALWAYS run (observation)
                SignalResult signal = signalService.checkEMATrend(instrument);
                lastSignals.put(instrument, signal);

                RegimeResult regime = signalService.checkRegime(instrument);
                lastRegimes.put(instrument, regime);

                // 3. Night gate — observe only, no action (drawdown still runs above)
                if (!isWithinTradingHours()) {
                    log.info("[NIGHT] {} regime={} signal={} gridActive={} — observe only, no action",
                            instrument, regime.getRegime(), signal.getSignal(), gridActive);
                    continue;
                }

                // 4. CIRCUIT BREAKER — daytime only
                if (signal.getSignal() == SignalResult.Signal.DANGER && gridActive) {
                    gridTradingService.stopGrid(instrument);
                    log.warn("CIRCUIT BREAKER: Stopped grid for {} DANGER", instrument);
                    continue;
                }

                // 5. RANGING = open grid, even if EMA downtrend
                if (regime.isTradeable() && !gridActive) {
                    if (signal.getSignal() != SignalResult.Signal.DANGER) {
                        GridMode mode = GridMode.valueOf(config.getGridMode() != null ? config.getGridMode().toUpperCase() : "NEUTRAL");
                        drawdownManager.resetPeak(instrument, config.getCapital());
                        gridTradingService.startGrid(instrument, config.getCapital(), config.getLeverage(),
                                config.isDemo(), config.getGridSpacingPct() / 100.0,
                                config.getTotalLevels(), config.getMaxLossPercent(), mode);
                        log.info("AUTO-GRID: Opened grid for {} RANGING (ADX={}, BBW={}) signal={}",
                                instrument, String.format("%.2f", regime.getAdx()),
                                String.format("%.2f", regime.getBbWidth()), signal.getSignal());
                    }
                }

                // 6. TRENDING = close-only or stop
                if (!regime.isTradeable() && gridActive) {
                    boolean hasPositions = gridTradingService.hasOpenPositionsOnKraken(instrument, config.isDemo());
                    if (hasPositions) {
                        gridState.setCloseOnly(true);
                        placeCloseOnlyProtection(instrument, config, signal);
                        log.warn("REGIME SWITCH CLOSE-ONLY for {} + TP/SL placed", instrument);
                    } else {
                        gridTradingService.stopGrid(instrument);
                        log.warn("REGIME SWITCH: Stopped grid for {} no positions", instrument);
                    }
                }

                if (gridActive && gridState != null && gridState.isCloseOnly()) {
                    boolean still = gridTradingService.hasOpenPositionsOnKraken(instrument, config.isDemo());
                    if (!still) {
                        gridTradingService.stopGrid(instrument);
                        log.info("CLOSE-ONLY completed for {} positions closed", instrument);
                    }
                }

                log.info("Auto-grid decision for {}: regime={}, tradeable={}, signal={}, gridActive={}",
                        instrument, regime.getRegime(), regime.isTradeable(), signal.getSignal(), gridActive);

            } catch (Exception e) {
                log.error("Auto-grid check failed for {}: {}", instrument, e.getMessage(), e);
            }
        }
    }

    private void placeCloseOnlyProtection(String instrument, AutoGridConfig config, SignalResult signal) {
        try {
            var posResponse = krakenClient.getOpenPositions(config.isDemo()).block();
            if (posResponse == null || posResponse.getOpenPositions() == null) return;

            for (var pos : posResponse.getOpenPositions()) {
                if (!instrument.equals(pos.getSymbol())) continue;
                if (pos.getSize() == null || Math.abs(pos.getSize()) < 0.0000001) continue;

                double size = Math.abs(pos.getSize());
                double entryPrice = pos.getPrice();
                double currentPrice = signal.getPrice();
                boolean isLong = pos.getSize() > 0;
                String closeSide = isLong ? "sell" : "buy";

                double tpPrice, slPrice;

                if (isLong) {
                    boolean winning = currentPrice > entryPrice;
                    if (winning) {
                        slPrice = currentPrice * (1 - WINNING_SL_PCT);
                        tpPrice = currentPrice * (1 + WINNING_TP_PCT);
                    } else {
                        slPrice = entryPrice * (1 - LOSING_SL_PCT);
                        tpPrice = entryPrice * (1 + LOSING_TP_PCT);
                    }
                } else {
                    boolean winning = currentPrice < entryPrice;
                    if (winning) {
                        slPrice = currentPrice * (1 + WINNING_SL_PCT);
                        tpPrice = currentPrice * (1 - WINNING_TP_PCT);
                    } else {
                        slPrice = entryPrice * (1 + LOSING_SL_PCT);
                        tpPrice = entryPrice * (1 - LOSING_TP_PCT);
                    }
                }

                // TP: limit order, reduce-only
                KrakenOrderRequest tpOrder = KrakenOrderRequest.builder()
                        .orderType("lmt").symbol(instrument).side(closeSide)
                        .size(size).limitPrice(tpPrice).reduceOnly(true).build();

                krakenClient.sendOrder(tpOrder, config.isDemo()).subscribe(
                        r -> log.info("CLOSE-ONLY TP placed: {} {} @ {} size={}", instrument, closeSide, tpPrice, size),
                        err -> log.error("CLOSE-ONLY TP FAILED {}: {}", instrument, err.getMessage())
                );

                // SL: stop-market, reduce-only
                KrakenOrderRequest slOrder = KrakenOrderRequest.builder()
                        .orderType("stp").symbol(instrument).side(closeSide)
                        .size(size).stopPrice(slPrice).reduceOnly(true)
                        .triggerSignal("mark").build();

                krakenClient.sendOrder(slOrder, config.isDemo()).subscribe(
                        r -> log.info("CLOSE-ONLY SL placed: {} {} stop @ {} size={}", instrument, closeSide, slPrice, size),
                        err -> log.error("CLOSE-ONLY SL FAILED {}: {}", instrument, err.getMessage())
                );

                log.info("CLOSE-ONLY protection {}: {} entry={} current={} TP={} SL={}",
                        instrument, isLong ? "LONG" : "SHORT", entryPrice, currentPrice,
                        String.format("%.5f", tpPrice), String.format("%.5f", slPrice));
            }
        } catch (Exception e) {
            log.error("CLOSE-ONLY protection FAILED {}: {}", instrument, e.getMessage(), e);
        }
    }

    public void enable() { this.enabled = true; log.info("Auto-grid scheduler ENABLED"); }
    public void disable() { this.enabled = false; log.info("Auto-grid scheduler DISABLED"); }
    public boolean isEnabled() { return enabled; }

    public void setConfig(AutoGridConfig config) {
        configs.put(config.getInstrument(), config);
        log.info("Auto-grid config set for {}: capital={}, leverage={}, levels={}, mode={}",
                config.getInstrument(), config.getCapital(), config.getLeverage(),
                config.getTotalLevels(), config.getGridMode());
    }

    public void removeConfig(String instrument) { configs.remove(instrument); lastSignals.remove(instrument); }
    public Map<String, AutoGridConfig> getConfigs() { return Collections.unmodifiableMap(configs); }
    public Map<String, SignalResult> getLastSignals() { return Collections.unmodifiableMap(lastSignals); }
    public Map<String, RegimeResult> getLastRegimes() { return Collections.unmodifiableMap(lastRegimes); }
    public DrawdownManager getDrawdownManager() { return drawdownManager; }
    public Instant getLastCheckTime() { return lastCheckTime; }
}
