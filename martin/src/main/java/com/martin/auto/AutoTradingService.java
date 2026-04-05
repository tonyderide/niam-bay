package com.martin.auto;

import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenOrderRequest;
import com.martin.kraken.dto.KrakenTickerResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.ta4j.core.BarSeries;
import org.ta4j.core.BaseBarSeriesBuilder;
import org.ta4j.core.num.DecimalNum;
import org.ta4j.core.indicators.EMAIndicator;
import org.ta4j.core.indicators.MACDIndicator;
import org.ta4j.core.indicators.RSIIndicator;
import org.ta4j.core.indicators.ATRIndicator;
import org.ta4j.core.indicators.adx.ADXIndicator;
import org.ta4j.core.indicators.helpers.ClosePriceIndicator;
import org.ta4j.core.indicators.helpers.VolumeIndicator;
import org.ta4j.core.indicators.SMAIndicator;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class AutoTradingService {

    private static final Logger log = LoggerFactory.getLogger(AutoTradingService.class);

    // DCA safety order config
    private static final double[] SAFETY_ORDER_OFFSETS = {0.01, 0.025, 0.05};
    private static final double SAFETY_ORDER_MULTIPLIER = 1.5;
    private static final int MAX_SAFETY_ORDERS = 3;
    private static final long MIN_DCA_INTERVAL_MS = 300_000; // 5 min between DCA orders

    // Risk management — R:R 2:1
    private static final double ATR_SL_MULTIPLIER = 2.0;
    private static final double ATR_TP_MULTIPLIER = 4.0; // was 3.0, now 4.0 for R:R 2:1
    private static final double TRAILING_TP_ACTIVATION_PCT = 0.02;
    private static final double TRAILING_TP_DISTANCE_PCT = 0.01;
    private static final double MAX_DRAWDOWN_PCT = 0.10;

    // Trading hours (UTC)
    private static final int TRADING_HOUR_START = 8;
    private static final int TRADING_HOUR_END = 22;

    // Cooldown after loss
    private static final long COOLDOWN_AFTER_LOSS_MS = 1_800_000; // 30 min

    // Volume filter
    private static final double VOLUME_FILTER_MULTIPLIER = 1.5;

    private final KrakenFuturesRestClient krakenClient;
    private final ConcurrentHashMap<String, AutoBotState> activeBots = new ConcurrentHashMap<>();

    // ─── Public API ────────────────────────────────────────────────────

    public AutoBotState startBot(String instrument, double capital, double leverage, boolean demo) {
        if (activeBots.containsKey(instrument)) {
            throw new IllegalStateException("Auto bot already active for " + instrument);
        }

        AutoBotState state = AutoBotState.builder()
                .instrument(instrument)
                .active(true)
                .demo(demo)
                .capital(capital)
                .leverage(leverage)
                .direction("FLAT")
                .entryPrice(0).currentPrice(0).stopLoss(0).takeProfit(0)
                .trailingTpHighest(0).safetyOrderCount(0).averageEntryPrice(0)
                .positionSize(0).unrealizedPnl(0).realizedPnl(0)
                .startedAt(Instant.now())
                .lastSignalAt(null)
                .lastSignalReason("Bot started, waiting for signal...")
                .totalTrades(0).wins(0).losses(0).winRate(0)
                .recentTrades(new ArrayList<>())
                .build();

        activeBots.put(instrument, state);
        log.info("AUTO BOT started for {} — capital={}, leverage={}, demo={}", instrument, capital, leverage, demo);
        return state;
    }

    public void stopBot(String instrument) {
        AutoBotState state = activeBots.get(instrument);
        if (state == null) throw new IllegalStateException("No active auto bot for " + instrument);

        if (!"FLAT".equals(state.getDirection())) {
            closePosition(state, state.getCurrentPrice(), "Bot stopped by user");
        }

        state.setActive(false);
        activeBots.remove(instrument);
        log.info("AUTO BOT stopped for {}", instrument);
    }

    public AutoBotState getState(String instrument) {
        return activeBots.get(instrument);
    }

    public Set<String> getActiveInstruments() {
        return activeBots.keySet();
    }

    // ─── Scheduled polling ─────────────────────────────────────────────

    @Scheduled(fixedDelay = 15000)
    public void pollSignals() {
        for (Map.Entry<String, AutoBotState> entry : activeBots.entrySet()) {
            AutoBotState state = entry.getValue();
            if (!state.isActive()) continue;

            try {
                processSignal(entry.getKey(), state);
            } catch (Exception e) {
                log.error("AUTO BOT error for {}: {}", entry.getKey(), e.getMessage(), e);
                state.setLastSignalReason("Error: " + e.getMessage());
            }
        }
    }

    // ─── Core signal processing ────────────────────────────────────────

    private void processSignal(String instrument, AutoBotState state) {
        double currentPrice = fetchCurrentPrice(instrument, state.isDemo());
        if (currentPrice <= 0) return;
        state.setCurrentPrice(currentPrice);

        // Cooldown check (after loss)
        if ("FLAT".equals(state.getDirection()) && state.getCooldownUntil() != null
                && Instant.now().isBefore(state.getCooldownUntil())) {
            long remaining = Duration.between(Instant.now(), state.getCooldownUntil()).getSeconds();
            state.setLastSignalReason(String.format("Post-loss cooldown — %ds remaining", remaining));
            state.setLastSignalAt(Instant.now());
            return;
        }

        // Max drawdown check
        if (!"FLAT".equals(state.getDirection())) {
            double drawdown = -state.getUnrealizedPnl();
            if (drawdown > state.getCapital() * MAX_DRAWDOWN_PCT) {
                log.warn("AUTO BOT {} — MAX DRAWDOWN! Closing. Drawdown={}", instrument, round(drawdown, 2));
                closePosition(state, currentPrice, "Max drawdown reached (" + round(drawdown, 2) + "$)");
                state.setActive(false);
                activeBots.remove(instrument);
                return;
            }
        }

        // Build 1h series
        BarSeries series1h = fetchAndBuildSeries(instrument, 60); // 1h bars
        if (series1h == null || series1h.getBarCount() < 30) {
            state.setLastSignalReason("Not enough 1h candle data (" + (series1h == null ? 0 : series1h.getBarCount()) + " bars)");
            return;
        }

        int last = series1h.getEndIndex();
        ClosePriceIndicator closePrice = new ClosePriceIndicator(series1h);

        // 1h Indicators
        EMAIndicator ema9 = new EMAIndicator(closePrice, 9);
        EMAIndicator ema21 = new EMAIndicator(closePrice, 21);
        RSIIndicator rsi = new RSIIndicator(closePrice, 14);
        MACDIndicator macd = new MACDIndicator(closePrice, 12, 26);
        EMAIndicator macdSignal = new EMAIndicator(macd, 9);
        ADXIndicator adx = new ADXIndicator(series1h, 14);
        ATRIndicator atr = new ATRIndicator(series1h, 14);

        double ema9Val = ema9.getValue(last).doubleValue();
        double ema21Val = ema21.getValue(last).doubleValue();
        double rsiVal = rsi.getValue(last).doubleValue();
        double macdVal = macd.getValue(last).doubleValue();
        double macdSigVal = macdSignal.getValue(last).doubleValue();
        double adxVal = adx.getValue(last).doubleValue();
        double atrVal = atr.getValue(last).doubleValue();

        // Volume on 1h
        VolumeIndicator volumeInd = new VolumeIndicator(series1h);
        SMAIndicator volumeSma = new SMAIndicator(volumeInd, 20);
        double currentVol = volumeInd.getValue(last).doubleValue();
        double avgVol = volumeSma.getValue(last).doubleValue();
        boolean volumeOk = currentVol > avgVol * VOLUME_FILTER_MULTIPLIER;

        String indicatorSummary = String.format(
                "EMA9=%.2f, EMA21=%.2f, RSI=%.2f, MACD=%.6f, ADX=%.2f, ATR=%.4f, Vol=%s",
                ema9Val, ema21Val, rsiVal, macdVal, adxVal, atrVal,
                volumeOk ? "OK" : "LOW");

        // If FLAT → check for entry
        if ("FLAT".equals(state.getDirection())) {
            evaluateEntry(state, currentPrice, ema9Val, ema21Val, rsiVal, macdVal, macdSigVal,
                    adxVal, atrVal, volumeOk, indicatorSummary);
            return;
        }

        // If in position → manage
        managePosition(state, currentPrice, atrVal, indicatorSummary);
    }

    // ─── Entry logic with all improvements ──────────────────────────────

    private void evaluateEntry(AutoBotState state, double currentPrice,
                                double ema9, double ema21, double rsi,
                                double macdVal, double macdSig, double adx, double atr,
                                boolean volumeOk, String summary) {

        // === TRADING HOURS FILTER ===
        int currentHourUtc = Instant.now().atZone(ZoneOffset.UTC).getHour();
        if (currentHourUtc < TRADING_HOUR_START || currentHourUtc >= TRADING_HOUR_END) {
            state.setLastSignalReason(String.format("Outside trading hours (%02d UTC). Active %02d-%02d UTC. %s",
                    currentHourUtc, TRADING_HOUR_START, TRADING_HOUR_END, summary));
            state.setLastSignalAt(Instant.now());
            return;
        }

        // ADX filter
        if (adx < 20) {
            state.setLastSignalReason("No trend (ADX=" + round(adx, 2) + " < 20). " + summary);
            state.setLastSignalAt(Instant.now());
            return;
        }

        // === VOLUME FILTER ===
        if (!volumeOk) {
            state.setLastSignalReason("Volume too low, waiting for confirmation. " + summary);
            state.setLastSignalAt(Instant.now());
            return;
        }

        // === MULTI-TIMEFRAME: check 4h trend ===
        String trend4h = get4hTrend(state.getInstrument());

        // RSI thresholds: 52/48 (was 55/45)
        boolean longSignal = ema9 > ema21 && rsi > 52 && macdVal > macdSig;
        boolean shortSignal = ema9 < ema21 && rsi < 48 && macdVal < macdSig;

        // Multi-timeframe filter: 1h signal must align with 4h trend
        if (longSignal && "BEARISH".equals(trend4h)) {
            state.setLastSignalReason("LONG signal BUT 4h trend is BEARISH — skipping. " + summary);
            state.setLastSignalAt(Instant.now());
            return;
        }
        if (shortSignal && "BULLISH".equals(trend4h)) {
            state.setLastSignalReason("SHORT signal BUT 4h trend is BULLISH — skipping. " + summary);
            state.setLastSignalAt(Instant.now());
            return;
        }

        if (!longSignal && !shortSignal) {
            state.setLastSignalReason("No confirmed signal. 4h=" + trend4h + ". " + summary);
            state.setLastSignalAt(Instant.now());
            return;
        }

        String direction = longSignal ? "LONG" : "SHORT";
        double baseSize = calculateBasePositionSize(state, currentPrice);

        // R:R 2:1: ATR*2 SL, ATR*4 TP
        double sl, tp;
        if ("LONG".equals(direction)) {
            sl = currentPrice - (atr * ATR_SL_MULTIPLIER);
            tp = currentPrice + (atr * ATR_TP_MULTIPLIER);
        } else {
            sl = currentPrice + (atr * ATR_SL_MULTIPLIER);
            tp = currentPrice - (atr * ATR_TP_MULTIPLIER);
        }
        sl = roundToTick(sl, state.getInstrument());
        tp = roundToTick(tp, state.getInstrument());

        String reason = String.format("ENTRY %s — Price=%.4f, SL=%.4f, TP=%.4f (R:R=2:1), Size=%.4f, ADX=%.2f, 4h=%s. %s",
                direction, currentPrice, sl, tp, baseSize, adx, trend4h, summary);

        log.info("AUTO BOT {} — {}", state.getInstrument(), reason);
        placeMarketOrder(state, direction, baseSize);

        state.setDirection(direction);
        state.setEntryPrice(currentPrice);
        state.setAverageEntryPrice(currentPrice);
        state.setPositionSize(baseSize);
        state.setStopLoss(sl);
        state.setTakeProfit(tp);
        state.setTrailingTpHighest(currentPrice);
        state.setSafetyOrderCount(0);
        state.setLastSafetyOrderAt(null);
        state.setLastSignalReason(reason);
        state.setLastSignalAt(Instant.now());
    }

    // ─── Multi-timeframe: 4h trend check ────────────────────────────────

    private String get4hTrend(String instrument) {
        try {
            BarSeries series4h = fetchAndBuildSeries(instrument, 240); // 4h bars
            if (series4h == null || series4h.getBarCount() < 15) return "NEUTRAL";

            int last = series4h.getEndIndex();
            ClosePriceIndicator cp = new ClosePriceIndicator(series4h);
            EMAIndicator ema9_4h = new EMAIndicator(cp, 9);
            EMAIndicator ema21_4h = new EMAIndicator(cp, 21);

            double e9 = ema9_4h.getValue(last).doubleValue();
            double e21 = ema21_4h.getValue(last).doubleValue();

            if (e9 > e21 * 1.001) return "BULLISH";  // 0.1% margin
            if (e9 < e21 * 0.999) return "BEARISH";
            return "NEUTRAL";
        } catch (Exception e) {
            log.warn("AUTO BOT — Failed to get 4h trend: {}", e.getMessage());
            return "NEUTRAL";
        }
    }

    // ─── Position management ───────────────────────────────────────────

    private void managePosition(AutoBotState state, double currentPrice, double atr, String summary) {
        String direction = state.getDirection();
        double avgEntry = state.getAverageEntryPrice();
        double priceDiffPct = "LONG".equals(direction)
                ? (currentPrice - avgEntry) / avgEntry
                : (avgEntry - currentPrice) / avgEntry;

        double unrealized = "LONG".equals(direction)
                ? (currentPrice - avgEntry) * state.getPositionSize()
                : (avgEntry - currentPrice) * state.getPositionSize();
        state.setUnrealizedPnl(round(unrealized, 4));

        // 1. Stop loss
        boolean slHit = "LONG".equals(direction) ? currentPrice <= state.getStopLoss() : currentPrice >= state.getStopLoss();
        if (slHit) {
            String reason = String.format("STOP LOSS — Price=%.4f, SL=%.4f, PnL=%.4f. %s",
                    currentPrice, state.getStopLoss(), unrealized, summary);
            log.warn("AUTO BOT {} — {}", state.getInstrument(), reason);
            closePosition(state, currentPrice, reason);
            return;
        }

        // 2. Trailing TP
        if (priceDiffPct >= TRAILING_TP_ACTIVATION_PCT) {
            if ("LONG".equals(direction)) {
                if (currentPrice > state.getTrailingTpHighest()) state.setTrailingTpHighest(currentPrice);
                double trailSl = state.getTrailingTpHighest() * (1 - TRAILING_TP_DISTANCE_PCT);
                if (currentPrice <= trailSl) {
                    closePosition(state, currentPrice, String.format("TRAILING TP — High=%.4f, Trail=%.4f, PnL=%.4f",
                            state.getTrailingTpHighest(), trailSl, unrealized));
                    return;
                }
            } else {
                if (currentPrice < state.getTrailingTpHighest() || state.getTrailingTpHighest() == state.getEntryPrice())
                    state.setTrailingTpHighest(currentPrice);
                double trailSl = state.getTrailingTpHighest() * (1 + TRAILING_TP_DISTANCE_PCT);
                if (currentPrice >= trailSl) {
                    closePosition(state, currentPrice, String.format("TRAILING TP — Low=%.4f, Trail=%.4f, PnL=%.4f",
                            state.getTrailingTpHighest(), trailSl, unrealized));
                    return;
                }
            }
            state.setLastSignalReason(String.format("Trailing active — Highest=%.4f, PnL=%.4f. %s",
                    state.getTrailingTpHighest(), unrealized, summary));
            state.setLastSignalAt(Instant.now());
            return;
        }

        // 3. Fixed TP
        boolean tpHit = "LONG".equals(direction) ? currentPrice >= state.getTakeProfit() : currentPrice <= state.getTakeProfit();
        if (tpHit) {
            closePosition(state, currentPrice, String.format("TAKE PROFIT — Price=%.4f, TP=%.4f, PnL=%.4f",
                    currentPrice, state.getTakeProfit(), unrealized));
            return;
        }

        // 4. DCA with timing filter (minimum 5 min between orders)
        if (priceDiffPct < 0 && state.getSafetyOrderCount() < MAX_SAFETY_ORDERS) {
            double absLossPct = Math.abs(priceDiffPct);
            int nextSO = state.getSafetyOrderCount();

            if (nextSO < SAFETY_ORDER_OFFSETS.length && absLossPct >= SAFETY_ORDER_OFFSETS[nextSO]) {
                // === DCA TIMING FILTER ===
                boolean canDca = state.getLastSafetyOrderAt() == null ||
                        Duration.between(state.getLastSafetyOrderAt(), Instant.now()).toMillis() >= MIN_DCA_INTERVAL_MS;

                if (canDca) {
                    executeSafetyOrder(state, currentPrice, nextSO);
                    return;
                } else {
                    long waitSec = (MIN_DCA_INTERVAL_MS - Duration.between(state.getLastSafetyOrderAt(), Instant.now()).toMillis()) / 1000;
                    state.setLastSignalReason(String.format("DCA #%d ready but cooldown — %ds until next SO allowed. %s",
                            nextSO + 1, waitSec, summary));
                    state.setLastSignalAt(Instant.now());
                    return;
                }
            }
        }

        state.setLastSignalReason(String.format("In %s — Price=%.4f, Avg=%.4f, PnL=%.4f (%.2f%%). %s",
                direction, currentPrice, avgEntry, unrealized, priceDiffPct * 100, summary));
        state.setLastSignalAt(Instant.now());
    }

    // ─── DCA Safety Orders ─────────────────────────────────────────────

    private void executeSafetyOrder(AutoBotState state, double currentPrice, int soIndex) {
        double baseSize = calculateBasePositionSize(state, currentPrice);
        double soSize = roundSize(baseSize * Math.pow(SAFETY_ORDER_MULTIPLIER, soIndex + 1), state.getInstrument());

        log.info("AUTO BOT {} — SAFETY ORDER #{} — Price={}, Size={}", state.getInstrument(), soIndex + 1, currentPrice, soSize);
        placeMarketOrder(state, state.getDirection(), soSize);

        double totalCost = state.getAverageEntryPrice() * state.getPositionSize() + currentPrice * soSize;
        double totalSize = state.getPositionSize() + soSize;
        double newAvg = totalCost / totalSize;

        state.setAverageEntryPrice(round(newAvg, 6));
        state.setPositionSize(round(totalSize, 6));
        state.setSafetyOrderCount(soIndex + 1);
        state.setLastSafetyOrderAt(Instant.now()); // timing tracker

        double slDistance = Math.abs(state.getEntryPrice() - state.getStopLoss());
        if ("LONG".equals(state.getDirection())) {
            state.setStopLoss(roundToTick(newAvg - slDistance, state.getInstrument()));
        } else {
            state.setStopLoss(roundToTick(newAvg + slDistance, state.getInstrument()));
        }

        state.setLastSignalReason(String.format("SO #%d — NewAvg=%.4f, TotalSize=%.4f", soIndex + 1, newAvg, totalSize));
        state.setLastSignalAt(Instant.now());
    }

    // ─── Close position with cooldown ───────────────────────────────────

    private void closePosition(AutoBotState state, double exitPrice, String reason) {
        double pnl = "LONG".equals(state.getDirection())
                ? (exitPrice - state.getAverageEntryPrice()) * state.getPositionSize()
                : (state.getAverageEntryPrice() - exitPrice) * state.getPositionSize();
        pnl = round(pnl, 4);

        String closeSide = "LONG".equals(state.getDirection()) ? "sell" : "buy";
        try {
            KrakenOrderRequest closeOrder = KrakenOrderRequest.builder()
                    .orderType("mkt").symbol(state.getInstrument())
                    .side(closeSide).size(state.getPositionSize()).reduceOnly(true).build();
            krakenClient.sendOrder(closeOrder, state.isDemo()).block();
        } catch (Exception e) {
            log.error("AUTO BOT {} — Close order failed: {}", state.getInstrument(), e.getMessage());
        }

        AutoBotTrade trade = AutoBotTrade.builder()
                .direction(state.getDirection()).instrument(state.getInstrument())
                .entryPrice(state.getAverageEntryPrice()).exitPrice(exitPrice)
                .pnl(pnl).size(state.getPositionSize())
                .openedAt(state.getLastSignalAt() != null ? state.getLastSignalAt() : state.getStartedAt())
                .closedAt(Instant.now()).build();

        List<AutoBotTrade> trades = state.getRecentTrades();
        if (trades == null) trades = new ArrayList<>();
        trades.add(0, trade);
        if (trades.size() > 50) trades = new ArrayList<>(trades.subList(0, 50));

        state.setTotalTrades(state.getTotalTrades() + 1);
        if (pnl > 0) state.setWins(state.getWins() + 1);
        else state.setLosses(state.getLosses() + 1);
        state.setWinRate(state.getTotalTrades() > 0 ? round((double) state.getWins() / state.getTotalTrades() * 100, 2) : 0);

        state.setRealizedPnl(round(state.getRealizedPnl() + pnl, 4));
        state.setUnrealizedPnl(0);
        state.setRecentTrades(trades);
        state.setLastTradeAt(Instant.now());

        // Reset position
        state.setDirection("FLAT");
        state.setEntryPrice(0);
        state.setAverageEntryPrice(0);
        state.setPositionSize(0);
        state.setStopLoss(0);
        state.setTakeProfit(0);
        state.setTrailingTpHighest(0);
        state.setSafetyOrderCount(0);
        state.setLastSafetyOrderAt(null);

        // === COOLDOWN AFTER LOSS ===
        if (pnl < 0) {
            state.setCooldownUntil(Instant.now().plusMillis(COOLDOWN_AFTER_LOSS_MS));
            log.info("AUTO BOT {} — Loss cooldown activated (30min)", state.getInstrument());
        } else {
            state.setCooldownUntil(null);
        }

        state.setLastSignalReason(reason + String.format(" — Closed PnL=%.4f", pnl));
        state.setLastSignalAt(Instant.now());

        log.info("AUTO BOT {} — Closed. PnL={}, Total={}, W/L={}/{}, WR={}%",
                state.getInstrument(), pnl, state.getRealizedPnl(), state.getWins(), state.getLosses(), state.getWinRate());
    }

    // ─── Kraken interaction ────────────────────────────────────────────

    private double fetchCurrentPrice(String instrument, boolean demo) {
        try {
            KrakenTickerResponse response = krakenClient.getTickers(demo).block();
            if (response != null && response.getTickers() != null) {
                return response.getTickers().stream()
                        .filter(t -> instrument.equals(t.getSymbol()))
                        .findFirst()
                        .map(KrakenTickerResponse.Ticker::getLast)
                        .orElse(0.0);
            }
        } catch (Exception e) {
            log.error("Failed to fetch price for {}: {}", instrument, e.getMessage());
        }
        return 0;
    }

    private void placeMarketOrder(AutoBotState state, String direction, double size) {
        String side = "LONG".equals(direction) ? "buy" : "sell";
        try {
            KrakenOrderRequest order = KrakenOrderRequest.builder()
                    .orderType("mkt").symbol(state.getInstrument()).side(side).size(size).build();
            krakenClient.sendOrder(order, state.isDemo()).block();
            log.info("AUTO BOT {} — Order: {} {}", state.getInstrument(), side, size);
        } catch (Exception e) {
            log.error("AUTO BOT {} — Order failed: {}", state.getInstrument(), e.getMessage());
            throw new RuntimeException("Order failed: " + e.getMessage(), e);
        }
    }

    // ─── OHLC & ta4j series building (configurable bar size) ────────────

    @SuppressWarnings("unchecked")
    private BarSeries fetchAndBuildSeries(String instrument, int barSizeMinutes) {
        try {
            // Fetch enough 1m candles for the desired bar count
            int minutesNeeded = barSizeMinutes * 60; // 60 bars of barSize
            var ohlcData = krakenClient.getOhlc(instrument, minutesNeeded).block();

            if (ohlcData == null || !ohlcData.containsKey("candles")) return null;

            List<Map<String, Object>> candles = (List<Map<String, Object>>) ohlcData.get("candles");
            if (candles == null || candles.size() < barSizeMinutes) return null;

            BarSeries series = new BaseBarSeriesBuilder()
                    .withName("auto-" + instrument + "-" + barSizeMinutes + "m")
                    .withNumTypeOf(DecimalNum.class)
                    .build();

            for (int i = 0; i + barSizeMinutes <= candles.size(); i += barSizeMinutes) {
                double open = Double.parseDouble(candles.get(i).get("open").toString());
                double high = Double.MIN_VALUE;
                double low = Double.MAX_VALUE;
                double close = 0;
                double volume = 0;
                long time = 0;

                for (int j = i; j < i + barSizeMinutes; j++) {
                    Map<String, Object> c = candles.get(j);
                    double h = Double.parseDouble(c.get("high").toString());
                    double l = Double.parseDouble(c.get("low").toString());
                    close = Double.parseDouble(c.get("close").toString());
                    if (h > high) high = h;
                    if (l < low) low = l;
                    Object vol = c.get("volume");
                    if (vol != null) volume += Double.parseDouble(vol.toString());
                    if (c.containsKey("time")) time = Long.parseLong(c.get("time").toString());
                }

                ZonedDateTime barTime = time > 0
                        ? Instant.ofEpochSecond(time).atZone(ZoneOffset.UTC)
                        : ZonedDateTime.now().minusMinutes((long)(candles.size() - i));

                series.addBar(Duration.ofMinutes(barSizeMinutes), barTime,
                        DecimalNum.valueOf(open), DecimalNum.valueOf(high),
                        DecimalNum.valueOf(low), DecimalNum.valueOf(close),
                        DecimalNum.valueOf(volume));
            }

            return series;
        } catch (Exception e) {
            log.error("Failed to build {}m series for {}: {}", barSizeMinutes, instrument, e.getMessage());
            return null;
        }
    }

    // ─── Sizing & rounding ───────────────────────────────────────────────

    private double calculateBasePositionSize(AutoBotState state, double currentPrice) {
        double dcaReserve = 1 + SAFETY_ORDER_MULTIPLIER + Math.pow(SAFETY_ORDER_MULTIPLIER, 2) + Math.pow(SAFETY_ORDER_MULTIPLIER, 3);
        return roundSize((state.getCapital() * state.getLeverage()) / dcaReserve / currentPrice, state.getInstrument());
    }

    private double roundSize(double size, String instrument) {
        if (instrument.contains("XBT")) return round(size, 4);
        if (instrument.contains("ETH")) return round(size, 3);
        return round(size, 4);
    }

    private double roundToTick(double price, String instrument) {
        if (instrument.contains("XBT")) return Math.round(price);
        if (instrument.contains("ETH")) return round(price, 1);
        return round(price, 2);
    }

    private double round(double value, int decimals) {
        return BigDecimal.valueOf(value).setScale(decimals, RoundingMode.HALF_UP).doubleValue();
    }
}
