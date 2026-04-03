package com.martin.grid;

import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenFillsResponse;
import com.martin.kraken.dto.KrakenOrderRequest;
import com.martin.kraken.dto.KrakenOpenOrdersResponse;
import com.martin.kraken.dto.KrakenTickerResponse;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import java.util.Arrays;

@Service
@RequiredArgsConstructor
public class GridTradingService {

    private static final Logger log = LoggerFactory.getLogger(GridTradingService.class);
    private static final BigDecimal MAKER_FEE_PCT = new BigDecimal("0.02");

    private final KrakenFuturesRestClient krakenClient;
    private final GridStateRepository gridStateRepository;

    private final ConcurrentHashMap<String, GridState> activeGrids = new ConcurrentHashMap<>();

    @PostConstruct
    public void reloadActiveGrids() {
        List<GridStateEntity> entities = gridStateRepository.findAllByActiveTrue();
        for (GridStateEntity entity : entities) {
            GridState state = fromEntity(entity);
            activeGrids.put(state.getInstrument(), state);

            // Cancel ALL existing orders for this instrument before re-placing
            try {
                var openOrders = krakenClient.getOpenOrders(state.isDemo()).block();
                if (openOrders != null && openOrders.getOpenOrders() != null) {
                    openOrders.getOpenOrders().stream()
                            .filter(o -> state.getInstrument().equals(o.getSymbol()))
                            .forEach(o -> {
                                log.info("Grid reload: cancelling stale order {} for {}", o.getOrderId(), state.getInstrument());
                                cancelOrder(o.getOrderId(), state.isDemo());
                            });
                }
            } catch (Exception e) {
                log.warn("Grid reload: failed to cancel stale orders: {}", e.getMessage());
            }

            log.info("Grid reloaded for {} - center={}, range=[{}, {}], P&L=${}, roundTrips={}",
                    state.getInstrument(), state.getCenterPrice(),
                    state.getLowerBound(), state.getUpperBound(),
                    state.getTotalProfit(), state.getCompletedRoundTrips());

            // Recalculate sides based on current price (price may have moved during downtime)
            double currentPrice = fetchCurrentPrice(state.getInstrument(), state.isDemo());
            if (currentPrice > 0) {
                // If price moved outside range, recenter
                if (currentPrice > state.getUpperBound() || currentPrice < state.getLowerBound()) {
                    log.info("Grid reload: price {} is outside range [{}, {}], recentering",
                            currentPrice, state.getLowerBound(), state.getUpperBound());
                    double halfRange = state.getGridSpacing() * (state.getTotalLevels() / 2);
                    state.setCenterPrice(currentPrice);
                    state.setUpperBound(roundToTick(state.getInstrument(), currentPrice + halfRange));
                    state.setLowerBound(roundToTick(state.getInstrument(), currentPrice - halfRange));

                    List<GridLevel> newLevels = new ArrayList<>();
                    for (int i = 0; i < state.getTotalLevels(); i++) {
                        double price = roundToTick(state.getInstrument(),
                                state.getLowerBound() + state.getGridSpacing() * i + state.getGridSpacing() / 2);
                        String side = getSideForMode(state.getGridMode(), price, currentPrice);
                        newLevels.add(GridLevel.builder()
                                .index(i).price(price).side(side)
                                .status(GridLevel.GridLevelStatus.WAITING)
                                .roundTrips(0).build());
                    }
                    state.setLevels(newLevels);
                } else {
                    // Price still in range: recalculate side per level based on current price
                    // Only flip sides in NEUTRAL mode — SHORT/LONG modes keep their direction
                    if (state.getGridMode() == GridMode.NEUTRAL || state.getGridMode() == null) {
                        for (GridLevel level : state.getLevels()) {
                            String correctSide = level.getPrice() < currentPrice ? "buy" : "sell";
                            if (!correctSide.equals(level.getSide())) {
                                log.info("Grid reload: flipping level #{} @ {} from {} to {} (price={})",
                                        level.getIndex(), level.getPrice(), level.getSide(), correctSide, currentPrice);
                                level.setSide(correctSide);
                            }
                            level.setKrakenOrderId(null);
                            level.setStatus(GridLevel.GridLevelStatus.WAITING);
                        }
                    } else {
                        for (GridLevel level : state.getLevels()) {
                            level.setKrakenOrderId(null);
                            level.setStatus(GridLevel.GridLevelStatus.WAITING);
                        }
                    }
                }
            } else {
                // Can't fetch price, just re-place with existing sides
                for (GridLevel level : state.getLevels()) {
                    level.setKrakenOrderId(null);
                    if (level.getStatus() == GridLevel.GridLevelStatus.PLACED) {
                        level.setStatus(GridLevel.GridLevelStatus.WAITING);
                    }
                }
            }
            placeAllOrders(state);
            persistState(state);
        }
        if (!entities.isEmpty()) {
            log.info("Reloaded {} active grid(s) from database", entities.size());
        }
    }

