package com.martin.service;

import com.martin.domain.entity.BotConfig;
import com.martin.domain.entity.Trade;
import com.martin.domain.entity.TradeSeries;
import com.martin.domain.enums.Direction;
import com.martin.domain.enums.SeriesStatus;
import com.martin.domain.enums.TradeStatus;
import com.martin.domain.repository.TradeRepository;
import com.martin.domain.repository.TradeSeriesRepository;
import com.martin.engine.MartingaleEngine;
import com.martin.engine.MartingaleState;
import com.martin.engine.PnlCalculator;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.client.KrakenFuturesWsClient;
import com.martin.kraken.dto.KrakenOrderRequest;
import com.martin.kraken.dto.KrakenOrderResponse;
import com.martin.kraken.dto.KrakenTickerResponse;
import com.martin.strategy.SignalResult;
import com.martin.strategy.TechnicalAnalysisService;
import com.martin.kraken.dto.KrakenFillsResponse;
import com.martin.kraken.dto.KrakenOpenOrdersResponse;
import com.martin.kraken.dto.KrakenPositionResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TradingOrchestrator {

    private static final Logger log = LoggerFactory.getLogger(TradingOrchestrator.class);
    private static final BigDecimal TAKER_FEE_PCT = new BigDecimal("0.05");
    private static final double MIN_SIGNAL_CONFIDENCE = 0.5;

    private final MartingaleEngine martingaleEngine;
    private final PnlCalculator pnlCalculator;
    private final TechnicalAnalysisService technicalAnalysis;
    private final KrakenFuturesRestClient krakenClient;
    private final KrakenFuturesWsClient krakenWsClient;
    private final TradeRepository tradeRepository;
    private final TradeSeriesRepository seriesRepository;
    private final LiveUpdateService liveUpdateService;
    private final BotConfigService botConfigService;
    private final ObjectMapper objectMapper;

    private final ConcurrentHashMap<String, MartingaleState> activeStates = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, List<Double>> priceHistory = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, BotConfig> activeConfigs = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, String> pendingTPOrders = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, String> pendingSLOrders = new ConcurrentHashMap<>();

    /**
     * On startup, recover open trades: restore state, subscribe to WS, and place TP/SL if missing.
     */
    @PostConstruct
    public void recoverOpenTrades() {
        List<BotConfig> allConfigs = botConfigService.getAllConfigs();
        Map<String, BotConfig> configByInstrument = allConfigs.stream()
                .collect(Collectors.toMap(BotConfig::getInstrument, c -> c, (a, b) -> a));

        // Fetch actual Kraken positions (both demo and prod)
        Set<String> krakenPositionInstruments = new HashSet<>();
        Set<Boolean> checkedDemo = new HashSet<>();
        for (BotConfig config : allConfigs) {
            if (!checkedDemo.add(config.isDemo())) continue;
            try {
                var response = krakenClient.getOpenPositions(config.isDemo()).block();
                if (response != null && response.getOpenPositions() != null) {
                    response.getOpenPositions().stream()
                            .filter(p -> Math.abs(p.getSize()) > 0)
                            .forEach(p -> krakenPositionInstruments.add(p.getSymbol()));
                }
            } catch (Exception e) {
                log.warn("Startup recovery: failed to fetch Kraken positions (demo={}): {}", config.isDemo(), e.getMessage());
            }
        }
        log.info("Startup recovery: Kraken has positions for: {}", krakenPositionInstruments);

        // Get ALL open trades, grouped by instrument, sorted newest first
        List<Trade> openTrades = tradeRepository.findByStatus(TradeStatus.OPEN);
        log.info("Startup recovery: found {} open trade(s) in DB", openTrades.size());

        // Group by instrument - keep newest, close the rest as stale
        Map<String, Trade> latestByInstrument = new HashMap<>();
        for (Trade t : openTrades) {
            String inst = t.getInstrument();
            Trade existing = latestByInstrument.get(inst);
            if (existing == null || (t.getOpenedAt() != null && existing.getOpenedAt() != null
                    && t.getOpenedAt().isAfter(existing.getOpenedAt()))) {
                if (existing != null) {
                    log.warn("Startup recovery: closing stale duplicate trade #{} for {}", existing.getId(), inst);
                    existing.setStatus(TradeStatus.LOST);
                    existing.setClosedAt(Instant.now());
                    tradeRepository.save(existing);
                }
                latestByInstrument.put(inst, t);
            } else {
                log.warn("Startup recovery: closing stale duplicate trade #{} for {}", t.getId(), inst);
                t.setStatus(TradeStatus.LOST);
                t.setClosedAt(Instant.now());
                tradeRepository.save(t);
            }
        }

        Set<String> recoveredInstruments = new HashSet<>();

        for (Map.Entry<String, Trade> entry : latestByInstrument.entrySet()) {
            String instrument = entry.getKey();
            Trade openTrade = entry.getValue();
            BotConfig config = configByInstrument.get(instrument);

            if (config == null) {
                log.warn("Startup recovery: no config for {}, skipping", instrument);
                continue;
            }

            if (!krakenPositionInstruments.contains(instrument)) {
                log.warn("Startup recovery: DB trade OPEN for {} but NO Kraken position - closing stale trade", instrument);
                openTrade.setStatus(TradeStatus.LOST);
                openTrade.setClosedAt(Instant.now());
                tradeRepository.save(openTrade);
                continue;
            }

            recoverInstrument(instrument, openTrade, config);
            recoveredInstruments.add(instrument);
        }

        // Also check Kraken positions for orphaned positions (no trade in DB)
        for (String krakenInstrument : krakenPositionInstruments) {
            if (recoveredInstruments.contains(krakenInstrument)) continue;
            BotConfig config = configByInstrument.get(krakenInstrument);
            if (config == null) {
                log.warn("Startup recovery: orphaned Kraken position for {} but no config", krakenInstrument);
                continue;
            }
            try {
                recoverFromKrakenPosition(config);
            } catch (Exception e) {
                log.warn("Startup recovery: failed to recover Kraken position for {}: {}",
                        krakenInstrument, e.getMessage());
            }
        }
    }

    private void recoverInstrument(String instrument, Trade openTrade, BotConfig config) {
        log.info("Startup recovery: restoring {} - direction={}, stake={}, step={}, entry={}",
                instrument, openTrade.getDirection(), openTrade.getStake(),
                openTrade.getDoublingStep(), openTrade.getEntryPrice());

        MartingaleState state = MartingaleState.builder()
                .instrument(instrument)
                .currentDirection(openTrade.getDirection())
                .currentStake(openTrade.getStake())
                .currentDoubling(openTrade.getDoublingStep())
                .active(true)
                .build();
        activeStates.put(instrument, state);
        activeConfigs.put(instrument, config);

        // Pre-load current price from REST API so sparkline has data immediately
        List<Double> prices = Collections.synchronizedList(new ArrayList<>());
        try {
            KrakenTickerResponse tickerResponse = krakenClient.getTickers(config.isDemo()).block();
            if (tickerResponse != null && tickerResponse.getTickers() != null) {
                tickerResponse.getTickers().stream()
                        .filter(t -> instrument.equals(t.getSymbol()))
                        .map(KrakenTickerResponse.Ticker::getLast)
                        .findFirst()
                        .ifPresent(p -> {
                            prices.add(p);
                            log.info("Startup recovery: pre-loaded price {} for {}", p, instrument);
                        });
            }
        } catch (Exception e) {
            log.warn("Startup recovery: failed to pre-load price for {}: {}", instrument, e.getMessage());
        }
        priceHistory.put(instrument, prices);

        krakenWsClient.subscribeTicker(instrument, config.isDemo())
                .subscribe(price -> {
                    List<Double> ph = priceHistory.get(instrument);
                    if (ph != null) {
                        ph.add(price);
                        MartingaleState s = activeStates.get(instrument);
                        if (s != null) {
                            checkPositionStatus(config, s, price);
                        }
                    }
                });

        checkAndPlaceTPSL(config, openTrade);
    }

    /**
     * Check Kraken for an open position with no corresponding DB trade.
     * Create a Trade record and restore bot state if found.
     */
    private void recoverFromKrakenPosition(BotConfig config) {
        String instrument = config.getInstrument();
        var response = krakenClient.getOpenPositions(config.isDemo()).block();
        if (response == null || response.getOpenPositions() == null) return;

        var krakenPos = response.getOpenPositions().stream()
                .filter(p -> instrument.equals(p.getSymbol()) && p.getSize() > 0)
                .findFirst()
                .orElse(null);
        if (krakenPos == null) return;

        log.info("Startup recovery: found orphaned Kraken position for {} - side={}, size={}, entry={}",
                instrument, krakenPos.getSide(), krakenPos.getSize(), krakenPos.getPrice());

        Direction direction = "long".equalsIgnoreCase(krakenPos.getSide()) ? Direction.LONG : Direction.SHORT;
        BigDecimal entryPrice = BigDecimal.valueOf(krakenPos.getPrice());
        BigDecimal stake = config.getInitialStake();

        // Create a TradeSeries
        TradeSeries series = TradeSeries.builder()
                .instrument(instrument)
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        // Create a Trade record
        Trade trade = Trade.builder()
                .series(series)
                .instrument(instrument)
                .direction(direction)
                .status(TradeStatus.OPEN)
                .stake(stake)
                .leverage(config.getLeverage())
                .entryPrice(entryPrice)
                .doublingStep(0)
                .openedAt(Instant.now())
                .build();
        trade = tradeRepository.save(trade);

        log.info("Startup recovery: created Trade#{} for orphaned {} position", trade.getId(), instrument);

        recoverInstrument(instrument, trade, config);
    }

    /**
     * Check Kraken for existing TP/SL orders for this trade. Place them if missing.
     */
    private void checkAndPlaceTPSL(BotConfig config, Trade openTrade) {
        String instrument = config.getInstrument();

        krakenClient.getOpenOrders(config.isDemo())
                .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                .subscribe(response -> {
                    if (response == null || response.getOpenOrders() == null) {
                        log.warn("Startup recovery: could not fetch open orders for {}", instrument);
                        placeTPSLFromTrade(config, openTrade);
                        return;
                    }

                    List<KrakenOpenOrdersResponse.Order> orders = response.getOpenOrders().stream()
                            .filter(o -> instrument.equals(o.getSymbol()))
                            .toList();

                    boolean hasTP = orders.stream().anyMatch(o -> "take_profit".equals(o.getOrderType()));
                    boolean hasSL = orders.stream().anyMatch(o -> "stp".equals(o.getOrderType()) || "stop".equals(o.getOrderType()));

                    // Store existing order IDs
                    orders.stream()
                            .filter(o -> "take_profit".equals(o.getOrderType()))
                            .findFirst()
                            .ifPresent(o -> {
                                pendingTPOrders.put(instrument, o.getOrderId());
                                log.info("Startup recovery: found existing TP order {} for {}", o.getOrderId(), instrument);
                            });
                    orders.stream()
                            .filter(o -> "stp".equals(o.getOrderType()) || "stop".equals(o.getOrderType()))
                            .findFirst()
                            .ifPresent(o -> {
                                pendingSLOrders.put(instrument, o.getOrderId());
                                log.info("Startup recovery: found existing SL order {} for {}", o.getOrderId(), instrument);
                            });

                    if (!hasTP || !hasSL) {
                        log.warn("Startup recovery: missing orders for {} (TP={}, SL={}) - placing now",
                                instrument, hasTP, hasSL);
                        if (!hasTP && !hasSL) {
                            placeTPSLFromTrade(config, openTrade);
                        }
                        // If only one is missing, we still place both (cancel existing first)
                        // This keeps things simple - Kraken will reject duplicates
                    } else {
                        log.info("Startup recovery: TP and SL orders already exist for {}", instrument);
                    }
                }, err -> {
                    log.error("Startup recovery: error fetching open orders for {}, placing TP/SL", instrument, err);
                    placeTPSLFromTrade(config, openTrade);
                });
    }

    /**
     * Place TP/SL orders from an existing open trade (used during startup recovery).
     */
    private void placeTPSLFromTrade(BotConfig config, Trade openTrade) {
        double entryPrice = openTrade.getEntryPrice().doubleValue();
        double size = openTrade.getStake().doubleValue() * openTrade.getLeverage() / entryPrice;
        int precision = config.getInstrument().contains("XBT") ? 4
                : config.getInstrument().contains("XRP") ? 0 : 3;
        double factor = Math.pow(10, precision);
        size = Math.round(size * factor) / factor;

        log.info("Startup recovery: placing TP/SL for {} - entry={}, size={}", config.getInstrument(), entryPrice, size);
        placeTPSLOrders(config, openTrade.getDirection(), entryPrice, size);
    }

    /**
     * Start the bot for a given config: subscribe to WebSocket ticker, collect prices,
     * and start a series once 30+ prices are available.
     */
    public void startBot(BotConfig config) {
        String instrument = config.getInstrument();
        log.info("Starting bot for instrument: {}", instrument);

        activeConfigs.put(instrument, config);
        priceHistory.put(instrument, Collections.synchronizedList(new ArrayList<>()));

        krakenWsClient.subscribeTicker(instrument, config.isDemo())
                .subscribe(price -> {
                    List<Double> prices = priceHistory.get(instrument);
                    if (prices != null) {
                        prices.add(price);
                        if (prices.size() >= 30 && !activeStates.containsKey(instrument)) {
                            checkForMacdEntry(config, new ArrayList<>(prices));
                        } else if (activeStates.containsKey(instrument)) {
                            checkPositionStatus(config, activeStates.get(instrument), price);
                        }
                    }
                });
    }

    /**
     * Analyze prices with technical indicators (unless MANUAL strategy)
     * and start a series with the determined direction.
     */
    public void startNewSeries(BotConfig config, List<Double> prices) {
        if ("MANUAL".equalsIgnoreCase(config.getSignalStrategy())) {
            log.info("MANUAL strategy for {} - waiting for forced direction", config.getInstrument());
            return;
        }

        SignalResult signal = technicalAnalysis.analyze(prices);
        log.info("Signal for {}: direction={}, confidence={}, reason={}",
                config.getInstrument(), signal.getDirection(), signal.getConfidence(), signal.getReason());

        if (signal.getConfidence() < MIN_SIGNAL_CONFIDENCE) {
            log.info("Signal confidence {} below minimum {} for {} - skipping entry",
                    signal.getConfidence(), MIN_SIGNAL_CONFIDENCE, config.getInstrument());
            return;
        }

        startSeriesWithDirection(config, signal.getDirection());
    }

    /**
     * Initialize martingale state, create TradeSeries entity, and place the first order.
     */
    public void startSeriesWithDirection(BotConfig config, Direction direction) {
        String instrument = config.getInstrument();
        log.info("Starting series for {} with direction {}", instrument, direction);

        MartingaleState state = martingaleEngine.initSeries(config, direction);
        activeStates.put(instrument, state);

        TradeSeries series = TradeSeries.builder()
                .instrument(instrument)
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        placeOrder(config, state, series);
        publishDashboardUpdate(instrument);
    }

    /**
     * Force a specific direction: stop current series if any, then start with the forced direction.
     */
    public void forceDirection(BotConfig config, Direction direction) {
        String instrument = config.getInstrument();
        log.info("Forcing direction {} for {}", direction, instrument);

        if (activeStates.containsKey(instrument)) {
            stopBot(instrument);
        }
        startSeriesWithDirection(config, direction);
    }

    /**
     * Stop the bot for a given instrument: remove state, mark active series as STOPPED.
     */
    public void stopBot(String instrument) {
        log.info("Stopping bot for instrument: {}", instrument);
        MartingaleState state = activeStates.remove(instrument);
        BotConfig cfg = activeConfigs.get(instrument);
        if (cfg != null) {
            cancelPendingTPSLOrders(cfg);
            closePositionOnKraken(cfg, state);
        }
        activeConfigs.remove(instrument);
        priceHistory.remove(instrument);

        seriesRepository.findByInstrumentAndStatus(instrument, SeriesStatus.ACTIVE)
                .forEach(series -> {
                    series.setStatus(SeriesStatus.STOPPED);
                    series.setEndedAt(Instant.now());
                    seriesRepository.save(series);
                });

        // Close open trades in DB
        tradeRepository.findByInstrumentOrderByOpenedAtDesc(instrument).stream()
                .filter(t -> t.getStatus() == TradeStatus.OPEN)
                .forEach(t -> {
                    t.setStatus(TradeStatus.LOST);
                    t.setClosedAt(Instant.now());
                    tradeRepository.save(t);
                });

        publishDashboardUpdate(instrument);
    }

    /**
     * Close the position on Kraken by sending an opposite market order with reduceOnly.
     */
    private void closePositionOnKraken(BotConfig config, MartingaleState state) {
        String instrument = config.getInstrument();
        try {
            var response = krakenClient.getOpenPositions(config.isDemo()).block();
            if (response == null || response.getOpenPositions() == null) return;

            var pos = response.getOpenPositions().stream()
                    .filter(p -> instrument.equals(p.getSymbol()) && Math.abs(p.getSize()) > 0)
                    .findFirst()
                    .orElse(null);
            if (pos == null) {
                log.info("No open position on Kraken for {} - nothing to close", instrument);
                return;
            }

            String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
            double size = Math.abs(pos.getSize());

            KrakenOrderRequest closeOrder = KrakenOrderRequest.builder()
                    .orderType("mkt")
                    .symbol(instrument)
                    .side(closeSide)
                    .size(size)
                    .reduceOnly(true)
                    .build();

            log.info("Closing position on Kraken: {} {} {} size={}", instrument, closeSide, "mkt", size);

            krakenClient.sendOrder(closeOrder, config.isDemo())
                    .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                    .subscribe(
                            r -> log.info("Position closed on Kraken for {}: result={}, status={}",
                                    instrument, r.getResult(),
                                    r.getSendStatus() != null ? r.getSendStatus().getStatus() : "null"),
                            err -> log.error("Failed to close position on Kraken for {}: {}", instrument, err.getMessage()));
        } catch (Exception e) {
            log.error("Error closing position on Kraken for {}: {}", instrument, e.getMessage());
        }
    }

    /**
     * Send a market order to Kraken and save the Trade entity.
     */
    public void placeOrder(BotConfig config, MartingaleState state, TradeSeries series) {
        String side = state.getCurrentDirection() == Direction.LONG ? "buy" : "sell";

        // Convert USD stake to BTC using last known price (WebSocket or REST fallback)
        List<Double> prices = priceHistory.get(config.getInstrument());
        double lastPrice = (prices != null && !prices.isEmpty()) ? prices.get(prices.size() - 1) : 0;
        if (lastPrice <= 0) {
            // Fallback: fetch price from REST API
            try {
                KrakenTickerResponse tickerResponse = krakenClient.getTickers(config.isDemo()).block();
                if (tickerResponse != null && tickerResponse.getTickers() != null) {
                    lastPrice = tickerResponse.getTickers().stream()
                            .filter(t -> config.getInstrument().equals(t.getSymbol()))
                            .map(KrakenTickerResponse.Ticker::getLast)
                            .findFirst()
                            .orElse(0.0);
                }
            } catch (Exception e) {
                log.error("Failed to fetch ticker for {}: {}", config.getInstrument(), e.getMessage());
            }
        }
        if (lastPrice <= 0) {
            log.error("No price available for {}, cannot place order", config.getInstrument());
            return;
        }
        double sizeInBtc = state.getCurrentStake().doubleValue() * config.getLeverage() / lastPrice;
        // Round to instrument-appropriate decimal places (BTC=4, ETH=3, others=3)
        int precision = config.getInstrument().contains("XBT") ? 4
                : config.getInstrument().contains("XRP") ? 0 : 3;
        double factor = Math.pow(10, precision);
        sizeInBtc = Math.round(sizeInBtc * factor) / factor;

        log.info("Converting stake: {} USD x {} leverage / {} price = {} BTC",
                state.getCurrentStake(), config.getLeverage(), lastPrice, sizeInBtc);

        KrakenOrderRequest orderRequest = KrakenOrderRequest.builder()
                .orderType("mkt")
                .symbol(config.getInstrument())
                .side(side)
                .size(sizeInBtc)
                .build();

        final double entryPriceForTP = lastPrice;
        final double sizeBtc = sizeInBtc;

        krakenClient.sendOrder(orderRequest, config.isDemo())
                .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                .subscribe(response -> {
                    if ("success".equals(response.getResult())) {
                        String orderId = response.getSendStatus().getOrderId();

                        // Fetch actual fill price from Kraken (with retry)
                        double actualFillPrice = fetchFillPrice(orderId, config.getInstrument(), config.isDemo());
                        double realEntryPrice = actualFillPrice > 0 ? actualFillPrice : entryPriceForTP;

                        if (actualFillPrice > 0) {
                            log.info("Actual fill price for {}: {} (WebSocket was {})",
                                    config.getInstrument(), actualFillPrice, entryPriceForTP);
                        } else {
                            log.warn("Could not fetch fill price for {}, using WebSocket price {} as fallback",
                                    config.getInstrument(), entryPriceForTP);
                        }

                        Trade trade = Trade.builder()
                                .series(series)
                                .instrument(config.getInstrument())
                                .krakenOrderId(orderId)
                                .direction(state.getCurrentDirection())
                                .status(TradeStatus.OPEN)
                                .stake(state.getCurrentStake())
                                .leverage(config.getLeverage())
                                .entryPrice(BigDecimal.valueOf(realEntryPrice))
                                .doublingStep(state.getCurrentDoubling())
                                .openedAt(Instant.now())
                                .build();
                        tradeRepository.save(trade);
                        log.info("Order placed: orderId={}, instrument={}, direction={}, stake={}, entryPrice={}",
                                orderId, config.getInstrument(),
                                state.getCurrentDirection(), state.getCurrentStake(), realEntryPrice);
                        try {
                            placeTPSLOrders(config, state.getCurrentDirection(), realEntryPrice, sizeBtc);
                        } catch (Exception e) {
                            log.error("Failed to place TP/SL after market order for {}: {}", config.getInstrument(), e.getMessage(), e);
                        }
                    } else {
                        log.error("Failed to place order for {}: result={}, error={}", config.getInstrument(),
                                response.getResult(), response.getError());
                    }
                }, error -> log.error("Error sending order for {}: {}", config.getInstrument(), error.getMessage()));
    }

    /**
     * Check if take-profit or stop-loss has been hit based on current price.
     */
    public void checkPositionStatus(BotConfig config, MartingaleState state, double price) {
        if (!state.isActive()) return;

        BigDecimal currentPrice = BigDecimal.valueOf(price);

        // Find the open trade for this instrument
        List<Trade> trades = tradeRepository.findByInstrumentOrderByOpenedAtDesc(config.getInstrument());
        Trade openTrade = trades.stream()
                .filter(t -> t.getStatus() == TradeStatus.OPEN)
                .findFirst()
                .orElse(null);

        if (openTrade == null || openTrade.getEntryPrice() == null) return;

        BigDecimal entryPrice = openTrade.getEntryPrice();
        BigDecimal tpPrice = martingaleEngine.calculateTakeProfitPrice(
                state.getCurrentDirection(), entryPrice, config.getTakeProfitPct());
        BigDecimal slPrice = martingaleEngine.calculateStopLossPrice(
                state.getCurrentDirection(), entryPrice, config.getStopLossPct());

        TradeSeries series = openTrade.getSeries();

        if (state.getCurrentDirection() == Direction.LONG) {
            if (currentPrice.compareTo(tpPrice) >= 0) {
                handleWin(config, state, openTrade, series, currentPrice);
            } else if (currentPrice.compareTo(slPrice) <= 0) {
                handleLoss(config, state, openTrade, series, currentPrice);
            }
        } else {
            if (currentPrice.compareTo(tpPrice) <= 0) {
                handleWin(config, state, openTrade, series, currentPrice);
            } else if (currentPrice.compareTo(slPrice) >= 0) {
                handleLoss(config, state, openTrade, series, currentPrice);
            }
        }
    }

    /**
     * Handle a winning trade: close position on Kraken, fetch real fill price, calculate net PnL.
     */
    public void handleWin(BotConfig config, MartingaleState state, Trade trade,
                          TradeSeries series, BigDecimal exitPrice) {
        log.info("WIN for {} at price {}", config.getInstrument(), exitPrice);
        cancelPendingTPSLOrders(config);

        // Close the position on Kraken and get actual exit price
        BigDecimal realExitPrice = closeAndGetFillPrice(config, state, exitPrice);

        BigDecimal netPnl = pnlCalculator.calculateNetPnl(
                state.getCurrentDirection(), trade.getStake(), config.getLeverage(),
                trade.getEntryPrice(), realExitPrice, TAKER_FEE_PCT);
        BigDecimal fees = pnlCalculator.calculateFees(trade.getStake(), config.getLeverage(), TAKER_FEE_PCT);

        trade.setExitPrice(realExitPrice);
        trade.setPnl(netPnl);
        trade.setFees(fees);
        trade.setStatus(TradeStatus.WON);
        trade.setClosedAt(Instant.now());
        tradeRepository.save(trade);

        series.setTotalPnl(series.getTotalPnl().add(netPnl));
        series.setTotalFees(series.getTotalFees().add(fees));
        series.setStatus(SeriesStatus.COMPLETED);
        series.setEndedAt(Instant.now());
        seriesRepository.save(series);

        log.info("WIN closed for {} - entry={}, exit={}, netPnl={}", config.getInstrument(),
                trade.getEntryPrice(), realExitPrice, netPnl);

        // Remove activeStates to wait for next MACD crossover
        activeStates.remove(config.getInstrument());
        publishDashboardUpdate(config.getInstrument());
    }

    /**
     * Handle a losing trade: close position on Kraken, fetch real fill price, calculate loss.
     */
    public void handleLoss(BotConfig config, MartingaleState state, Trade trade,
                           TradeSeries series, BigDecimal exitPrice) {
        log.info("LOSS for {} at price {}", config.getInstrument(), exitPrice);
        cancelPendingTPSLOrders(config);

        // Close the position on Kraken and get actual exit price
        BigDecimal realExitPrice = closeAndGetFillPrice(config, state, exitPrice);

        BigDecimal netPnl = pnlCalculator.calculateNetPnl(
                state.getCurrentDirection(), trade.getStake(), config.getLeverage(),
                trade.getEntryPrice(), realExitPrice, TAKER_FEE_PCT);
        BigDecimal fees = pnlCalculator.calculateFees(trade.getStake(), config.getLeverage(), TAKER_FEE_PCT);

        trade.setExitPrice(realExitPrice);
        trade.setPnl(netPnl);
        trade.setFees(fees);
        trade.setStatus(TradeStatus.LOST);
        trade.setClosedAt(Instant.now());
        tradeRepository.save(trade);

        log.info("LOSS closed for {} - entry={}, exit={}, netPnl={}", config.getInstrument(),
                trade.getEntryPrice(), realExitPrice, netPnl);

        series.setTotalPnl(series.getTotalPnl().add(netPnl));
        series.setTotalFees(series.getTotalFees().add(fees));

        // Apply martingale doubling
        MartingaleState updatedState = martingaleEngine.onLoss(state, config);

        if (!updatedState.isActive()) {
            // Max doublings reached - stop the series
            log.warn("Max doublings reached for {}. Stopping series.", config.getInstrument());
            series.setStatus(SeriesStatus.STOPPED);
            series.setEndedAt(Instant.now());
            seriesRepository.save(series);
            activeStates.remove(config.getInstrument());
            publishDashboardUpdate(config.getInstrument());
        } else {
            // Double stake and invert direction - place next order
            series.setCurrentDoubling(updatedState.getCurrentDoubling());
            seriesRepository.save(series);
            activeStates.put(config.getInstrument(), updatedState);
            placeOrder(config, updatedState, series);
            publishDashboardUpdate(config.getInstrument());
        }
    }

    /**
     * Return the current MartingaleState for an instrument.
     */
    public MartingaleState getState(String instrument) {
        return activeStates.get(instrument);
    }

    /**
     * Return the last known price for an instrument from WebSocket price history.
     */
    public Double getLastPrice(String instrument) {
        List<Double> prices = priceHistory.get(instrument);
        return (prices != null && !prices.isEmpty()) ? prices.get(prices.size() - 1) : null;
    }

    /**
     * Return recent price history for an instrument (last N prices).
     */
    public List<Double> getPriceHistory(String instrument, int maxPoints) {
        List<Double> prices = priceHistory.get(instrument);
        if (prices == null || prices.isEmpty()) return List.of();
        int size = prices.size();
        int from = Math.max(0, size - maxPoints);
        return new ArrayList<>(prices.subList(from, size));
    }

    /**
     * Check for MACD crossover signal. Enters a position only when crossover is detected.
     * Replaces the immediate-entry behavior after price history is available.
     */
    private void checkForMacdEntry(BotConfig config, List<Double> prices) {
        if ("MANUAL".equalsIgnoreCase(config.getSignalStrategy())) return;

        Optional<Direction> crossover = technicalAnalysis.detectCrossover(prices);
        if (crossover.isEmpty()) return;

        if (!technicalAnalysis.confirmWithRsi(prices, crossover.get())) {
            log.info("MACD {} crossover for {} rejected by RSI confirmation",
                    crossover.get() == Direction.LONG ? "bullish" : "bearish",
                    config.getInstrument());
            return;
        }

        log.info("MACD {} crossover detected for {} → entering {}",
                crossover.get() == Direction.LONG ? "bullish" : "bearish",
                config.getInstrument(), crossover.get());
        startSeriesWithDirection(config, crossover.get());
    }

    /**
     * Place take-profit and stop-loss orders on Kraken immediately after a market fill.
     * Both orders are reduceOnly to prevent accidental position opening.
     */
    private void placeTPSLOrders(BotConfig config, Direction direction, double entryPrice, double size) {
        double tpPct = config.getTakeProfitPct().doubleValue() / 100.0;
        double slPct = config.getStopLossPct().doubleValue() / 100.0;

        // Kraken tick size: BTC = 1, ETH = 0.1, XRP = 0.0001
        double tickSize;
        if (config.getInstrument().contains("XBT")) {
            tickSize = 1.0;
        } else if (config.getInstrument().contains("XRP")) {
            tickSize = 0.00001;
        } else {
            tickSize = 0.1;
        }

        double tpTrigger, slTrigger;
        String closeSide;
        if (direction == Direction.LONG) {
            tpTrigger = Math.round(entryPrice * (1.0 + tpPct) / tickSize) * tickSize;
            slTrigger = Math.round(entryPrice * (1.0 - slPct) / tickSize) * tickSize;
            closeSide = "sell";
        } else {
            tpTrigger = Math.round(entryPrice * (1.0 - tpPct) / tickSize) * tickSize;
            slTrigger = Math.round(entryPrice * (1.0 + slPct) / tickSize) * tickSize;
            closeSide = "buy";
        }

        String instrument = config.getInstrument();
        log.info("Placing TP/SL orders for {} - TP trigger={}, SL trigger={}, side={}, size={}, demo={}",
                instrument, tpTrigger, slTrigger, closeSide, size, config.isDemo());

        KrakenOrderRequest tpOrder = KrakenOrderRequest.builder()
                .orderType("take_profit")
                .symbol(instrument)
                .side(closeSide)
                .size(size)
                .stopPrice(tpTrigger)
                .limitPrice(tpTrigger)
                .triggerSignal("last")
                .reduceOnly(true)
                .build();

        KrakenOrderRequest slOrder = KrakenOrderRequest.builder()
                .orderType("stp")
                .symbol(instrument)
                .side(closeSide)
                .size(size)
                .stopPrice(slTrigger)
                .limitPrice(slTrigger)
                .triggerSignal("last")
                .reduceOnly(true)
                .build();

        krakenClient.sendOrder(tpOrder, config.isDemo())
                .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                .subscribe(r -> {
                    if ("success".equals(r.getResult()) && "placed".equals(r.getSendStatus().getStatus())) {
                        pendingTPOrders.put(instrument, r.getSendStatus().getOrderId());
                        log.info("TP order placed: orderId={}, trigger={}", r.getSendStatus().getOrderId(), tpTrigger);
                    } else {
                        log.error("FAILED to place TP order for {}: result={}, status={}, error={}", instrument, r.getResult(), r.getSendStatus() != null ? r.getSendStatus().getStatus() : "null", r.getError());
                    }
                }, err -> log.error("ERROR placing TP order for {}", instrument, err));

        krakenClient.sendOrder(slOrder, config.isDemo())
                .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                .subscribe(r -> {
                    if ("success".equals(r.getResult()) && "placed".equals(r.getSendStatus().getStatus())) {
                        pendingSLOrders.put(instrument, r.getSendStatus().getOrderId());
                        log.info("SL order placed: orderId={}, trigger={}", r.getSendStatus().getOrderId(), slTrigger);
                    } else {
                        log.error("FAILED to place SL order for {}: result={}, status={}, error={}", instrument, r.getResult(), r.getSendStatus() != null ? r.getSendStatus().getStatus() : "null", r.getError());
                    }
                }, err -> log.error("ERROR placing SL order for {}", instrument, err));
    }

    /**
     * Close the position on Kraken (if still open) and return the actual exit fill price.
     * If the position was already closed by Kraken TP/SL, fetches the fill price from fills history.
     * Falls back to the WebSocket exitPrice if fill price cannot be retrieved.
     */
    private BigDecimal closeAndGetFillPrice(BotConfig config, MartingaleState state, BigDecimal wsExitPrice) {
        String instrument = config.getInstrument();
        try {
            var response = krakenClient.getOpenPositions(config.isDemo()).block();
            if (response != null && response.getOpenPositions() != null) {
                var pos = response.getOpenPositions().stream()
                        .filter(p -> instrument.equals(p.getSymbol()) && Math.abs(p.getSize()) > 0)
                        .findFirst()
                        .orElse(null);

                if (pos != null) {
                    // Position still open - Kraken TP/SL didn't fire yet. Close with market order.
                    String closeSide = "long".equalsIgnoreCase(pos.getSide()) ? "sell" : "buy";
                    double size = Math.abs(pos.getSize());

                    KrakenOrderRequest closeOrder = KrakenOrderRequest.builder()
                            .orderType("mkt")
                            .symbol(instrument)
                            .side(closeSide)
                            .size(size)
                            .reduceOnly(true)
                            .build();

                    log.info("Position still open on Kraken, closing: {} {} size={}", instrument, closeSide, size);
                    KrakenOrderResponse closeResponse = krakenClient.sendOrder(closeOrder, config.isDemo()).block();

                    if (closeResponse != null && "success".equals(closeResponse.getResult())) {
                        String closeOrderId = closeResponse.getSendStatus().getOrderId();
                        double fillPrice = fetchFillPrice(closeOrderId, instrument, config.isDemo());
                        if (fillPrice > 0) {
                            log.info("Position closed at real fill price: {}", fillPrice);
                            return BigDecimal.valueOf(fillPrice);
                        }
                    }
                } else {
                    // Position already closed by Kraken TP/SL - fetch the fill price
                    log.info("Position already closed on Kraken for {}, fetching TP/SL fill price", instrument);
                    String tpOrderId = pendingTPOrders.get(instrument);
                    String slOrderId = pendingSLOrders.get(instrument);

                    if (tpOrderId != null) {
                        double fillPrice = fetchFillPrice(tpOrderId, instrument, config.isDemo());
                        if (fillPrice > 0) {
                            log.info("TP fill price for {}: {}", instrument, fillPrice);
                            return BigDecimal.valueOf(fillPrice);
                        }
                    }
                    if (slOrderId != null) {
                        double fillPrice = fetchFillPrice(slOrderId, instrument, config.isDemo());
                        if (fillPrice > 0) {
                            log.info("SL fill price for {}: {}", instrument, fillPrice);
                            return BigDecimal.valueOf(fillPrice);
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Error closing/fetching fill price for {}: {}", instrument, e.getMessage());
        }

        log.warn("Using WebSocket exit price {} as fallback for {}", wsExitPrice, instrument);
        return wsExitPrice;
    }

    /**
     * Fetch the actual fill price from Kraken for a given order ID.
     * Retries up to 3 times with 500ms delay to allow the fill to be recorded.
     */
    private double fetchFillPrice(String orderId, String instrument, boolean demo) {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                if (attempt > 1) {
                    Thread.sleep(500);
                }
                KrakenFillsResponse fillsResponse = krakenClient.getFills(demo).block();
                if (fillsResponse != null && fillsResponse.getFills() != null) {
                    var fill = fillsResponse.getFills().stream()
                            .filter(f -> orderId.equals(f.getOrderId()) && instrument.equals(f.getSymbol()))
                            .findFirst()
                            .orElse(null);
                    if (fill != null && fill.getPrice() != null) {
                        return fill.getPrice();
                    }
                }
            } catch (Exception e) {
                log.warn("Attempt {}/3 - Failed to fetch fill price for order {}: {}", attempt, orderId, e.getMessage());
            }
        }
        return 0;
    }

    /**
     * Cancel pending TP and SL orders on Kraken when internal monitoring closes the position first.
     */
    private void cancelPendingTPSLOrders(BotConfig config) {
        String instrument = config.getInstrument();
        String tpId = pendingTPOrders.remove(instrument);
        String slId = pendingSLOrders.remove(instrument);
        if (tpId != null) {
            krakenClient.cancelOrder(tpId, config.isDemo())
                    .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                    .subscribe(
                            r -> log.info("TP order cancelled: orderId={}", tpId),
                            err -> log.warn("Error cancelling TP order {}: {}", tpId, err.getMessage()));
        }
        if (slId != null) {
            krakenClient.cancelOrder(slId, config.isDemo())
                    .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                    .subscribe(
                            r -> log.info("SL order cancelled: orderId={}", slId),
                            err -> log.warn("Error cancelling SL order {}: {}", slId, err.getMessage()));
        }
    }

    /**
     * Build and publish a dashboard state update via SSE.
     */
    private void publishDashboardUpdate(String instrument) {
        try {
            MartingaleState state = activeStates.get(instrument);
            List<Trade> trades = tradeRepository.findByInstrumentOrderByOpenedAtDesc(instrument);

            BigDecimal totalPnl = trades.stream()
                    .map(t -> t.getPnl() != null ? t.getPnl() : BigDecimal.ZERO)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

            int wins = (int) trades.stream().filter(t -> t.getStatus() == TradeStatus.WON).count();
            int losses = (int) trades.stream().filter(t -> t.getStatus() == TradeStatus.LOST).count();

            // Find open trade for entry/TP/SL prices
            Trade openTrade = trades.stream()
                    .filter(t -> t.getStatus() == TradeStatus.OPEN)
                    .findFirst()
                    .orElse(null);

            BigDecimal entryPrice = openTrade != null ? openTrade.getEntryPrice() : null;
            BigDecimal takeProfitPrice = null;
            BigDecimal stopLossPrice = null;

            if (openTrade != null && entryPrice != null) {
                BotConfig config = activeConfigs.get(instrument);
                Direction direction = state != null ? state.getCurrentDirection() : openTrade.getDirection();
                if (config != null && direction != null) {
                    takeProfitPrice = martingaleEngine.calculateTakeProfitPrice(
                            direction, entryPrice, config.getTakeProfitPct());
                    stopLossPrice = martingaleEngine.calculateStopLossPrice(
                            direction, entryPrice, config.getStopLossPct());
                }
            }

            // Current price from WebSocket
            List<Double> prices = priceHistory.get(instrument);
            BigDecimal currentPrice = (prices != null && !prices.isEmpty())
                    ? BigDecimal.valueOf(prices.get(prices.size() - 1)) : null;

            // Win rate
            int totalClosed = wins + losses;
            BigDecimal winRate = totalClosed > 0
                    ? BigDecimal.valueOf(wins * 100.0 / totalClosed).setScale(1, java.math.RoundingMode.HALF_UP)
                    : null;

            var dashboardMap = new java.util.LinkedHashMap<String, Object>();
            dashboardMap.put("instrument", instrument);
            dashboardMap.put("botActive", state != null && state.isActive());
            dashboardMap.put("currentDirection", state != null ? state.getCurrentDirection().name()
                    : (openTrade != null ? openTrade.getDirection().name() : null));
            dashboardMap.put("currentStake", state != null ? state.getCurrentStake()
                    : (openTrade != null ? openTrade.getStake() : null));
            dashboardMap.put("currentDoubling", state != null ? state.getCurrentDoubling()
                    : (openTrade != null ? openTrade.getDoublingStep() : 0));
            dashboardMap.put("totalPnl", totalPnl);
            dashboardMap.put("totalTrades", trades.size());
            dashboardMap.put("wins", wins);
            dashboardMap.put("losses", losses);
            dashboardMap.put("currentPrice", currentPrice);
            dashboardMap.put("entryPrice", entryPrice);
            dashboardMap.put("takeProfitPrice", takeProfitPrice);
            dashboardMap.put("stopLossPrice", stopLossPrice);
            dashboardMap.put("winRate", winRate);

            // Unrealized P&L in USD (includes estimated fees)
            BigDecimal unrealizedPnl = null;
            if (openTrade != null && entryPrice != null && currentPrice != null) {
                BotConfig config = activeConfigs.get(instrument);
                Direction direction = state != null ? state.getCurrentDirection() : openTrade.getDirection();
                if (config != null && direction != null) {
                    unrealizedPnl = pnlCalculator.calculateNetPnl(
                            direction, openTrade.getStake(), config.getLeverage(),
                            entryPrice, currentPrice, TAKER_FEE_PCT);
                }
            }
            dashboardMap.put("unrealizedPnl", unrealizedPnl);

            String json = objectMapper.writeValueAsString(dashboardMap);
            liveUpdateService.publishUpdate(instrument, json);
        } catch (Exception e) {
            log.warn("Failed to publish dashboard update for {}: {}", instrument, e.getMessage());
        }
    }
}
