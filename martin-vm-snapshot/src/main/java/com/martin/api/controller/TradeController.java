package com.martin.api.controller;

import com.martin.api.dto.TradeDto;
import com.martin.domain.entity.Trade;
import com.martin.domain.enums.Direction;
import com.martin.domain.enums.TradeStatus;
import com.martin.domain.repository.TradeRepository;
import com.martin.domain.repository.TradeSeriesRepository;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenFillsResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.transaction.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/trades")
@RequiredArgsConstructor
public class TradeController {

    private static final Logger log = LoggerFactory.getLogger(TradeController.class);

    private final TradeRepository tradeRepository;
    private final TradeSeriesRepository tradeSeriesRepository;
    private final KrakenFuturesRestClient krakenClient;

    @GetMapping("/{instrument}")
    public ResponseEntity<List<TradeDto>> getTradeHistory(@PathVariable String instrument) {
        List<TradeDto> trades = tradeRepository.findByInstrumentOrderByOpenedAtDesc(instrument)
                .stream()
                .map(this::toDto)
                .toList();
        log.debug(">> GET /trades/{} -> {} trades", instrument, trades.size());
        return ResponseEntity.ok(trades);
    }

    @GetMapping("/all")
    public ResponseEntity<List<TradeDto>> getAllTrades() {
        List<TradeDto> trades = tradeRepository.findAllByOrderByClosedAtAsc()
                .stream()
                .map(this::toDto)
                .toList();
        return ResponseEntity.ok(trades);
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getTradeStats(
            @RequestParam(required = false) String instrument) {

        List<Trade> trades;
        if (instrument != null && !instrument.isEmpty() && !instrument.equals("ALL")) {
            trades = tradeRepository.findByInstrumentOrderByClosedAtAsc(instrument);
        } else {
            trades = tradeRepository.findAllByOrderByClosedAtAsc();
        }

        List<Trade> closed = trades.stream()
                .filter(t -> t.getStatus() == TradeStatus.WON || t.getStatus() == TradeStatus.LOST)
                .toList();

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalTrades", closed.size());

        if (closed.isEmpty()) {
            stats.put("totalPnl", 0);
            stats.put("wins", 0);
            stats.put("losses", 0);
            stats.put("winRate", 0);
            stats.put("avgWin", 0);
            stats.put("avgLoss", 0);
            stats.put("bestTrade", 0);
            stats.put("worstTrade", 0);
            stats.put("profitFactor", 0);
            stats.put("maxDrawdown", 0);
            stats.put("totalFees", 0);
            stats.put("equityCurve", List.of());
            return ResponseEntity.ok(stats);
        }

        long wins = closed.stream().filter(t -> t.getStatus() == TradeStatus.WON).count();
        long losses = closed.stream().filter(t -> t.getStatus() == TradeStatus.LOST).count();
        double totalPnl = closed.stream()
                .mapToDouble(t -> t.getPnl() != null ? t.getPnl().doubleValue() : 0)
                .sum();
        double totalFees = closed.stream()
                .mapToDouble(t -> t.getFees() != null ? t.getFees().doubleValue() : 0)
                .sum();

        double grossProfit = closed.stream()
                .filter(t -> t.getPnl() != null && t.getPnl().doubleValue() > 0)
                .mapToDouble(t -> t.getPnl().doubleValue())
                .sum();
        double grossLoss = Math.abs(closed.stream()
                .filter(t -> t.getPnl() != null && t.getPnl().doubleValue() < 0)
                .mapToDouble(t -> t.getPnl().doubleValue())
                .sum());

        double avgWin = wins > 0 ? grossProfit / wins : 0;
        double avgLoss = losses > 0 ? grossLoss / losses : 0;
        double bestTrade = closed.stream()
                .mapToDouble(t -> t.getPnl() != null ? t.getPnl().doubleValue() : 0)
                .max().orElse(0);
        double worstTrade = closed.stream()
                .mapToDouble(t -> t.getPnl() != null ? t.getPnl().doubleValue() : 0)
                .min().orElse(0);
        double profitFactor = grossLoss > 0 ? grossProfit / grossLoss : (grossProfit > 0 ? 999 : 0);

        // Equity curve + max drawdown
        List<Map<String, Object>> equityCurve = new ArrayList<>();
        double cumPnl = 0;
        double peak = 0;
        double maxDrawdown = 0;
        for (Trade t : closed) {
            double pnl = t.getPnl() != null ? t.getPnl().doubleValue() : 0;
            cumPnl += pnl;
            if (cumPnl > peak) peak = cumPnl;
            double dd = peak - cumPnl;
            if (dd > maxDrawdown) maxDrawdown = dd;

            Map<String, Object> point = new LinkedHashMap<>();
            point.put("time", t.getClosedAt() != null ? t.getClosedAt().getEpochSecond() : 0);
            point.put("value", Math.round(cumPnl * 10000.0) / 10000.0);
            equityCurve.add(point);
        }

        stats.put("totalPnl", Math.round(totalPnl * 10000.0) / 10000.0);
        stats.put("wins", wins);
        stats.put("losses", losses);
        stats.put("winRate", closed.size() > 0 ? Math.round(wins * 1000.0 / closed.size()) / 10.0 : 0);
        stats.put("avgWin", Math.round(avgWin * 10000.0) / 10000.0);
        stats.put("avgLoss", Math.round(avgLoss * 10000.0) / 10000.0);
        stats.put("bestTrade", Math.round(bestTrade * 10000.0) / 10000.0);
        stats.put("worstTrade", Math.round(worstTrade * 10000.0) / 10000.0);
        stats.put("profitFactor", Math.round(profitFactor * 100.0) / 100.0);
        stats.put("maxDrawdown", Math.round(maxDrawdown * 10000.0) / 10000.0);
        stats.put("totalFees", Math.round(totalFees * 10000.0) / 10000.0);
        stats.put("equityCurve", equityCurve);

        return ResponseEntity.ok(stats);
    }

    @PostMapping("/sync")
    @Transactional
    public ResponseEntity<Map<String, Object>> syncFillsFromKraken(
            @RequestParam(defaultValue = "false") boolean demo) {
        log.info(">> POST /trades/sync (demo={})", demo);

        KrakenFillsResponse response = krakenClient.getFills(demo).block();
        if (response == null || response.getFills() == null) {
            return ResponseEntity.ok(Map.of("synced", 0, "message", "No fills returned from Kraken"));
        }

        // Delete old synced trades — we re-import with proper matching each time
        int deleted = tradeRepository.deleteBySource("kraken-fill");
        log.info(">> Deleted {} old kraken-fill trades", deleted);

        List<KrakenFillsResponse.Fill> allFills = response.getFills();

        // Group fills by instrument, sorted by time
        Map<String, List<KrakenFillsResponse.Fill>> fillsByInstrument = allFills.stream()
                .sorted(Comparator.comparing(f -> parseFillTime(f.getFillTime())))
                .collect(Collectors.groupingBy(KrakenFillsResponse.Fill::getSymbol,
                        LinkedHashMap::new, Collectors.toList()));

        int synced = 0;
        int openPositions = 0;

        for (Map.Entry<String, List<KrakenFillsResponse.Fill>> entry : fillsByInstrument.entrySet()) {
            String instrument = entry.getKey();
            List<KrakenFillsResponse.Fill> fills = entry.getValue();

            // FIFO matching: track open fills queue and net position
            Deque<double[]> openQueue = new ArrayDeque<>(); // [price, remainingSize, timeEpoch]
            List<String> openFillIds = new ArrayList<>();
            double position = 0; // positive = long, negative = short

            for (KrakenFillsResponse.Fill fill : fills) {
                boolean isBuy = "buy".equalsIgnoreCase(fill.getSide());
                double fillSize = fill.getSize();
                double fillPrice = fill.getPrice();
                Instant fillTime = parseFillTime(fill.getFillTime());
                double fillDir = isBuy ? 1.0 : -1.0;

                // Fee rate: maker 0.02%, taker 0.05% — use taker as default
                double feeRate = "maker".equalsIgnoreCase(fill.getFillType()) ? 0.0002 : 0.0005;

                // Does this fill reduce the current position?
                boolean reduces = (position > 1e-9 && !isBuy) || (position < -1e-9 && isBuy);

                if (reduces) {
                    double remaining = fillSize;

                    while (remaining > 1e-9 && !openQueue.isEmpty()) {
                        double[] open = openQueue.peek();
                        double openPrice = open[0];
                        double openSize = open[1];
                        Instant openTime = Instant.ofEpochMilli((long) open[2]);

                        double matchSize = Math.min(remaining, openSize);
                        Direction dir = position > 0 ? Direction.LONG : Direction.SHORT;

                        double pnl;
                        if (dir == Direction.LONG) {
                            pnl = (fillPrice - openPrice) * matchSize;
                        } else {
                            pnl = (openPrice - fillPrice) * matchSize;
                        }

                        // Fees on both entry and exit legs
                        double entryFee = openPrice * matchSize * feeRate;
                        double exitFee = fillPrice * matchSize * feeRate;
                        double totalFees = entryFee + exitFee;
                        double netPnl = pnl - totalFees;

                        Trade trade = Trade.builder()
                                .instrument(instrument)
                                .krakenOrderId(fill.getOrderId())
                                .krakenFillId(fill.getFillId())
                                .source("kraken-fill")
                                .direction(dir)
                                .status(netPnl >= 0 ? TradeStatus.WON : TradeStatus.LOST)
                                .stake(BigDecimal.valueOf(matchSize))
                                .leverage(1)
                                .entryPrice(BigDecimal.valueOf(openPrice))
                                .exitPrice(BigDecimal.valueOf(fillPrice))
                                .pnl(BigDecimal.valueOf(netPnl).setScale(4, RoundingMode.HALF_UP))
                                .fees(BigDecimal.valueOf(totalFees).setScale(4, RoundingMode.HALF_UP))
                                .doublingStep(0)
                                .openedAt(openTime)
                                .closedAt(fillTime)
                                .build();
                        tradeRepository.save(trade);
                        synced++;

                        remaining -= matchSize;
                        open[1] -= matchSize;
                        if (open[1] < 1e-9) {
                            openQueue.poll();
                            if (!openFillIds.isEmpty()) openFillIds.remove(0);
                        }
                    }

                    position += fillDir * fillSize;

                    // If remaining after closing, this opens a new position in opposite direction
                    if (remaining > 1e-9) {
                        openQueue.add(new double[]{fillPrice, remaining, fillTime.toEpochMilli()});
                        openFillIds.add(fill.getFillId());
                    }
                } else {
                    // Opening or adding to position
                    openQueue.add(new double[]{fillPrice, fillSize, fillTime.toEpochMilli()});
                    openFillIds.add(fill.getFillId());
                    position += fillDir * fillSize;
                }
            }

            if (!openQueue.isEmpty()) {
                openPositions += openQueue.size();
                log.info(">> {} has {} open fill(s) not yet matched (current position)", instrument, openQueue.size());
            }
        }

        log.info(">> Synced {} round-trip trades from {} fills ({} open positions remaining)",
                synced, allFills.size(), openPositions);
        return ResponseEntity.ok(Map.of(
                "synced", synced,
                "totalFills", allFills.size(),
                "openPositions", openPositions,
                "message", synced + " round-trip trades from " + allFills.size() + " fills"
        ));
    }

    @DeleteMapping
    public ResponseEntity<String> deleteAllTrades() {
        log.info(">> DELETE /trades (all)");
        tradeRepository.deleteAll();
        tradeSeriesRepository.deleteAll();
        return ResponseEntity.ok("All trades and series deleted");
    }

    private TradeDto toDto(Trade trade) {
        return TradeDto.builder()
                .id(trade.getId())
                .instrument(trade.getInstrument())
                .direction(trade.getDirection() != null ? trade.getDirection().name() : null)
                .status(trade.getStatus() != null ? trade.getStatus().name() : null)
                .source(trade.getSource())
                .stake(trade.getStake())
                .leverage(trade.getLeverage())
                .entryPrice(trade.getEntryPrice())
                .exitPrice(trade.getExitPrice())
                .pnl(trade.getPnl())
                .fees(trade.getFees())
                .doublingStep(trade.getDoublingStep())
                .openedAt(trade.getOpenedAt())
                .closedAt(trade.getClosedAt())
                .build();
    }

    private Instant parseFillTime(String fillTime) {
        if (fillTime == null) return Instant.now();
        try {
            return ZonedDateTime.parse(fillTime, DateTimeFormatter.ISO_DATE_TIME).toInstant();
        } catch (Exception e) {
            try {
                return Instant.parse(fillTime);
            } catch (Exception e2) {
                return Instant.now();
            }
        }
    }
}