    @Transactional
    public GridState startGrid(String instrument, double capital, int leverage, boolean demo,
                               double gridSpacingPct, int totalLevels, double maxLossPercent, GridMode gridMode) {
        if (activeGrids.containsKey(instrument)) {
            throw new IllegalStateException("Grid already active for " + instrument);
        }

        double currentPrice = fetchCurrentPrice(instrument, demo);
        if (currentPrice <= 0) {
            throw new IllegalStateException("Cannot fetch price for " + instrument);
        }

        // Defaults
        if (gridSpacingPct <= 0) gridSpacingPct = 0.007;
        if (gridSpacingPct < 0.005) {
            throw new IllegalArgumentException("Grid spacing " + (gridSpacingPct * 100) + "% is below minimum 0.5%");
        }
        if (totalLevels <= 0) totalLevels = 6;
        if (maxLossPercent <= 0) maxLossPercent = 50.0;
        double amountPerLevel = capital / totalLevels;
        double gridSpacing = roundToTick(instrument, currentPrice * gridSpacingPct);
        double halfRange = gridSpacing * (totalLevels / 2);
        double upperBound = roundToTick(instrument, currentPrice + halfRange);
        double lowerBound = roundToTick(instrument, currentPrice - halfRange);

        if (gridMode == null) gridMode = GridMode.NEUTRAL;

        List<GridLevel> levels = new ArrayList<>();
        for (int i = 0; i < totalLevels; i++) {
            double price = roundToTick(instrument, lowerBound + gridSpacing * i + gridSpacing / 2);
            String side = getSideForMode(gridMode, price, currentPrice);
            levels.add(GridLevel.builder()
                    .index(i)
                    .price(price)
                    .side(side)
                    .status(GridLevel.GridLevelStatus.WAITING)
                    .roundTrips(0)
                    .build());
        }

        GridState state = GridState.builder()
                .instrument(instrument)
                .active(true)
                .demo(demo)
                .centerPrice(currentPrice)
                .upperBound(upperBound)
                .lowerBound(lowerBound)
                .gridSpacing(gridSpacing)
                .totalLevels(totalLevels)
                .leverage(leverage)
                .amountPerLevel(amountPerLevel)
                .levels(levels)
                .totalProfit(BigDecimal.ZERO)
                .completedRoundTrips(0)
                .startedAt(Instant.now())
                .fills(new ArrayList<>())
                .maxLossPercent(maxLossPercent)
                .capital(capital)
                .gridMode(gridMode)
                .build();

        activeGrids.put(instrument, state);
        persistState(state);

        log.info("Grid started for {} [{}] - center={}, range=[{}, {}], spacing={}, levels={}, $/level={}",
                instrument, gridMode, currentPrice, lowerBound, upperBound, gridSpacing, totalLevels, amountPerLevel);

        placeAllOrders(state);
        return state;
    }

    @Transactional
    public void stopGrid(String instrument) {
        GridState state = activeGrids.remove(instrument);
        if (state == null) return;

        state.setActive(false);
        log.info("Stopping grid for {} - cancelling all orders", instrument);

        for (GridLevel level : state.getLevels()) {
            if (level.getStatus() == GridLevel.GridLevelStatus.PLACED && level.getKrakenOrderId() != null) {
                cancelOrder(level.getKrakenOrderId(), state.isDemo());
            }
        }

        // Mark inactive in DB
        gridStateRepository.findByInstrument(instrument).ifPresent(entity -> {
            entity.setActive(false);
            gridStateRepository.save(entity);
        });
    }

    public GridState getState(String instrument) {
        GridState state = activeGrids.get(instrument);
        if (state != null) {
            // Enrich with real Kraken P&L
            enrichWithKrakenPnl(state);
        }
        return state;
    }

    /**
     * Fetch real P&L from Kraken fills and open positions.
     * This gives the true realized + unrealized P&L, not our internal calculation.
     */
    private void enrichWithKrakenPnl(GridState state) {
        try {
            // Get real fills from Kraken
            KrakenFillsResponse fillsResponse = krakenClient.getFills(state.isDemo()).block();
            if (fillsResponse == null || !"success".equals(fillsResponse.getResult()) || fillsResponse.getFills() == null) {
                return;
            }

            // Filter fills for this instrument
            List<KrakenFillsResponse.Fill> instrumentFills = fillsResponse.getFills().stream()
                    .filter(f -> state.getInstrument().equals(f.getSymbol()))
                    .sorted(Comparator.comparing(KrakenFillsResponse.Fill::getFillTime))
                    .collect(Collectors.toList());

            // FIFO matching: match buys to sells
            List<double[]> buys = new ArrayList<>();  // [remaining_size, price]
            List<double[]> sells = new ArrayList<>(); // [remaining_size, price]

            for (KrakenFillsResponse.Fill fill : instrumentFills) {
                if ("buy".equals(fill.getSide())) {
                    buys.add(new double[]{fill.getSize(), fill.getPrice()});
                } else {
                    sells.add(new double[]{fill.getSize(), fill.getPrice()});
                }
            }

            double realizedPnl = 0;
            double totalFees = 0;
            int bi = 0, si = 0;

            while (bi < buys.size() && si < sells.size()) {
                double[] b = buys.get(bi);
                double[] s = sells.get(si);
                double matchSize = Math.min(b[0], s[0]);

                realizedPnl += matchSize * (s[1] - b[1]);
                totalFees += matchSize * b[1] * MAKER_FEE_PCT.doubleValue() / 100.0
                           + matchSize * s[1] * MAKER_FEE_PCT.doubleValue() / 100.0;

                b[0] -= matchSize;
                s[0] -= matchSize;

                if (b[0] < 0.0000001) bi++;
                if (s[0] < 0.0000001) si++;
            }

            // Get unrealized P&L from open position
            double unrealizedPnl = 0;
            try {
                var posResponse = krakenClient.getOpenPositions(state.isDemo()).block();
                if (posResponse != null && posResponse.getOpenPositions() != null) {
                    for (var pos : posResponse.getOpenPositions()) {
                        if (state.getInstrument().equals(pos.getSymbol())) {
                            double currentPrice = fetchCurrentPrice(state.getInstrument(), state.isDemo());
                            if (currentPrice > 0 && pos.getSize() != null && pos.getPrice() != null) {
                                double posSize = pos.getSize();
                                double entryPrice = pos.getPrice();
                                if ("long".equals(pos.getSide())) {
                                    unrealizedPnl = posSize * (currentPrice - entryPrice);
                                } else {
                                    unrealizedPnl = posSize * (entryPrice - currentPrice);
                                }
                            }
                        }
                    }
                }
            } catch (Exception e) {
                log.debug("Could not fetch positions for Kraken P&L: {}", e.getMessage());
            }

            state.setKrakenRealizedPnl(BigDecimal.valueOf(realizedPnl - totalFees).setScale(4, RoundingMode.HALF_UP));
            state.setKrakenUnrealizedPnl(BigDecimal.valueOf(unrealizedPnl).setScale(4, RoundingMode.HALF_UP));
            state.setKrakenTotalPnl(state.getKrakenRealizedPnl().add(state.getKrakenUnrealizedPnl()));

        } catch (Exception e) {
            log.debug("Could not fetch Kraken P&L: {}", e.getMessage());
        }
    }

