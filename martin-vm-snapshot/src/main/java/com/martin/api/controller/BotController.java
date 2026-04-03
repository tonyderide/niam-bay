package com.martin.api.controller;

import com.martin.api.dto.DashboardDto;
import com.martin.domain.entity.BotConfig;
import com.martin.domain.entity.Trade;
import com.martin.domain.enums.Direction;
import com.martin.domain.enums.TradeStatus;
import com.martin.domain.repository.TradeRepository;
import com.martin.engine.MartingaleEngine;
import com.martin.engine.MartingaleState;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenOpenOrdersResponse;
import com.martin.kraken.dto.KrakenPositionResponse;
import com.martin.service.BotConfigService;
import com.martin.service.TradingOrchestrator;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

@RestController
@RequestMapping("/api/bot")
@RequiredArgsConstructor
public class BotController {

    private static final Logger log = LoggerFactory.getLogger(BotController.class);

    private final TradingOrchestrator orchestrator;
    private final BotConfigService botConfigService;
    private final TradeRepository tradeRepository;
    private final MartingaleEngine martingaleEngine;
    private final KrakenFuturesRestClient krakenClient;
    private final com.martin.engine.PnlCalculator pnlCalculator;

    @PostMapping("/start/{configId}")
    public ResponseEntity<String> startBot(@PathVariable Long configId) {
        log.info(">> POST /bot/start/{}", configId);
        BotConfig config = botConfigService.getById(configId);
        orchestrator.startBot(config);
        log.info("<< Bot started for {}", config.getInstrument());
        return ResponseEntity.ok("Bot started for " + config.getInstrument());
    }

    @PostMapping("/stop/{instrument}")
    public ResponseEntity<String> stopBot(@PathVariable String instrument) {
        log.info(">> POST /bot/stop/{}", instrument);
        orchestrator.stopBot(instrument);
        log.info("<< Bot stopped for {}", instrument);
        return ResponseEntity.ok("Bot stopped for " + instrument);
    }

    @PostMapping("/force-direction/{configId}")
    public ResponseEntity<String> forceDirection(@PathVariable Long configId,
                                                  @RequestParam Direction direction) {
        log.info(">> POST /bot/force-direction/{} direction={}", configId, direction);
        BotConfig config = botConfigService.getById(configId);
        orchestrator.forceDirection(config, direction);
        log.info("<< Direction forced to {} for {}", direction, config.getInstrument());
        return ResponseEntity.ok("Direction forced to " + direction + " for " + config.getInstrument());
    }

