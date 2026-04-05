package com.martin.position;

import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenOpenOrdersResponse;
import com.martin.kraken.dto.KrakenOrderRequest;
import com.martin.kraken.dto.KrakenOrderResponse;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class PositionService {

    private static final Logger log = LoggerFactory.getLogger(PositionService.class);
    private final Map<String, PositionState> positions = new ConcurrentHashMap<>();

    @Autowired
    private KrakenFuturesRestClient krakenClient;

    @Autowired
    private PositionRepository positionRepository;

    /**
     * On startup, recover all active positions from the database.
     * Verify they still have open orders on Kraken and log any mismatches.
     */
    @PostConstruct
    public void recoverPositions() {
        log.info("Recovering active positions from database...");
        List<PositionState> activePositions = positionRepository.findByActiveTrue();

        if (activePositions.isEmpty()) {
            log.info("No active positions to recover");
            return;
        }

        for (PositionState pos : activePositions) {
            positions.put(pos.getInstrument(), pos);
            log.info("Recovered position: {} {} {} size={} entry={}",
                    pos.getDirection(), pos.getInstrument(), pos.getStatus(),
                    pos.getSize(), pos.getEntryPrice());
        }

        // Verify against Kraken open orders
        try {
            // Check both live and demo
            verifyAgainstKraken(false);
            verifyAgainstKraken(true);
        } catch (Exception e) {
            log.warn("Could not verify positions against Kraken: {}", e.getMessage());
        }

        log.info("Position recovery complete: {} positions loaded", activePositions.size());
    }

    private void verifyAgainstKraken(boolean demo) {
        try {
            KrakenOpenOrdersResponse openOrders = krakenClient.getOpenOrders(demo).block();
            if (openOrders == null || openOrders.getOpenOrders() == null) return;

            for (PositionState pos : positions.values()) {
                if (pos.isDemo() != demo) continue;
                if (!pos.isActive()) continue;

                // Check if SL order still exists
                boolean slFound = false;
                boolean tpFound = false;
                if (pos.getSlOrderId() != null) {
                    slFound = openOrders.getOpenOrders().stream()
                            .anyMatch(o -> pos.getSlOrderId().equals(o.getOrderId()));
                }
                if (pos.getTpOrderId() != null) {
                    tpFound = openOrders.getOpenOrders().stream()
                            .anyMatch(o -> pos.getTpOrderId().equals(o.getOrderId()));
                }

                if (!slFound && pos.getSlOrderId() != null) {
                    log.warn("MISMATCH: SL order {} for {} not found on Kraken (may have been filled)",
                            pos.getSlOrderId(), pos.getInstrument());
                }
                if (!tpFound && pos.getTpOrderId() != null) {
                    log.warn("MISMATCH: TP order {} for {} not found on Kraken (may have been filled)",
                            pos.getTpOrderId(), pos.getInstrument());
                }

                // If neither SL nor TP found, position may have been closed
                if (!slFound && !tpFound && pos.getSlOrderId() != null && pos.getTpOrderId() != null) {
                    log.warn("MISMATCH: Both SL and TP orders missing for {} — position may have been closed externally",
                            pos.getInstrument());
                }
            }
        } catch (Exception e) {
            log.warn("Kraken order verification failed for demo={}: {}", demo, e.getMessage());
        }
    }

    public PositionState openShort(String instrument, double capital, int leverage,
                                   double slPct, double tpPct, boolean demo) {
        return openPosition(instrument, "SHORT", capital, leverage, slPct, tpPct, demo);
    }

    public PositionState openLong(String instrument, double capital, int leverage,
                                  double slPct, double tpPct, boolean demo) {
        return openPosition(instrument, "LONG", capital, leverage, slPct, tpPct, demo);
    }

    private PositionState openPosition(String instrument, String direction, double capital,
                                        int leverage, double slPct, double tpPct, boolean demo) {
        if (positions.containsKey(instrument) && positions.get(instrument).isActive()) {
            throw new IllegalStateException("Position already active for " + instrument);
        }

        String entrySide = direction.equals("SHORT") ? "sell" : "buy";
        String closeSide = direction.equals("SHORT") ? "buy" : "sell";

        double currentPrice = getCurrentPrice(instrument);
        if (currentPrice <= 0) throw new IllegalStateException("Could not get price for " + instrument);

        double notional = capital * leverage;
        double size = Math.round((notional / currentPrice) * 10000.0) / 10000.0;
        if (size < 0.001) size = 0.001;

        log.info("Opening {} {} x{}: price={} size={}", direction, instrument, leverage, currentPrice, size);

        KrakenOrderRequest entryOrder = KrakenOrderRequest.builder()
                .orderType("mkt").symbol(instrument).side(entrySide).size(size).build();

        KrakenOrderResponse entryResp = krakenClient.sendOrder(entryOrder, demo).block();
        String entryOrderId = extractOrderId(entryResp);
        log.info("Entry: {} {}", entryOrderId, entryResp != null ? entryResp.getResult() : "null");

        double fillPrice = currentPrice;

        double slPrice = direction.equals("SHORT")
                ? roundToTick(fillPrice * (1 + slPct / 100), instrument)
                : roundToTick(fillPrice * (1 - slPct / 100), instrument);

        KrakenOrderRequest slOrder = KrakenOrderRequest.builder()
                .orderType("stp").symbol(instrument).side(closeSide).size(size)
                .stopPrice(slPrice).reduceOnly(true).triggerSignal("last_price").build();

        KrakenOrderResponse slResp = krakenClient.sendOrder(slOrder, demo).block();
        String slOrderId = extractOrderId(slResp);
        log.info("SL at {}: {} {}", slPrice, slOrderId, slResp != null ? slResp.getResult() : "null");

        double tpPrice = direction.equals("SHORT")
                ? roundToTick(fillPrice * (1 - tpPct / 100), instrument)
                : roundToTick(fillPrice * (1 + tpPct / 100), instrument);

        KrakenOrderRequest tpOrder = KrakenOrderRequest.builder()
                .orderType("lmt").symbol(instrument).side(closeSide).size(size)
                .limitPrice(tpPrice).reduceOnly(true).build();

        KrakenOrderResponse tpResp = krakenClient.sendOrder(tpOrder, demo).block();
        String tpOrderId = extractOrderId(tpResp);
        log.info("TP at {}: {} {}", tpPrice, tpOrderId, tpResp != null ? tpResp.getResult() : "null");

        PositionState state = new PositionState();
        state.setInstrument(instrument);
        state.setActive(true);
        state.setDirection(direction);
        state.setEntryPrice(fillPrice);
        state.setSize(size);
        state.setCapital(capital);
        state.setLeverage(leverage);
        state.setSlPct(slPct);
        state.setTpPct(tpPct);
        state.setSlPrice(slPrice);
        state.setTpPrice(tpPrice);
        state.setEntryOrderId(entryOrderId);
        state.setSlOrderId(slOrderId);
        state.setTpOrderId(tpOrderId);
        state.setStatus("OPEN");
        state.setStartedAt(Instant.now());
        state.setDemo(String.valueOf(demo));

        // Persist to database
        positionRepository.save(state);

        positions.put(instrument, state);
        return state;
    }

    public PositionState closePosition(String instrument) {
        PositionState state = positions.get(instrument);
        if (state == null || !state.isActive()) {
            throw new IllegalStateException("No active position for " + instrument);
        }

        boolean demo = state.isDemo();
        String closeSide = state.getDirection().equals("SHORT") ? "buy" : "sell";

        if (state.getSlOrderId() != null) {
            try { krakenClient.cancelOrder(state.getSlOrderId(), demo).block(); } catch (Exception e) { log.warn("Cancel SL: {}", e.getMessage()); }
        }
        if (state.getTpOrderId() != null) {
            try { krakenClient.cancelOrder(state.getTpOrderId(), demo).block(); } catch (Exception e) { log.warn("Cancel TP: {}", e.getMessage()); }
        }

        KrakenOrderRequest closeOrder = KrakenOrderRequest.builder()
                .orderType("mkt").symbol(instrument).side(closeSide)
                .size(state.getSize()).reduceOnly(true).build();
        krakenClient.sendOrder(closeOrder, demo).block();

        double closePrice = getCurrentPrice(instrument);
        double pnl = state.getDirection().equals("SHORT")
                ? (state.getEntryPrice() - closePrice) * state.getSize()
                : (closePrice - state.getEntryPrice()) * state.getSize();

        state.setActive(false);
        state.setStatus("CLOSED");
        state.setRealizedPnl(pnl);

        // Persist to database
        positionRepository.save(state);

        log.info("Closed {} PnL={}", instrument, pnl);
        return state;
    }

    public PositionState getStatus(String instrument) {
        return positions.get(instrument);
    }

    public Map<String, PositionState> getAllPositions() {
        return positions;
    }

    private double getCurrentPrice(String instrument) {
        try {
            var tickers = krakenClient.getTickers(false).block();
            if (tickers != null && tickers.getTickers() != null) {
                return tickers.getTickers().stream()
                        .filter(t -> instrument.equals(t.getSymbol()))
                        .mapToDouble(t -> t.getLast())
                        .findFirst().orElse(0);
            }
        } catch (Exception e) { log.error("Price: {}", e.getMessage()); }
        return 0;
    }

    private String extractOrderId(KrakenOrderResponse resp) {
        if (resp == null || resp.getSendStatus() == null) return null;
        return resp.getSendStatus().getOrderId();
    }

    private double roundToTick(double price, String instrument) {
        double tick = (instrument.contains("XBT") || instrument.contains("BTC")) ? 1.0
                    : instrument.contains("ETH") ? 0.1
                    : instrument.contains("SOL") ? 0.01 : 0.0001;
        return Math.round(price / tick) * tick;
    }
}