    public Set<String> getActiveInstruments() {
        return activeGrids.keySet();
    }

    @Scheduled(fixedDelay = 10000)
    @Transactional
    public void pollGridOrders() {
        for (Map.Entry<String, GridState> entry : activeGrids.entrySet()) {
            GridState state = entry.getValue();
            if (!state.isActive()) continue;

            try {
                checkForFills(state);
                checkStopLoss(state);
                checkForRecenter(state);
            } catch (Exception e) {
                log.error("Grid poll error for {}: {}", entry.getKey(), e.getMessage());
            }
        }
    }

    private void checkForFills(GridState state) {
        KrakenOpenOrdersResponse response = krakenClient.getOpenOrders(state.isDemo()).block();
        if (response == null || response.getOpenOrders() == null) return;

        Set<String> openOrderIds = response.getOpenOrders().stream()
                .map(KrakenOpenOrdersResponse.Order::getOrderId)
                .collect(Collectors.toSet());

        boolean changed = false;
        for (GridLevel level : state.getLevels()) {
            if (level.getStatus() == GridLevel.GridLevelStatus.PLACED
                    && level.getKrakenOrderId() != null
                    && !openOrderIds.contains(level.getKrakenOrderId())) {
                handleFill(state, level);
                changed = true;
            }
        }

        if (changed) {
            persistState(state);
        }
    }

    private void handleFill(GridState state, GridLevel level) {
        log.info("Grid FILL [{}]: {} {} at {} (level {})",
                state.getGridMode(), level.getSide(), state.getInstrument(), level.getPrice(), level.getIndex());

        String fillSide = level.getSide();
        double fillPrice = level.getPrice();
        double fillProfit = 0;

        level.setStatus(GridLevel.GridLevelStatus.FILLED);
        level.setFilledAt(Instant.now());
        level.setKrakenOrderId(null);

        if (state.getGridMode() == GridMode.SHORT) {
            // SHORT mode: sell first, then buy to close
            fillProfit = handleFillShort(state, level);
        } else {
            // NEUTRAL (and LONG) mode: buy first, then sell to close
            fillProfit = handleFillNeutral(state, level);
        }

        // Record fill for chart markers
        state.getFills().add(GridFill.builder()
                .side(fillSide)
                .price(fillPrice)
                .filledAt(Instant.now())
                .profit(fillProfit)
                .build());
    }

    /**
     * NEUTRAL mode fill handling (existing logic, unchanged).
     * Cycle: buy -> sell (round-trip complete, profit counted)
     */
    private double handleFillNeutral(GridState state, GridLevel level) {
        double fillProfit = 0;

        if ("buy".equals(level.getSide())) {
            // Buy filled — mark that this level has a long position
            level.setHasBuyFill(true);

            double sellPrice = roundToTick(state.getInstrument(), level.getPrice() + state.getGridSpacing());
            if (hasLevelAtPrice(state, sellPrice, level.getIndex())) {
                log.info("Grid: skipping reverse sell @ {} (duplicate level exists)", sellPrice);
                level.setStatus(GridLevel.GridLevelStatus.WAITING);
                return 0;
            }
            level.setSide("sell");
            level.setPrice(sellPrice);
            placeGridOrder(state, level);
        } else {
            double buyPrice = roundToTick(state.getInstrument(), level.getPrice() - state.getGridSpacing());

            if (level.isHasBuyFill()) {
                // Sell after a buy = real round-trip, count profit
                double notional = state.getAmountPerLevel() * state.getLeverage();
                double size = notional / buyPrice;
                double grossProfit = state.getGridSpacing() * size;
                double fees = notional * MAKER_FEE_PCT.doubleValue() / 100.0 * 2;
                fillProfit = grossProfit - fees;

                state.setCompletedRoundTrips(state.getCompletedRoundTrips() + 1);
                state.setTotalProfit(state.getTotalProfit().add(BigDecimal.valueOf(fillProfit).setScale(4, RoundingMode.HALF_UP)));
                level.setRoundTrips(level.getRoundTrips() + 1);
                level.setHasBuyFill(false);

                log.info("Grid round trip #{} completed! Net profit: ${} (total: ${})",
                        state.getCompletedRoundTrips(), String.format("%.4f", fillProfit), state.getTotalProfit());
            } else {
                // Sell without prior buy = opening a short, no profit to count
                log.info("Grid SELL opening short at {} (no prior buy, no profit counted)", level.getPrice());
            }

            if (hasLevelAtPrice(state, buyPrice, level.getIndex())) {
                log.info("Grid: skipping reverse buy @ {} (duplicate level exists)", buyPrice);
                level.setStatus(GridLevel.GridLevelStatus.WAITING);
                return 0;
            }
            level.setSide("buy");
            level.setPrice(buyPrice);
            placeGridOrder(state, level);
        }

        return fillProfit;
    }