    @GetMapping("/dashboard/{instrument}")
    public ResponseEntity<DashboardDto> dashboard(@PathVariable String instrument) {
        log.debug(">> GET /bot/dashboard/{}", instrument);
        MartingaleState state = orchestrator.getState(instrument);
        List<Trade> trades = tradeRepository.findByInstrumentOrderByOpenedAtDesc(instrument);

        BigDecimal totalPnl = trades.stream()
                .map(t -> t.getPnl() != null ? t.getPnl() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        int wins = (int) trades.stream().filter(t -> t.getStatus() == TradeStatus.WON).count();
        int losses = (int) trades.stream().filter(t -> t.getStatus() == TradeStatus.LOST).count();

        // Current price from WebSocket
        Double lastPrice = orchestrator.getLastPrice(instrument);
        BigDecimal currentPrice = lastPrice != null ? BigDecimal.valueOf(lastPrice) : null;

        // Open trade entry/TP/SL
        Trade openTrade = trades.stream()
                .filter(t -> t.getStatus() == TradeStatus.OPEN)
                .findFirst()
                .orElse(null);
        BigDecimal entryPrice = openTrade != null ? openTrade.getEntryPrice() : null;
        BigDecimal takeProfitPrice = null;
        BigDecimal stopLossPrice = null;

        if (entryPrice != null && openTrade != null) {
            // Find config for this instrument (try active first, then any)
            BotConfig config = botConfigService.findByInstrument(instrument);
            Direction direction = state != null ? state.getCurrentDirection() : openTrade.getDirection();
            if (config != null && direction != null) {
                takeProfitPrice = martingaleEngine.calculateTakeProfitPrice(
                        direction, entryPrice, config.getTakeProfitPct());
                stopLossPrice = martingaleEngine.calculateStopLossPrice(
                        direction, entryPrice, config.getStopLossPct());
            }
        }

        // Win rate
        int totalClosed = wins + losses;
        BigDecimal winRate = totalClosed > 0
                ? BigDecimal.valueOf(wins * 100.0 / totalClosed).setScale(1, RoundingMode.HALF_UP)
                : null;

        DashboardDto dto = DashboardDto.builder()
                .instrument(instrument)
                .botActive(state != null && state.isActive())
                .currentDirection(state != null ? state.getCurrentDirection().name()
                        : (openTrade != null ? openTrade.getDirection().name() : null))
                .currentStake(state != null ? state.getCurrentStake()
                        : (openTrade != null ? openTrade.getStake() : null))
                .currentDoubling(state != null ? state.getCurrentDoubling()
                        : (openTrade != null ? openTrade.getDoublingStep() : 0))
                .totalPnl(totalPnl)
                .totalTrades(trades.size())
                .wins(wins)
                .losses(losses)
                .currentPrice(currentPrice)
                .entryPrice(entryPrice)
                .takeProfitPrice(takeProfitPrice)
                .stopLossPrice(stopLossPrice)
                .winRate(winRate)
                .unrealizedPnl(calculateUnrealizedPnl(openTrade, currentPrice, state, instrument))
                .build();

        return ResponseEntity.ok(dto);
    }

    private static final BigDecimal TAKER_FEE_PCT = new BigDecimal("0.05");

    private BigDecimal calculateUnrealizedPnl(Trade openTrade, BigDecimal currentPrice,
                                                MartingaleState state, String instrument) {
        if (openTrade == null || openTrade.getEntryPrice() == null || currentPrice == null) return null;
        BotConfig config = botConfigService.findByInstrument(instrument);
        Direction direction = state != null ? state.getCurrentDirection() : openTrade.getDirection();
        if (config == null || direction == null) return null;
        return pnlCalculator.calculateNetPnl(
                direction, openTrade.getStake(), config.getLeverage(),
                openTrade.getEntryPrice(), currentPrice, TAKER_FEE_PCT);
    }

    @GetMapping("/positions")
    public ResponseEntity<List<KrakenPositionResponse.Position>> getOpenPositions(
            @RequestParam(defaultValue = "false") boolean demo) {
        log.debug(">> GET /bot/positions demo={}", demo);
        KrakenPositionResponse response = krakenClient.getOpenPositions(demo).block();
        if (response != null && response.getOpenPositions() != null) {
            log.debug("<< {} open positions", response.getOpenPositions().size());
            return ResponseEntity.ok(response.getOpenPositions());
        }
        log.debug("<< no positions");
        return ResponseEntity.ok(List.of());
    }

    @PostMapping("/cancel-order")
    public ResponseEntity<String> cancelOrder(@RequestParam String orderId,
                                               @RequestParam(defaultValue = "false") boolean demo) {
        log.info(">> POST /bot/cancel-order orderId={}", orderId);
        try {
            var response = krakenClient.cancelOrder(orderId, demo).block();
            return ResponseEntity.ok("Cancelled: " + orderId);
        } catch (Exception e) {
            return ResponseEntity.ok("Cancel failed: " + e.getMessage());
        }
    }

    @GetMapping("/orders")
    public ResponseEntity<List<KrakenOpenOrdersResponse.Order>> getOpenOrders(
            @RequestParam(defaultValue = "false") boolean demo) {
        log.debug(">> GET /bot/orders demo={}", demo);
        KrakenOpenOrdersResponse response = krakenClient.getOpenOrders(demo).block();
        if (response != null && response.getOpenOrders() != null) {
            log.debug("<< {} open orders", response.getOpenOrders().size());
            return ResponseEntity.ok(response.getOpenOrders());
        }
        log.debug("<< no open orders");
        return ResponseEntity.ok(List.of());
    }

    @GetMapping("/prices/{instrument}")
    public ResponseEntity<List<Double>> getPriceHistory(@PathVariable String instrument,
                                                         @RequestParam(defaultValue = "100") int limit) {
        List<Double> prices = orchestrator.getPriceHistory(instrument, limit);
        return ResponseEntity.ok(prices);
    }

    /**
     * Get real account balance from Kraken.
     */
    /**
     * Health check / keep-alive endpoint.
     */
    @GetMapping("/health")
    public ResponseEntity<?> health() {
        return ResponseEntity.ok(java.util.Map.of(
                "status", "UP",
                "timestamp", java.time.Instant.now().toString()
        ));
    }

    @GetMapping("/balance")
    public ResponseEntity<?> getAccountBalance(@RequestParam(defaultValue = "false") boolean demo) {
        log.debug(">> GET /bot/balance demo={}", demo);
        try {
            var response = krakenClient.getAccounts(demo).block();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to get balance: {}", e.getMessage());
            return ResponseEntity.ok(java.util.Map.of("error", e.getMessage()));
        }
    }

    /**
     * Proxy OHLC candles from Kraken public API for chart history.
     */
    @GetMapping("/ohlc/{instrument}")
    public ResponseEntity<?> getOhlc(@PathVariable String instrument,
                                      @RequestParam(defaultValue = "60") int minutes) {
        log.debug(">> GET /bot/ohlc/{} minutes={}", instrument, minutes);
        try {
            var response = krakenClient.getOhlc(instrument, minutes).block();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to get OHLC: {}", e.getMessage());
            return ResponseEntity.ok(java.util.Map.of("error", e.getMessage()));
        }
    }
}
