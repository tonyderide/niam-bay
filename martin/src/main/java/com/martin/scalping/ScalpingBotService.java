package com.martin.scalping;

import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.*;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class ScalpingBotService {

    private static final Logger log = LoggerFactory.getLogger(ScalpingBotService.class);

    // Indicator params
    private static final int BB_PERIOD = 20;
    private static final double BB_STD_DEV = 2.0;
    private static final int RSI_PERIOD = 7;
    private static final int EMA_FAST = 5;
    private static final int EMA_SLOW = 13;

    // Trade params
    private static final double TP_PCT = 0.0050;   // 0.50% take profit — net ~0.46% after maker+maker fees
    private static final double SL_PCT = 0.0020;    // 0.20% stop loss — net ~0.27% after maker+taker fees
    private static final int MAX_HOLD_SECONDS = 600; // 10 min max
    private static final int COOLDOWN_WIN_MS = 10_000;    // 10s after win
    private static final int ENTRY_TIMEOUT_MS = 45_000;   // 45s to fill limit
    private static final double MAX_SPREAD_PCT = 0.0008;  // 0.08% max spread — tighter filter to avoid slippage
    private static final double TRAILING_ACTIVATION_PCT = 0.40; // activate trailing when 40% of TP reached

    // Progressive cooldown after losses
    private static final int COOLDOWN_1_LOSS_MS = 120_000;   // 2 min after 1 loss
    private static final int COOLDOWN_2_LOSS_MS = 300_000;   // 5 min after 2 consecutive
    private static final int COOLDOWN_3_LOSS_MS = 900_000;   // 15 min after 3+ consecutive

    // Trading hours filter (UTC)
    private static final int TRADING_HOUR_START = 8;  // 08:00 UTC
    private static final int TRADING_HOUR_END = 22;   // 22:00 UTC

    // Volume filter
    private static final double VOLUME_FILTER_MULTIPLIER = 1.5; // volume > 1.5x avg

    // BB Squeeze detection
    private static final double BB_SQUEEZE_THRESHOLD = 0.003; // BB width < 0.3% of price = squeeze

    // Fee tracking
    private static final double MAKER_FEE = 0.0002;  // 0.02%
    private static final double TAKER_FEE = 0.0005;  // 0.05%

    private final KrakenFuturesRestClient krakenClient;
    private final ConcurrentHashMap<String, ScalpingBotState> activeBots = new ConcurrentHashMap<>();

    // ─── Public API ────────────────────────────────────────────────────

    public void setTradingHoursEnabled(String instrument, boolean enabled) {
        ScalpingBotState state = activeBots.get(instrument);
        if (state != null) {
            state.setTradingHoursEnabled(enabled);
            log.info("SCALP BOT {} — Trading hours filter {}", instrument, enabled ? "ENABLED" : "DISABLED");
        }
    }

    public ScalpingBotState startBot(String instrument, double capital, double leverage, boolean demo) {
        return startBot(instrument, capital, leverage, demo, true);
    }

    public ScalpingBotState startBot(String instrument, double capital, double leverage, boolean demo, boolean tradingHoursEnabled) {
        if (activeBots.containsKey(instrument)) {
            throw new IllegalStateException("Scalping bot already active for " + instrument);
        }

        ScalpingBotState state = ScalpingBotState.builder()
                .instrument(instrument)
                .active(true)
                .demo(demo)
                .capital(capital)
                .leverage(leverage)
                .phase(ScalpingBotState.Phase.FLAT)
                .direction("FLAT")
                .currentPrice(0).bidPrice(0).askPrice(0).spread(0)
                .entryPrice(0).positionSize(0).stopLoss(0).takeProfit(0).unrealizedPnl(0)
                .realizedPnl(0).totalTrades(0).wins(0).losses(0).winRate(0)
                .bestTrade(0).worstTrade(0).tradesPerHour(0)
                .consecutiveLosses(0)
                .startedAt(Instant.now())
                .lastSignalReason("Bot started, collecting candle data...")
                .bbUpper(0).bbMiddle(0).bbLower(0).bbWidth(0).rsi(0).emaFast(0).emaSlow(0)
                .squeezed(false)
                .tradingHoursEnabled(tradingHoursEnabled)
                .recentTrades(new ArrayList<>())
                .build();

        activeBots.put(instrument, state);
        log.info("SCALP BOT started for {} — capital={}, leverage={}, demo={}", instrument, capital, leverage, demo);
        return state;
    }

    public void stopBot(String instrument) {
        ScalpingBotState state = activeBots.get(instrument);
        if (state == null) {
            throw new IllegalStateException("No active scalping bot for " + instrument);
        }

        cancelPendingOrders(state);
        if (state.getPhase() == ScalpingBotState.Phase.IN_POSITION) {
            closePositionMarket(state, "Bot stopped by user");
        }

        state.setActive(false);
        activeBots.remove(instrument);
        log.info("SCALP BOT stopped for {}", instrument);
    }

    public ScalpingBotState getState(String instrument) {
        return activeBots.get(instrument);
    }

    public Set<String> getActiveInstruments() {
        return activeBots.keySet();
    }

    // ─── Main loop (every 3 seconds) ────────────────────────────────

    @Scheduled(fixedDelay = 3000)
    public void tick() {
        for (Map.Entry<String, ScalpingBotState> entry : activeBots.entrySet()) {
            ScalpingBotState state = entry.getValue();
            if (!state.isActive()) continue;

            try {
                processTick(entry.getKey(), state);
            } catch (Exception e) {
                log.error("SCALP BOT error for {}: {}", entry.getKey(), e.getMessage(), e);
                state.setLastSignalReason("Error: " + e.getMessage());
            }
        }
    }

    // ─── State machine ──────────────────────────────────────────────

    private void processTick(String instrument, ScalpingBotState state) {
        updatePrices(state);
        if (state.getCurrentPrice() <= 0) return;

        switch (state.getPhase()) {
            case FLAT -> handleFlat(state);
            case ENTRY_PENDING -> handleEntryPending(state);
            case IN_POSITION -> handleInPosition(state);
            case COOLDOWN -> handleCooldown(state);
        }

        if (state.getStartedAt() != null && state.getTotalTrades() > 0) {
            long secondsRunning = Duration.between(state.getStartedAt(), Instant.now()).getSeconds();
            if (secondsRunning > 0) {
                state.setTradesPerHour((int) (state.getTotalTrades() * 3600.0 / secondsRunning));
            }
        }
    }

    // ─── FLAT: look for signals ─────────────────────────────────────

    private void handleFlat(ScalpingBotState state) {
        // === TRADING HOURS FILTER ===
        if (state.isTradingHoursEnabled()) {
            int currentHourUtc = Instant.now().atZone(ZoneOffset.UTC).getHour();
            if (currentHourUtc < TRADING_HOUR_START || currentHourUtc >= TRADING_HOUR_END) {
                state.setLastSignalReason(String.format("Outside trading hours (%02d:00 UTC). Active %02d:00-%02d:00 UTC",
                        currentHourUtc, TRADING_HOUR_START, TRADING_HOUR_END));
                state.setLastSignalAt(Instant.now());
                return;
            }
        }

        // === SPREAD CHECK ===
        double spreadPct = state.getSpread() / state.getCurrentPrice();
        if (spreadPct > MAX_SPREAD_PCT) {
            state.setLastSignalReason(String.format("Spread too wide: %.4f%% (max %.4f%%)",
                    spreadPct * 100, MAX_SPREAD_PCT * 100));
            state.setLastSignalAt(Instant.now());
            return;
        }

        // === FETCH CANDLES WITH VOLUME ===
        CandleData candleData = fetch1mCandlesWithVolume(state.getInstrument());
        if (candleData == null || candleData.closes.length < BB_PERIOD + 5) {
            state.setLastSignalReason("Not enough candle data (" + (candleData == null ? 0 : candleData.closes.length) + " bars)");
            return;
        }

        double[] closes = candleData.closes;
        double[] volumes = candleData.volumes;

        // === COMPUTE INDICATORS ===
        double[] bb = bollingerBands(closes, BB_PERIOD, BB_STD_DEV);
        double rsi = rsi(closes, RSI_PERIOD);
        double emaF = ema(closes, EMA_FAST);
        double emaS = ema(closes, EMA_SLOW);

        // BB Squeeze detection
        double bbWidth = (bb[0] - bb[2]) / bb[1]; // (upper - lower) / middle
        boolean isSqueezed = bbWidth < BB_SQUEEZE_THRESHOLD;

        state.setBbUpper(round(bb[0], 2));
        state.setBbMiddle(round(bb[1], 2));
        state.setBbLower(round(bb[2], 2));
        state.setBbWidth(round(bbWidth * 100, 3)); // as percentage
        state.setRsi(round(rsi, 2));
        state.setEmaFast(round(emaF, 2));
        state.setEmaSlow(round(emaS, 2));
        state.setSqueezed(isSqueezed);

        double price = state.getCurrentPrice();

        // === VOLUME FILTER ===
        double avgVolume = 0;
        double currentVolume = volumes[volumes.length - 1];
        for (int i = Math.max(0, volumes.length - 20); i < volumes.length - 1; i++) {
            avgVolume += volumes[i];
        }
        avgVolume /= Math.min(19, volumes.length - 1);
        boolean volumeOk = currentVolume > avgVolume * VOLUME_FILTER_MULTIPLIER;

        // === SIGNAL DETECTION ===
        String direction = null;
        String reason = null;

        // Strategy 1: BB Squeeze Breakout (highest priority)
        if (isSqueezed) {
            // Check if price is breaking out of the squeeze
            boolean breakoutUp = price > bb[0] && rsi > 50;
            boolean breakoutDown = price < bb[2] && rsi < 50;

            if (breakoutUp && volumeOk) {
                direction = "LONG";
                reason = String.format("SQUEEZE BREAKOUT UP — Price=%.2f > BB_Up=%.2f, BBW=%.3f%%, Vol=%.0f (avg=%.0f), RSI=%.1f",
                        price, bb[0], bbWidth * 100, currentVolume, avgVolume, rsi);
            } else if (breakoutDown && volumeOk) {
                direction = "SHORT";
                reason = String.format("SQUEEZE BREAKOUT DOWN — Price=%.2f < BB_Low=%.2f, BBW=%.3f%%, Vol=%.0f (avg=%.0f), RSI=%.1f",
                        price, bb[2], bbWidth * 100, currentVolume, avgVolume, rsi);
            }
        }

        // Strategy 2: BB Mean Reversion (needs volume confirmation)
        if (direction == null && volumeOk) {
            if (price <= bb[2] && rsi < 35) {
                direction = "LONG";
                reason = String.format("BB BUY — Price=%.2f <= BB_Low=%.2f, RSI=%.1f, Vol=%.0f/%.0f",
                        price, bb[2], rsi, currentVolume, avgVolume);
            } else if (price >= bb[0] && rsi > 65) {
                direction = "SHORT";
                reason = String.format("BB SELL — Price=%.2f >= BB_Up=%.2f, RSI=%.1f, Vol=%.0f/%.0f",
                        price, bb[0], rsi, currentVolume, avgVolume);
            }
        }

        // Strategy 3: EMA Micro-Momentum (needs volume confirmation)
        if (direction == null && volumeOk) {
            if (emaF > emaS && price > emaF && rsi > 45 && rsi < 60) {
                direction = "LONG";
                reason = String.format("EMA BUY — EMA5=%.2f > EMA13=%.2f, RSI=%.1f, Vol=%.0f/%.0f",
                        emaF, emaS, rsi, currentVolume, avgVolume);
            } else if (emaF < emaS && price < emaF && rsi < 55 && rsi > 40) {
                direction = "SHORT";
                reason = String.format("EMA SELL — EMA5=%.2f < EMA13=%.2f, RSI=%.1f, Vol=%.0f/%.0f",
                        emaF, emaS, rsi, currentVolume, avgVolume);
            }
        }

        if (direction == null) {
            String volStatus = volumeOk ? "OK" : String.format("LOW (%.0f < %.0f*1.5)", currentVolume, avgVolume);
            String sqStatus = isSqueezed ? " [SQUEEZE]" : "";
            state.setLastSignalReason(String.format("No signal — Price=%.2f, BB=[%.2f/%.2f/%.2f], RSI=%.1f, Vol=%s%s",
                    price, bb[2], bb[1], bb[0], rsi, volStatus, sqStatus));
            state.setLastSignalAt(Instant.now());
            return;
        }

        placeEntryOrder(state, direction, reason);
    }

    // ─── ENTRY_PENDING: check if limit order filled ─────────────────

    private void handleEntryPending(ScalpingBotState state) {
        if (state.getEntryOrderTime() != null &&
                Duration.between(state.getEntryOrderTime(), Instant.now()).toMillis() > ENTRY_TIMEOUT_MS) {
            log.info("SCALP BOT {} — Entry order timeout, cancelling {}", state.getInstrument(), state.getEntryOrderId());
            cancelOrder(state, state.getEntryOrderId());
            state.setPhase(ScalpingBotState.Phase.FLAT);
            state.setEntryOrderId(null);
            state.setLastSignalReason("Entry order timed out (30s), back to scanning...");
            state.setLastSignalAt(Instant.now());
            return;
        }

        boolean filled = checkOrderFilled(state, state.getEntryOrderId());
        if (filled) {
            double fillPrice = getActualFillPrice(state, state.getEntryOrderId());
            if (fillPrice <= 0) fillPrice = state.getEntryPrice();

            state.setEntryPrice(fillPrice);
            state.setPhase(ScalpingBotState.Phase.IN_POSITION);
            state.setPositionOpenedAt(Instant.now());

            double tp, sl;
            if ("LONG".equals(state.getDirection())) {
                tp = roundToTick(fillPrice * (1 + TP_PCT), state.getInstrument());
                sl = roundToTick(fillPrice * (1 - SL_PCT), state.getInstrument());
            } else {
                tp = roundToTick(fillPrice * (1 - TP_PCT), state.getInstrument());
                sl = roundToTick(fillPrice * (1 + SL_PCT), state.getInstrument());
            }
            state.setTakeProfit(tp);
            state.setStopLoss(sl);

            placeTpOrder(state, tp);
            placeSlOrder(state, sl);

            String msg = String.format("ENTRY FILLED %s — Price=%.2f, TP=%.2f (+%.2f%%), SL=%.2f (-%.2f%%)",
                    state.getDirection(), fillPrice, tp, TP_PCT * 100, sl, SL_PCT * 100);
            log.info("SCALP BOT {} — {}", state.getInstrument(), msg);
            state.setLastSignalReason(msg);
            state.setLastSignalAt(Instant.now());
        } else {
            state.setLastSignalReason(String.format("Waiting for entry fill %s — %s @ %.2f (%.0fs)...",
                    state.getDirection(), state.getEntryOrderId(),
                    state.getEntryPrice(),
                    state.getEntryOrderTime() != null ?
                            Duration.between(state.getEntryOrderTime(), Instant.now()).getSeconds() : 0));
        }
    }

    // ─── IN_POSITION: monitor TP/SL/timeout ─────────────────────────

    private void handleInPosition(ScalpingBotState state) {
        double price = state.getCurrentPrice();
        double pnl;
        if ("LONG".equals(state.getDirection())) {
            pnl = (price - state.getEntryPrice()) * state.getPositionSize();
        } else {
            pnl = (state.getEntryPrice() - price) * state.getPositionSize();
        }
        state.setUnrealizedPnl(round(pnl, 4));

        boolean tpFilled = state.getTpOrderId() != null && checkOrderFilled(state, state.getTpOrderId());
        boolean slFilled = state.getSlOrderId() != null && checkOrderFilled(state, state.getSlOrderId());

        if (tpFilled) {
            double exitPrice = getActualFillPrice(state, state.getTpOrderId());
            if (exitPrice <= 0) exitPrice = state.getTakeProfit();
            cancelOrder(state, state.getSlOrderId());
            recordTrade(state, exitPrice, "TP", MAKER_FEE + MAKER_FEE);
            return;
        }

        if (slFilled) {
            double exitPrice = getActualFillPrice(state, state.getSlOrderId());
            if (exitPrice <= 0) exitPrice = state.getStopLoss();
            cancelOrder(state, state.getTpOrderId());
            recordTrade(state, exitPrice, "SL", MAKER_FEE + TAKER_FEE);
            return;
        }

        // === TRAILING STOP LOGIC ===
        double pnlPct = "LONG".equals(state.getDirection())
                ? (price - state.getEntryPrice()) / state.getEntryPrice()
                : (state.getEntryPrice() - price) / state.getEntryPrice();

        if (!state.isTrailingActivated() && pnlPct >= TP_PCT * TRAILING_ACTIVATION_PCT) {
            // Activate trailing: move SL to breakeven + small buffer
            state.setTrailingActivated(true);
            double breakeven;
            if ("LONG".equals(state.getDirection())) {
                breakeven = roundToTick(state.getEntryPrice() * 1.0001, state.getInstrument()); // +0.01% above entry
            } else {
                breakeven = roundToTick(state.getEntryPrice() * 0.9999, state.getInstrument()); // -0.01% below entry
            }
            state.setTrailingStopPrice(breakeven);

            // Cancel old SL and place new one at breakeven
            cancelOrder(state, state.getSlOrderId());
            placeSlOrder(state, breakeven);
            state.setStopLoss(breakeven);

            log.info("SCALP BOT {} — TRAILING ACTIVATED: moved SL to breakeven {}", state.getInstrument(), breakeven);
        }

        if (state.isTrailingActivated()) {
            // Trail the stop higher as price moves in our favor
            double newTrailingStop;
            double trailDistance = state.getEntryPrice() * SL_PCT * 0.7; // 70% of original SL distance
            if ("LONG".equals(state.getDirection())) {
                newTrailingStop = roundToTick(price - trailDistance, state.getInstrument());
                if (newTrailingStop > state.getTrailingStopPrice()) {
                    state.setTrailingStopPrice(newTrailingStop);
                    cancelOrder(state, state.getSlOrderId());
                    placeSlOrder(state, newTrailingStop);
                    state.setStopLoss(newTrailingStop);
                }
            } else {
                newTrailingStop = roundToTick(price + trailDistance, state.getInstrument());
                if (newTrailingStop < state.getTrailingStopPrice()) {
                    state.setTrailingStopPrice(newTrailingStop);
                    cancelOrder(state, state.getSlOrderId());
                    placeSlOrder(state, newTrailingStop);
                    state.setStopLoss(newTrailingStop);
                }
            }
        }

        // === TIMEOUT: close with limit order to avoid taker fees ===
        if (state.getPositionOpenedAt() != null) {
            long holdSeconds = Duration.between(state.getPositionOpenedAt(), Instant.now()).getSeconds();
            if (holdSeconds >= MAX_HOLD_SECONDS) {
                if (pnl <= 0) {
                    // Losing trade at timeout → close with limit at current bid/ask to get maker fee
                    log.info("SCALP BOT {} — Timeout losing position ({}s, PnL={}), closing limit", state.getInstrument(), holdSeconds, round(pnl, 4));
                    cancelPendingOrders(state);
                    closePositionLimit(state, "TIMEOUT (" + holdSeconds + "s)");
                    return;
                } else if (holdSeconds >= MAX_HOLD_SECONDS * 2) {
                    // Winning but held 2x timeout → close with limit
                    log.info("SCALP BOT {} — Force timeout winning position ({}s, PnL={})", state.getInstrument(), holdSeconds, round(pnl, 4));
                    cancelPendingOrders(state);
                    closePositionLimit(state, "TIMEOUT (" + holdSeconds + "s)");
                    return;
                }
                // Winning at timeout → let trailing do its job, just log
            }
        }

        long holdSec = state.getPositionOpenedAt() != null
                ? Duration.between(state.getPositionOpenedAt(), Instant.now()).getSeconds() : 0;
        String trailInfo = state.isTrailingActivated() ? String.format(", TRAIL=%.2f", state.getTrailingStopPrice()) : "";

        state.setLastSignalReason(String.format("IN %s — Entry=%.2f, Now=%.2f, PnL=%.4f (%.3f%%), Hold=%ds, TP=%.2f, SL=%.2f%s",
                state.getDirection(), state.getEntryPrice(), price, pnl, pnlPct * 100, holdSec,
                state.getTakeProfit(), state.getStopLoss(), trailInfo));
        state.setLastSignalAt(Instant.now());
    }

    // ─── COOLDOWN: progressive wait ─────────────────────────────────

    private void handleCooldown(ScalpingBotState state) {
        if (state.getCooldownUntil() != null && Instant.now().isAfter(state.getCooldownUntil())) {
            state.setPhase(ScalpingBotState.Phase.FLAT);
            state.setLastSignalReason("Cooldown ended, scanning for signals...");
            state.setLastSignalAt(Instant.now());
            log.info("SCALP BOT {} — Cooldown ended (consecutive losses: {})", state.getInstrument(), state.getConsecutiveLosses());
        } else {
            long remaining = state.getCooldownUntil() != null
                    ? Duration.between(Instant.now(), state.getCooldownUntil()).getSeconds() : 0;
            state.setLastSignalReason(String.format("Cooldown — %ds remaining (streak: %d losses)",
                    remaining, state.getConsecutiveLosses()));
        }
    }

    // ─── Order placement ────────────────────────────────────────────

    private void placeEntryOrder(ScalpingBotState state, String direction, String reason) {
        double size = calculatePositionSize(state);
        double entryPrice;
        if ("LONG".equals(direction)) {
            entryPrice = state.getBidPrice();
        } else {
            entryPrice = state.getAskPrice();
        }

        String side = "LONG".equals(direction) ? "buy" : "sell";

        try {
            KrakenOrderRequest order = KrakenOrderRequest.builder()
                    .orderType("lmt")
                    .symbol(state.getInstrument())
                    .side(side)
                    .size(size)
                    .limitPrice(entryPrice)
                    .build();

            KrakenOrderResponse response = krakenClient.sendOrder(order, state.isDemo()).block();
            if (response != null && "success".equals(response.getResult())) {
                String orderId = response.getSendStatus() != null ? response.getSendStatus().getOrderId() : "unknown";
                state.setPhase(ScalpingBotState.Phase.ENTRY_PENDING);
                state.setDirection(direction);
                state.setEntryPrice(entryPrice);
                state.setPositionSize(size);
                state.setEntryOrderId(orderId);
                state.setEntryOrderTime(Instant.now());

                String msg = String.format("ENTRY ORDER %s — %s %.4f @ %.2f (limit/maker). %s",
                        direction, side, size, entryPrice, reason);
                log.info("SCALP BOT {} — {}", state.getInstrument(), msg);
                state.setLastSignalReason(msg);
                state.setLastSignalAt(Instant.now());
            } else {
                String error = response != null ? response.getError() : "No response";
                log.error("SCALP BOT {} — Entry order failed: {}", state.getInstrument(), error);
                state.setLastSignalReason("Entry order failed: " + error);
            }
        } catch (Exception e) {
            log.error("SCALP BOT {} — Entry order error: {}", state.getInstrument(), e.getMessage());
            state.setLastSignalReason("Entry error: " + e.getMessage());
        }
    }

    private void placeTpOrder(ScalpingBotState state, double tpPrice) {
        String side = "LONG".equals(state.getDirection()) ? "sell" : "buy";
        try {
            KrakenOrderRequest order = KrakenOrderRequest.builder()
                    .orderType("lmt")
                    .symbol(state.getInstrument())
                    .side(side)
                    .size(state.getPositionSize())
                    .limitPrice(tpPrice)
                    .reduceOnly(true)
                    .build();

            KrakenOrderResponse response = krakenClient.sendOrder(order, state.isDemo()).block();
            if (response != null && response.getSendStatus() != null) {
                state.setTpOrderId(response.getSendStatus().getOrderId());
            }
        } catch (Exception e) {
            log.error("SCALP BOT {} — TP order failed: {}", state.getInstrument(), e.getMessage());
        }
    }

    private void placeSlOrder(ScalpingBotState state, double slPrice) {
        String side = "LONG".equals(state.getDirection()) ? "sell" : "buy";
        try {
            KrakenOrderRequest order = KrakenOrderRequest.builder()
                    .orderType("stp")
                    .symbol(state.getInstrument())
                    .side(side)
                    .size(state.getPositionSize())
                    .stopPrice(slPrice)
                    .reduceOnly(true)
                    .triggerSignal("mark")
                    .build();

            KrakenOrderResponse response = krakenClient.sendOrder(order, state.isDemo()).block();
            if (response != null && response.getSendStatus() != null) {
                state.setSlOrderId(response.getSendStatus().getOrderId());
            }
        } catch (Exception e) {
            log.error("SCALP BOT {} — SL order failed: {}", state.getInstrument(), e.getMessage());
        }
    }

    // ─── Order management ───────────────────────────────────────────

    private boolean checkOrderFilled(ScalpingBotState state, String orderId) {
        if (orderId == null) return false;
        try {
            KrakenOpenOrdersResponse response = krakenClient.getOpenOrders(state.isDemo()).block();
            if (response != null && response.getOpenOrders() != null) {
                boolean stillOpen = response.getOpenOrders().stream()
                        .anyMatch(o -> orderId.equals(o.getOrderId()));
                return !stillOpen;
            }
        } catch (Exception e) {
            log.error("SCALP BOT {} — Check order failed: {}", state.getInstrument(), e.getMessage());
        }
        return false;
    }

    private double getActualFillPrice(ScalpingBotState state, String orderId) {
        if (orderId == null) return 0;
        try {
            KrakenFillsResponse response = krakenClient.getFills(state.isDemo()).block();
            if (response != null && response.getFills() != null) {
                return response.getFills().stream()
                        .filter(f -> orderId.equals(f.getOrderId()))
                        .mapToDouble(KrakenFillsResponse.Fill::getPrice)
                        .average()
                        .orElse(0);
            }
        } catch (Exception e) {
            log.error("SCALP BOT {} — Get fill price failed: {}", state.getInstrument(), e.getMessage());
        }
        return 0;
    }

    private void cancelOrder(ScalpingBotState state, String orderId) {
        if (orderId == null) return;
        try {
            krakenClient.cancelOrder(orderId, state.isDemo()).block();
        } catch (Exception e) {
            log.warn("SCALP BOT {} — Cancel order {} failed: {}", state.getInstrument(), orderId, e.getMessage());
        }
    }

    private void cancelPendingOrders(ScalpingBotState state) {
        cancelOrder(state, state.getEntryOrderId());
        cancelOrder(state, state.getTpOrderId());
        cancelOrder(state, state.getSlOrderId());
        state.setEntryOrderId(null);
        state.setTpOrderId(null);
        state.setSlOrderId(null);
    }

    // ─── Position close ─────────────────────────────────────────────

    private void closePositionLimit(ScalpingBotState state, String reason) {
        String side = "LONG".equals(state.getDirection()) ? "sell" : "buy";
        // Use ask for sell (LONG close) or bid for buy (SHORT close) to maximize fill chance as maker
        double limitPrice = "LONG".equals(state.getDirection())
                ? state.getAskPrice()  // sell at ask = aggressive limit, should fill fast
                : state.getBidPrice(); // buy at bid = aggressive limit
        try {
            KrakenOrderRequest order = KrakenOrderRequest.builder()
                    .orderType("lmt")
                    .symbol(state.getInstrument())
                    .side(side)
                    .size(state.getPositionSize())
                    .limitPrice(limitPrice)
                    .reduceOnly(true)
                    .build();
            krakenClient.sendOrder(order, state.isDemo()).block();
        } catch (Exception e) {
            log.error("SCALP BOT {} — Limit close failed, falling back to market: {}", state.getInstrument(), e.getMessage());
            closePositionMarket(state, reason);
            return;
        }

        recordTrade(state, limitPrice, reason, MAKER_FEE + MAKER_FEE); // maker both sides
    }

    private void closePositionMarket(ScalpingBotState state, String reason) {
        String side = "LONG".equals(state.getDirection()) ? "sell" : "buy";
        try {
            KrakenOrderRequest order = KrakenOrderRequest.builder()
                    .orderType("mkt")
                    .symbol(state.getInstrument())
                    .side(side)
                    .size(state.getPositionSize())
                    .reduceOnly(true)
                    .build();
            krakenClient.sendOrder(order, state.isDemo()).block();
        } catch (Exception e) {
            log.error("SCALP BOT {} — Market close failed: {}", state.getInstrument(), e.getMessage());
        }

        recordTrade(state, state.getCurrentPrice(), reason, MAKER_FEE + TAKER_FEE);
    }

    // ─── Trade recording with progressive cooldown ──────────────────

    private void recordTrade(ScalpingBotState state, double exitPrice, String exitReason, double totalFeeRate) {
        double rawPnl;
        if ("LONG".equals(state.getDirection())) {
            rawPnl = (exitPrice - state.getEntryPrice()) * state.getPositionSize();
        } else {
            rawPnl = (state.getEntryPrice() - exitPrice) * state.getPositionSize();
        }

        double fees = state.getEntryPrice() * state.getPositionSize() * totalFeeRate;
        double netPnl = round(rawPnl - fees, 4);

        double pnlPct = "LONG".equals(state.getDirection())
                ? (exitPrice - state.getEntryPrice()) / state.getEntryPrice() * 100
                : (state.getEntryPrice() - exitPrice) / state.getEntryPrice() * 100;

        long holdDuration = state.getPositionOpenedAt() != null
                ? Duration.between(state.getPositionOpenedAt(), Instant.now()).getSeconds() : 0;

        ScalpingBotTrade trade = ScalpingBotTrade.builder()
                .direction(state.getDirection())
                .instrument(state.getInstrument())
                .entryPrice(state.getEntryPrice())
                .exitPrice(exitPrice)
                .size(state.getPositionSize())
                .pnl(netPnl)
                .pnlPercent(round(pnlPct, 3))
                .fees(round(fees, 4))
                .exitReason(exitReason)
                .openedAt(state.getPositionOpenedAt())
                .closedAt(Instant.now())
                .durationSeconds(holdDuration)
                .build();

        List<ScalpingBotTrade> trades = state.getRecentTrades();
        if (trades == null) trades = new ArrayList<>();
        trades.add(0, trade);
        if (trades.size() > 100) trades = new ArrayList<>(trades.subList(0, 100));

        state.setTotalTrades(state.getTotalTrades() + 1);
        if (netPnl > 0) {
            state.setWins(state.getWins() + 1);
            state.setConsecutiveLosses(0); // reset on win
        } else {
            state.setLosses(state.getLosses() + 1);
            state.setConsecutiveLosses(state.getConsecutiveLosses() + 1);
        }
        state.setWinRate(state.getTotalTrades() > 0
                ? round((double) state.getWins() / state.getTotalTrades() * 100, 1) : 0);
        state.setRealizedPnl(round(state.getRealizedPnl() + netPnl, 4));
        if (netPnl > state.getBestTrade()) state.setBestTrade(netPnl);
        if (netPnl < state.getWorstTrade()) state.setWorstTrade(netPnl);
        state.setRecentTrades(trades);
        state.setLastTradeAt(Instant.now());

        // Reset position
        state.setUnrealizedPnl(0);
        state.setEntryPrice(0);
        state.setPositionSize(0);
        state.setStopLoss(0);
        state.setTakeProfit(0);
        state.setEntryOrderId(null);
        state.setTpOrderId(null);
        state.setSlOrderId(null);
        state.setPositionOpenedAt(null);
        state.setDirection("FLAT");
        state.setTrailingStopPrice(0);
        state.setTrailingActivated(false);

        // === PROGRESSIVE COOLDOWN ===
        int cooldownMs;
        if (netPnl > 0) {
            cooldownMs = COOLDOWN_WIN_MS;
        } else {
            int losses = state.getConsecutiveLosses();
            if (losses >= 3) {
                cooldownMs = COOLDOWN_3_LOSS_MS;
            } else if (losses >= 2) {
                cooldownMs = COOLDOWN_2_LOSS_MS;
            } else {
                cooldownMs = COOLDOWN_1_LOSS_MS;
            }
        }

        state.setPhase(ScalpingBotState.Phase.COOLDOWN);
        state.setCooldownUntil(Instant.now().plusMillis(cooldownMs));

        String msg = String.format("CLOSED %s — Entry=%.2f, Exit=%.2f, PnL=%.4f$ (%.3f%%), Fees=%.4f$, Reason=%s, Hold=%ds, Cooldown=%ds",
                trade.getDirection(), trade.getEntryPrice(), trade.getExitPrice(),
                netPnl, pnlPct, fees, exitReason, holdDuration, cooldownMs / 1000);
        log.info("SCALP BOT {} — {} | Total: PnL={}, W/L={}/{}, WR={}%, Streak={}",
                state.getInstrument(), msg, state.getRealizedPnl(),
                state.getWins(), state.getLosses(), state.getWinRate(), state.getConsecutiveLosses());
        state.setLastSignalReason(msg);
        state.setLastSignalAt(Instant.now());
    }

    // ─── Price fetching ─────────────────────────────────────────────

    private void updatePrices(ScalpingBotState state) {
        try {
            KrakenTickerResponse response = krakenClient.getTickers(state.isDemo()).block();
            if (response != null && response.getTickers() != null) {
                response.getTickers().stream()
                        .filter(t -> state.getInstrument().equals(t.getSymbol()))
                        .findFirst()
                        .ifPresent(ticker -> {
                            state.setCurrentPrice(ticker.getLast() != null ? ticker.getLast() : 0);
                            state.setBidPrice(ticker.getBid() != null ? ticker.getBid() : 0);
                            state.setAskPrice(ticker.getAsk() != null ? ticker.getAsk() : 0);
                            if (state.getBidPrice() > 0 && state.getAskPrice() > 0) {
                                state.setSpread(round(state.getAskPrice() - state.getBidPrice(), 4));
                            }
                        });
            }
        } catch (Exception e) {
            log.error("SCALP BOT {} — Price fetch failed: {}", state.getInstrument(), e.getMessage());
        }
    }

    // ─── OHLC data with volume ──────────────────────────────────────

    private record CandleData(double[] closes, double[] volumes) {}

    @SuppressWarnings("unchecked")
    private CandleData fetch1mCandlesWithVolume(String instrument) {
        try {
            var ohlcData = krakenClient.getOhlc(instrument, 120).block();
            if (ohlcData == null || !ohlcData.containsKey("candles")) return null;

            List<Map<String, Object>> candles = (List<Map<String, Object>>) ohlcData.get("candles");
            if (candles == null || candles.isEmpty()) return null;

            double[] closes = new double[candles.size()];
            double[] volumes = new double[candles.size()];
            for (int i = 0; i < candles.size(); i++) {
                closes[i] = Double.parseDouble(candles.get(i).get("close").toString());
                Object vol = candles.get(i).get("volume");
                volumes[i] = vol != null ? Double.parseDouble(vol.toString()) : 0;
            }
            return new CandleData(closes, volumes);
        } catch (Exception e) {
            log.error("SCALP BOT {} — OHLC fetch failed: {}", instrument, e.getMessage());
            return null;
        }
    }

    // ─── Technical indicators ───────────────────────────────────────

    private double[] bollingerBands(double[] closes, int period, double numStdDev) {
        int len = closes.length;
        if (len < period) return new double[]{0, 0, 0};

        double sum = 0;
        for (int i = len - period; i < len; i++) sum += closes[i];
        double sma = sum / period;

        double sqSum = 0;
        for (int i = len - period; i < len; i++) sqSum += Math.pow(closes[i] - sma, 2);
        double stdDev = Math.sqrt(sqSum / period);

        return new double[]{sma + numStdDev * stdDev, sma, sma - numStdDev * stdDev};
    }

    private double rsi(double[] closes, int period) {
        if (closes.length < period + 1) return 50;
        double gainSum = 0, lossSum = 0;
        for (int i = closes.length - period; i < closes.length; i++) {
            double change = closes[i] - closes[i - 1];
            if (change > 0) gainSum += change; else lossSum += Math.abs(change);
        }
        double avgGain = gainSum / period;
        double avgLoss = lossSum / period;
        if (avgLoss == 0) return 100;
        return 100 - (100 / (1 + avgGain / avgLoss));
    }

    private double ema(double[] closes, int period) {
        if (closes.length < period) return closes[closes.length - 1];
        double multiplier = 2.0 / (period + 1);
        int start = closes.length - Math.min(closes.length, period * 3);
        double ema = 0;
        for (int i = start; i < start + period && i < closes.length; i++) ema += closes[i];
        ema /= period;
        for (int i = start + period; i < closes.length; i++) ema = (closes[i] - ema) * multiplier + ema;
        return ema;
    }

    // ─── Sizing & rounding ──────────────────────────────────────────

    private double calculatePositionSize(ScalpingBotState state) {
        double notional = state.getCapital() * state.getLeverage();
        return roundSize(notional / state.getCurrentPrice(), state.getInstrument());
    }

    private double roundSize(double size, String instrument) {
        if (instrument.contains("XBT")) return round(size, 4);
        if (instrument.contains("ETH")) return round(size, 3);
        return round(size, 4);
    }

    private double roundToTick(double price, String instrument) {
        if (instrument.contains("XBT")) return Math.round(price * 10.0) / 10.0;
        if (instrument.contains("ETH")) return round(price, 1);
        return round(price, 2);
    }

    private double round(double value, int decimals) {
        return BigDecimal.valueOf(value).setScale(decimals, RoundingMode.HALF_UP).doubleValue();
    }
}