    /**
     * SHORT mode fill handling.
     * Cycle: sell first (open short) -> buy to close (round-trip complete, profit counted when price drops)
     */
    private double handleFillShort(GridState state, GridLevel level) {
        double fillProfit = 0;

        if ("sell".equals(level.getSide())) {
            // Sell filled — mark that this level has an open short position
            level.setHasSellFill(true);

            // Place a buy below to close the short (profit when price drops)
            double buyPrice = roundToTick(state.getInstrument(), level.getPrice() - state.getGridSpacing());
            if (hasLevelAtPrice(state, buyPrice, level.getIndex())) {
                log.info("Grid SHORT: skipping reverse buy @ {} (duplicate level exists)", buyPrice);
                level.setStatus(GridLevel.GridLevelStatus.WAITING);
                return 0;
            }
            level.setSide("buy");
            level.setPrice(buyPrice);
            placeGridOrder(state, level);

            log.info("Grid SHORT: sell filled at {}, placed buy at {} to close", level.getPrice() + state.getGridSpacing(), buyPrice);
        } else {
            // Buy filled
            double sellPrice = roundToTick(state.getInstrument(), level.getPrice() + state.getGridSpacing());

            if (level.isHasSellFill()) {
                // Buy after a sell = round-trip complete (short closed)
                // Profit = (sell price - buy price) * size - fees
                // The sell was at (current buy price + gridSpacing)
                double entryPrice = sellPrice; // the sell was placed at this price
                double notional = state.getAmountPerLevel() * state.getLeverage();
                double size = notional / entryPrice;
                double grossProfit = state.getGridSpacing() * size;
                double fees = notional * MAKER_FEE_PCT.doubleValue() / 100.0 * 2;
                fillProfit = grossProfit - fees;

                state.setCompletedRoundTrips(state.getCompletedRoundTrips() + 1);
                state.setTotalProfit(state.getTotalProfit().add(BigDecimal.valueOf(fillProfit).setScale(4, RoundingMode.HALF_UP)));
                level.setRoundTrips(level.getRoundTrips() + 1);
                level.setHasSellFill(false);

                log.info("Grid SHORT round trip #{} completed! Net profit: ${} (total: ${})",
                        state.getCompletedRoundTrips(), String.format("%.4f", fillProfit), state.getTotalProfit());
            } else {
                // Buy without prior sell = no profit to count
                log.info("Grid SHORT BUY at {} (no prior sell, no profit counted)", level.getPrice());
            }

            // Place a sell above to open a new short
            if (hasLevelAtPrice(state, sellPrice, level.getIndex())) {
                log.info("Grid SHORT: skipping reverse sell @ {} (duplicate level exists)", sellPrice);
                level.setStatus(GridLevel.GridLevelStatus.WAITING);
                return 0;
            }
            level.setSide("sell");
            level.setPrice(sellPrice);
            placeGridOrder(state, level);
        }

        return fillProfit;
    }

    private void checkStopLoss(GridState state) {
        if (state.getCapital() <= 0 || state.getMaxLossPercent() <= 0) return;

        double currentPrice = fetchCurrentPrice(state.getInstrument(), state.isDemo());
        if (currentPrice <= 0) return;

        double unrealizedPnl = 0;

        if (state.getGridMode() == GridMode.SHORT) {
            // SHORT mode: we hold short positions — profit when price drops
            // A sell level that flipped to buy means we hold a short position at (buyPrice + gridSpacing)
            for (GridLevel level : state.getLevels()) {
                if ("buy".equals(level.getSide()) && level.getStatus() == GridLevel.GridLevelStatus.PLACED
                        && level.isHasSellFill()) {
                    double entryPrice = level.getPrice() + state.getGridSpacing(); // sold at this price
                    double notional = state.getAmountPerLevel() * state.getLeverage();
                    double size = notional / entryPrice;
                    unrealizedPnl += (entryPrice - currentPrice) * size; // profit when price drops
                }
            }
        } else {
            // NEUTRAL/LONG mode: we hold long positions — profit when price rises
            // A buy level that flipped to sell means we hold a long position at (sellPrice - gridSpacing)
            for (GridLevel level : state.getLevels()) {
                if ("sell".equals(level.getSide()) && level.getStatus() == GridLevel.GridLevelStatus.PLACED) {
                    double entryPrice = level.getPrice() - state.getGridSpacing();
                    double notional = state.getAmountPerLevel() * state.getLeverage();
                    double size = notional / entryPrice;
                    unrealizedPnl += (currentPrice - entryPrice) * size;
                }
            }
        }

        double totalPnl = state.getTotalProfit().doubleValue() + unrealizedPnl;
        double maxLoss = state.getCapital() * state.getMaxLossPercent() / 100.0;

        if (totalPnl < -maxLoss) {
            log.warn("STOP LOSS triggered for {} — totalPnl=${} (realized=${}, unrealized=${}) > maxLoss=${}",
                    state.getInstrument(),
                    String.format("%.4f", totalPnl),
                    state.getTotalProfit(),
                    String.format("%.4f", unrealizedPnl),
                    String.format("%.2f", maxLoss));
            stopGrid(state.getInstrument());
        }
    }

    private void checkForRecenter(GridState state) {
        double currentPrice = fetchCurrentPrice(state.getInstrument(), state.isDemo());
        if (currentPrice <= 0) return;

        if (currentPrice > state.getUpperBound() || currentPrice < state.getLowerBound()) {
            log.info("Grid recenter for {} - price {} is outside [{}, {}]",
                    state.getInstrument(), currentPrice, state.getLowerBound(), state.getUpperBound());

            for (GridLevel level : state.getLevels()) {
                if (level.getStatus() == GridLevel.GridLevelStatus.PLACED && level.getKrakenOrderId() != null) {
                    cancelOrder(level.getKrakenOrderId(), state.isDemo());
                }
            }

            double halfRange = state.getGridSpacing() * (state.getTotalLevels() / 2);
            state.setCenterPrice(currentPrice);
            state.setUpperBound(roundToTick(state.getInstrument(), currentPrice + halfRange));
            state.setLowerBound(roundToTick(state.getInstrument(), currentPrice - halfRange));

            List<GridLevel> newLevels = new ArrayList<>();
            for (int i = 0; i < state.getTotalLevels(); i++) {
                double price = roundToTick(state.getInstrument(),
                        state.getLowerBound() + state.getGridSpacing() * i + state.getGridSpacing() / 2);
                String side;
                switch (state.getGridMode()) {
                    case SHORT:
                        side = "sell";
                        break;
                    case LONG:
                        side = "buy";
                        break;
                    default:
                        side = price < currentPrice ? "buy" : "sell";
                        break;
                }
                newLevels.add(GridLevel.builder()
                        .index(i)
                        .price(price)
                        .side(side)
                        .status(GridLevel.GridLevelStatus.WAITING)
                        .roundTrips(0)
                        .build());
            }
            state.setLevels(newLevels);

            log.info("Grid recentered [{}]: new range [{}, {}]", state.getGridMode(), state.getLowerBound(), state.getUpperBound());
            placeAllOrders(state);
            persistState(state);
        }
    }

    private String getSideForMode(GridMode mode, double price, double currentPrice) {
        if (mode == null) mode = GridMode.NEUTRAL;
        switch (mode) {
            case SHORT: return "sell";
            case LONG:  return "buy";
            default:    return price < currentPrice ? "buy" : "sell";
        }
    }

    private boolean hasLevelAtPrice(GridState state, double price, int excludeIndex) {
        for (GridLevel l : state.getLevels()) {
            if (l.getIndex() != excludeIndex && Math.abs(l.getPrice() - price) < 0.01) {
                return true;
            }
        }
        return false;
    }

    private void placeAllOrders(GridState state) {
        Set<Long> placedPrices = new HashSet<>();
        for (GridLevel level : state.getLevels()) {
            if (level.getStatus() == GridLevel.GridLevelStatus.WAITING) {
                // Close-only mode: skip entry orders, only place TP (exit) orders
                if (state.isCloseOnly()) {
                    boolean isEntryOrder = (state.getGridMode() == GridMode.SHORT)
                            ? "sell".equals(level.getSide())  // SHORT: sell is entry
                            : "buy".equals(level.getSide());  // NEUTRAL/LONG: buy is entry
                    if (isEntryOrder) {
                        log.info("CLOSE-ONLY: skipping entry order {} @ {} for {}", level.getSide(), level.getPrice(), state.getInstrument());
                        continue;
                    }
                }
                long priceKey = Math.round(level.getPrice() * 100000); // 5 decimal places dedup
                if (placedPrices.add(priceKey)) {
                    placeGridOrder(state, level);
                } else {
                    log.info("Grid: skipping duplicate order at {} for level #{}", level.getPrice(), level.getIndex());
                }
            }
        }
    }

    private void placeGridOrder(GridState state, GridLevel level) {
        double notional = state.getAmountPerLevel() * state.getLeverage();
        double size = notional / level.getPrice();

        // contractValueTradePrecision from Kraken instrument specs
        int precision;
        if (state.getInstrument().contains("XBT")) precision = 4;
        else if (state.getInstrument().contains("ADA")) precision = 0;
        else if (state.getInstrument().contains("DOT") || state.getInstrument().contains("LINK")) precision = 1;
        else if (state.getInstrument().contains("SOL") || state.getInstrument().contains("ETH")) precision = 2;
        else if (state.getInstrument().contains("XRP")) precision = 0;
        else precision = 0; // safe default: integers
        double factor = Math.pow(10, precision);
        size = Math.round(size * factor) / factor;

        if (size <= 0) {
            log.warn("Grid: size too small for level {} at {}", level.getIndex(), level.getPrice());
            return;
        }

        KrakenOrderRequest order = KrakenOrderRequest.builder()
                .orderType("lmt")
                .symbol(state.getInstrument())
                .side(level.getSide())
                .size(size)
                .limitPrice(level.getPrice())
                .reduceOnly(state.isCloseOnly())
                .build();

        final double orderSize = size;

        try {
            var r = krakenClient.sendOrder(order, state.isDemo()).block();
            if (r != null && "success".equals(r.getResult()) && r.getSendStatus() != null && "placed".equals(r.getSendStatus().getStatus())) {
                level.setKrakenOrderId(r.getSendStatus().getOrderId());
                level.setStatus(GridLevel.GridLevelStatus.PLACED);
                log.info("Grid order placed: {} {} lmt @ {} size={} orderId={}",
                        state.getInstrument(), level.getSide(),
                        level.getPrice(), orderSize, r.getSendStatus().getOrderId());
            } else {
                log.error("Grid order FAILED: {} {} @ {} - result={}, status={}, error={}",
                        state.getInstrument(), level.getSide(), level.getPrice(),
                        r != null ? r.getResult() : "null",
                        r != null && r.getSendStatus() != null ? r.getSendStatus().getStatus() : "null",
                        r != null ? r.getError() : "null");
            }
        } catch (Exception e) {
            log.error("Grid order ERROR: {} {} @ {} - {}", state.getInstrument(), level.getSide(), level.getPrice(), e.getMessage());
        }
    }

    private void cancelOrder(String orderId, boolean demo) {
        krakenClient.cancelOrder(orderId, demo)
                .publishOn(reactor.core.scheduler.Schedulers.boundedElastic())
                .subscribe(
                        r -> log.debug("Grid order cancelled: {}", orderId),
                        err -> log.warn("Grid cancel error for {}: {}", orderId, err.getMessage()));
    }

    private double fetchCurrentPrice(String instrument, boolean demo) {
        try {
            KrakenTickerResponse response = krakenClient.getTickers(demo).block();
            if (response != null && response.getTickers() != null) {
                return response.getTickers().stream()
                        .filter(t -> instrument.equals(t.getSymbol()))
                        .map(KrakenTickerResponse.Ticker::getLast)
                        .findFirst()
                        .orElse(0.0);
            }
        } catch (Exception e) {
            log.error("Failed to fetch price for {}: {}", instrument, e.getMessage());
        }
        return 0;
    }

    private double roundToTick(String instrument, double price) {
        BigDecimal tickSize;
        if (instrument.contains("XBT")) {
            tickSize = BigDecimal.ONE;
        } else if (instrument.contains("XRP")) {
            tickSize = new BigDecimal("0.00001");
        } else if (instrument.contains("ADA")) {
            tickSize = new BigDecimal("0.0001");
        } else if (instrument.contains("DOT") || instrument.contains("LINK")) {
            tickSize = new BigDecimal("0.001");
        } else if (instrument.contains("SOL") || instrument.contains("ETH")) {
            tickSize = new BigDecimal("0.01");
        } else {
            tickSize = new BigDecimal("0.1");
        }
        return BigDecimal.valueOf(price)
                .divide(tickSize, 0, RoundingMode.HALF_UP)
                .multiply(tickSize)
                .doubleValue();
    }

    /**
     * Check if there are open positions on Kraken for a given instrument.
     */
    public boolean hasOpenPositionsOnKraken(String instrument, boolean demo) {
        try {
            var posResponse = krakenClient.getOpenPositions(demo).block();
            if (posResponse != null && posResponse.getOpenPositions() != null) {
                return posResponse.getOpenPositions().stream()
                        .anyMatch(pos -> instrument.equals(pos.getSymbol())
                                && pos.getSize() != null
                                && Math.abs(pos.getSize()) > 0.0000001);
            }
        } catch (Exception e) {
            log.warn("Could not check positions for {}: {}", instrument, e.getMessage());
        }
        return false;
    }

    // --- Sync from Kraken ---

    /**
     * Reconstruct grid state from actual Kraken open orders and positions.
     * This allows any backend instance to "adopt" an existing grid.
     */
    @Transactional
    public GridState syncFromKraken(String instrument, double capital, int leverage, boolean demo,
                                    double gridSpacingPct, int totalLevels, double maxLossPercent, GridMode gridMode) {
        if (activeGrids.containsKey(instrument)) {
            throw new IllegalStateException("Grid already active for " + instrument + ". Stop it first.");
        }

        log.info("Syncing grid from Kraken for {} (demo={})", instrument, demo);

        // 1. Fetch open orders for this instrument
        KrakenOpenOrdersResponse ordersResponse = krakenClient.getOpenOrders(demo).block();
        List<KrakenOpenOrdersResponse.Order> instrumentOrders = new ArrayList<>();
        if (ordersResponse != null && ordersResponse.getOpenOrders() != null) {
            instrumentOrders = ordersResponse.getOpenOrders().stream()
                    .filter(o -> instrument.equals(o.getSymbol()))
                    .filter(o -> "lmt".equals(o.getOrderType()))
                    .sorted(Comparator.comparingDouble(KrakenOpenOrdersResponse.Order::getLimitPrice))
                    .collect(Collectors.toList());
        }

        log.info("Found {} open limit orders for {}", instrumentOrders.size(), instrument);

        if (instrumentOrders.isEmpty()) {
            throw new IllegalStateException("No open limit orders found for " + instrument + " on Kraken");
        }

        // 2. Detect grid spacing from orders
        double currentPrice = fetchCurrentPrice(instrument, demo);
        if (currentPrice <= 0) {
            throw new IllegalStateException("Cannot fetch price for " + instrument);
        }

        // Calculate grid spacing from the actual orders
        List<Double> prices = instrumentOrders.stream()
                .map(KrakenOpenOrdersResponse.Order::getLimitPrice)
                .sorted()
                .collect(Collectors.toList());

        double detectedSpacing = 0;
        if (prices.size() >= 2) {
            // Find most common spacing between adjacent prices
            Map<Long, Integer> spacingCount = new TreeMap<>();
            for (int i = 1; i < prices.size(); i++) {
                long spacingKey = Math.round((prices.get(i) - prices.get(i - 1)) * 10);
                spacingCount.merge(spacingKey, 1, Integer::sum);
            }
            long mostCommonKey = spacingCount.entrySet().stream()
                    .max(Map.Entry.comparingByValue())
                    .map(Map.Entry::getKey)
                    .orElse(0L);
            detectedSpacing = mostCommonKey / 10.0;
        }

        if (detectedSpacing <= 0) {
            // Fallback to configured spacing
            detectedSpacing = roundToTick(instrument, currentPrice * gridSpacingPct);
        }

        log.info("Detected grid spacing: ${}", detectedSpacing);

        // 3. Build grid levels from the actual orders
        double lowerBound = prices.get(0);
        double upperBound = prices.get(prices.size() - 1);
        double centerPrice = (lowerBound + upperBound) / 2.0;
        int detectedLevels = prices.size();
        double amountPerLevel = capital / detectedLevels;

        List<GridLevel> levels = new ArrayList<>();
        for (int i = 0; i < prices.size(); i++) {
            double price = prices.get(i);
            // Find the matching Kraken order
            KrakenOpenOrdersResponse.Order matchingOrder = instrumentOrders.stream()
                    .filter(o -> Math.abs(o.getLimitPrice() - price) < 0.01)
                    .findFirst()
                    .orElse(null);

            String side = matchingOrder != null ? matchingOrder.getSide() : (price < currentPrice ? "buy" : "sell");
            String krakenOrderId = matchingOrder != null ? matchingOrder.getOrderId() : null;

            levels.add(GridLevel.builder()
                    .index(i)
                    .price(price)
                    .side(side)
                    .status(krakenOrderId != null ? GridLevel.GridLevelStatus.PLACED : GridLevel.GridLevelStatus.WAITING)
                    .krakenOrderId(krakenOrderId)
                    .roundTrips(0)
                    .hasBuyFill("sell".equals(side) && price < currentPrice) // if sell below center, likely had a buy fill
                    .build());
        }

        // 4. Check open positions to detect hasBuyFill state
        try {
            var posResponse = krakenClient.getOpenPositions(demo).block();
            if (posResponse != null && posResponse.getOpenPositions() != null) {
                for (var pos : posResponse.getOpenPositions()) {
                    if (instrument.equals(pos.getSymbol()) && "long".equals(pos.getSide()) && pos.getSize() > 0) {
                        // We have a long position — mark sell levels as having a prior buy
                        for (GridLevel level : levels) {
                            if ("sell".equals(level.getSide())) {
                                level.setHasBuyFill(true);
                            }
                        }
                        log.info("Detected long position (size={}), marking sell levels with hasBuyFill", pos.getSize());
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Could not fetch positions during sync: {}", e.getMessage());
        }

        // 5. Fetch fills to reconstruct P&L
        BigDecimal totalProfit = BigDecimal.ZERO;
        int completedRoundTrips = 0;
        try {
            KrakenFillsResponse fillsResponse = krakenClient.getFills(demo).block();
            if (fillsResponse != null && "success".equals(fillsResponse.getResult()) && fillsResponse.getFills() != null) {
                long count = fillsResponse.getFills().stream()
                        .filter(f -> instrument.equals(f.getSymbol()))
                        .count();
                // Rough estimate: each pair of buy+sell = 1 round trip
                completedRoundTrips = (int) (count / 2);
                log.info("Detected ~{} fills, estimated {} round trips", count, completedRoundTrips);
            }
        } catch (Exception e) {
            log.debug("Could not fetch fills during sync: {}", e.getMessage());
        }

        // 6. Build state
        if (maxLossPercent <= 0) maxLossPercent = 50.0;

        GridState state = GridState.builder()
                .instrument(instrument)
                .active(true)
                .demo(demo)
                .centerPrice(centerPrice)
                .upperBound(upperBound)
                .lowerBound(lowerBound)
                .gridSpacing(detectedSpacing)
                .totalLevels(detectedLevels)
                .leverage(leverage)
                .amountPerLevel(amountPerLevel)
                .levels(levels)
                .totalProfit(totalProfit)
                .completedRoundTrips(completedRoundTrips)
                .startedAt(Instant.now())
                .fills(new ArrayList<>())
                .maxLossPercent(maxLossPercent)
                .capital(capital)
                .gridMode(gridMode != null ? gridMode : GridMode.NEUTRAL)
                .build();

        activeGrids.put(instrument, state);
        persistState(state);

        log.info("Grid synced for {} [{}] — {} levels, spacing=${}, range=[{}, {}], {} orders adopted",
                instrument, state.getGridMode(), detectedLevels, detectedSpacing, lowerBound, upperBound, instrumentOrders.size());

        return state;
    }

    // --- Market Analysis ---

    /**
     * Analyze historical data to assess if grid trading is a good idea right now.
     * Returns a map with volatility, trend, and recommendation.
     */
    public Map<String, Object> analyzeMarket(String instrument, boolean demo) {
        Map<String, Object> analysis = new LinkedHashMap<>();
        analysis.put("instrument", instrument);

        try {
            // Fetch 24h of 1m candles
            var ohlcData = krakenClient.getOhlc(instrument, 1440).block();

            if (ohlcData == null || !ohlcData.containsKey("candles")) {
                analysis.put("error", "Could not fetch historical data");
                return analysis;
            }

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> candles = (List<Map<String, Object>>) ohlcData.get("candles");
            if (candles == null || candles.size() < 60) {
                analysis.put("error", "Not enough historical data");
                return analysis;
            }

            // Extract close prices (Kraken returns strings)
            double[] closes = candles.stream()
                    .mapToDouble(c -> Double.parseDouble(c.get("close").toString()))
                    .toArray();

            double currentPrice = closes[closes.length - 1];
            analysis.put("currentPrice", currentPrice);
            analysis.put("dataPoints", closes.length);

            // --- Volatility (std deviation of 1m returns) ---
            double[] returns = new double[closes.length - 1];
            for (int i = 1; i < closes.length; i++) {
                returns[i - 1] = (closes[i] - closes[i - 1]) / closes[i - 1];
            }
            double meanReturn = Arrays.stream(returns).average().orElse(0);
            double variance = Arrays.stream(returns)
                    .map(r -> Math.pow(r - meanReturn, 2))
                    .average().orElse(0);
            double volatility1m = Math.sqrt(variance);
            double volatility1h = volatility1m * Math.sqrt(60);
            double volatility24h = volatility1m * Math.sqrt(1440);

            analysis.put("volatility1h", Math.round(volatility1h * 10000) / 100.0); // in %
            analysis.put("volatility24h", Math.round(volatility24h * 10000) / 100.0); // in %

            // --- Trend (price change over different periods) ---
            double price1hAgo = closes.length > 60 ? closes[closes.length - 61] : closes[0];
            double price4hAgo = closes.length > 240 ? closes[closes.length - 241] : closes[0];
            double price24hAgo = closes[0];

            double trend1h = (currentPrice - price1hAgo) / price1hAgo * 100;
            double trend4h = (currentPrice - price4hAgo) / price4hAgo * 100;
            double trend24h = (currentPrice - price24hAgo) / price24hAgo * 100;

            analysis.put("trend1h", Math.round(trend1h * 100) / 100.0);
            analysis.put("trend4h", Math.round(trend4h * 100) / 100.0);
            analysis.put("trend24h", Math.round(trend24h * 100) / 100.0);

            // --- Range (high/low over 24h) ---
            double high24h = candles.stream()
                    .mapToDouble(c -> Double.parseDouble(c.get("high").toString()))
                    .max().orElse(currentPrice);
            double low24h = candles.stream()
                    .mapToDouble(c -> Double.parseDouble(c.get("low").toString()))
                    .min().orElse(currentPrice);
            double range24hPct = (high24h - low24h) / low24h * 100;

            analysis.put("high24h", high24h);
            analysis.put("low24h", low24h);
            analysis.put("range24hPct", Math.round(range24hPct * 100) / 100.0);

            // --- Score and recommendation ---
            // Grid trading works best in ranging markets with moderate volatility
            int score = 0;
            List<String> reasons = new ArrayList<>();

            // Volatility check: too low = no profit, too high = risk
            if (volatility1h * 100 < 0.3) {
                score -= 2;
                reasons.add("Volatilité très faible — peu d'opportunités de round-trip");
            } else if (volatility1h * 100 < 0.8) {
                score += 2;
                reasons.add("Volatilité modérée — idéal pour le grid");
            } else if (volatility1h * 100 < 2.0) {
                score += 1;
                reasons.add("Volatilité élevée — grid possible mais risqué");
            } else {
                score -= 2;
                reasons.add("Volatilité extrême — risque de dépasser les bornes rapidement");
            }

            // Trend check: strong trend = bad for grid
            double absTrend4h = Math.abs(trend4h);
            if (absTrend4h < 0.5) {
                score += 2;
                reasons.add("Marché en range (tendance 4h faible) — parfait pour le grid");
            } else if (absTrend4h < 1.5) {
                score += 0;
                reasons.add("Tendance 4h modérée — grid acceptable avec recentrage");
            } else {
                score -= 2;
                reasons.add("Forte tendance 4h (" + String.format("%.1f", trend4h) + "%) — le grid va se faire balayer");
            }

            // 24h range vs grid spacing default
            double defaultSpacingPct = 0.7; // 0.7%
            double rangeToSpacing = range24hPct / defaultSpacingPct;
            if (rangeToSpacing >= 3 && rangeToSpacing <= 15) {
                score += 1;
                reasons.add("Range 24h (" + String.format("%.1f", range24hPct) + "%) compatible avec le spacing grid");
            } else if (rangeToSpacing > 15) {
                score -= 1;
                reasons.add("Range 24h très large (" + String.format("%.1f", range24hPct) + "%) — réduire le capital ou augmenter les niveaux");
            } else {
                score -= 1;
                reasons.add("Range 24h étroit (" + String.format("%.1f", range24hPct) + "%) — peu de place pour le grid");
            }

            // Score interpretation
            String recommendation;
            String signal;
            if (score >= 3) {
                recommendation = "Conditions favorables pour le grid trading";
                signal = "GO";
            } else if (score >= 1) {
                recommendation = "Conditions acceptables, attention aux paramètres";
                signal = "CAUTION";
            } else {
                recommendation = "Conditions défavorables — considérer d'attendre";
                signal = "WAIT";
            }

            analysis.put("score", score);
            analysis.put("signal", signal);
            analysis.put("recommendation", recommendation);
            analysis.put("reasons", reasons);

        } catch (Exception e) {
            log.error("Market analysis failed for {}: {}", instrument, e.getMessage());
            analysis.put("error", "Analysis failed: " + e.getMessage());
        }

        return analysis;
    }

    // --- Persistence ---

    private void persistState(GridState state) {
        try {
            GridStateEntity entity = gridStateRepository.findByInstrument(state.getInstrument())
                    .orElse(new GridStateEntity());

            entity.setInstrument(state.getInstrument());
            entity.setActive(state.isActive());
            entity.setDemo(state.isDemo());
            entity.setCenterPrice(state.getCenterPrice());
            entity.setUpperBound(state.getUpperBound());
            entity.setLowerBound(state.getLowerBound());
            entity.setGridSpacing(state.getGridSpacing());
            entity.setTotalLevels(state.getTotalLevels());
            entity.setLeverage(state.getLeverage());
            entity.setAmountPerLevel(state.getAmountPerLevel());
            entity.setCapital(state.getCapital());
            entity.setMaxLossPercent(state.getMaxLossPercent());
            entity.setGridMode(state.getGridMode() != null ? state.getGridMode().name() : "NEUTRAL");
            entity.setTotalProfit(state.getTotalProfit());
            entity.setCompletedRoundTrips(state.getCompletedRoundTrips());
            entity.setStartedAt(state.getStartedAt());

            // Sync levels
            entity.getLevels().clear();
            for (GridLevel l : state.getLevels()) {
                entity.getLevels().add(GridLevelEntity.builder()
                        .gridState(entity)
                        .idx(l.getIndex())
                        .price(l.getPrice())
                        .side(l.getSide())
                        .status(l.getStatus().name())
                        .krakenOrderId(l.getKrakenOrderId())
                        .filledAt(l.getFilledAt())
                        .roundTrips(l.getRoundTrips())
                        .hasBuyFill(l.isHasBuyFill())
                        .hasSellFill(l.isHasSellFill())
                        .build());
            }

            // Sync fills
            entity.getFills().clear();
            for (GridFill f : state.getFills()) {
                entity.getFills().add(GridFillEntity.builder()
                        .gridState(entity)
                        .side(f.getSide())
                        .price(f.getPrice())
                        .filledAt(f.getFilledAt())
                        .profit(f.getProfit())
                        .build());
            }

            gridStateRepository.save(entity);
        } catch (Exception e) {
            log.error("Failed to persist grid state for {}: {}", state.getInstrument(), e.getMessage());
        }
    }

    private GridState fromEntity(GridStateEntity entity) {
        List<GridLevel> levels = entity.getLevels().stream()
                .map(l -> GridLevel.builder()
                        .index(l.getIdx())
                        .price(l.getPrice())
                        .side(l.getSide())
                        .status(GridLevel.GridLevelStatus.valueOf(l.getStatus()))
                        .krakenOrderId(l.getKrakenOrderId())
                        .filledAt(l.getFilledAt())
                        .roundTrips(l.getRoundTrips())
                        .hasBuyFill(l.isHasBuyFill())
                        .hasSellFill(l.isHasSellFill())
                        .build())
                .collect(Collectors.toList());

        List<GridFill> fills = entity.getFills().stream()
                .map(f -> GridFill.builder()
                        .side(f.getSide())
                        .price(f.getPrice())
                        .filledAt(f.getFilledAt())
                        .profit(f.getProfit())
                        .build())
                .collect(Collectors.toList());

        return GridState.builder()
                .instrument(entity.getInstrument())
                .active(entity.isActive())
                .demo(entity.isDemo())
                .centerPrice(entity.getCenterPrice())
                .upperBound(entity.getUpperBound())
                .lowerBound(entity.getLowerBound())
                .gridSpacing(entity.getGridSpacing())
                .totalLevels(entity.getTotalLevels())
                .leverage(entity.getLeverage())
                .amountPerLevel(entity.getAmountPerLevel())
                .capital(entity.getCapital())
                .maxLossPercent(entity.getMaxLossPercent() > 0 ? entity.getMaxLossPercent() : 50.0)
                .gridMode(entity.getGridMode() != null ? GridMode.valueOf(entity.getGridMode()) : GridMode.NEUTRAL)
                .levels(levels)
                .totalProfit(entity.getTotalProfit())
                .completedRoundTrips(entity.getCompletedRoundTrips())
                .startedAt(entity.getStartedAt())
                .fills(fills)
                .build();
    }
}
