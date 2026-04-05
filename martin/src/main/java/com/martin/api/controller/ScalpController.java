package com.martin.api.controller;

import com.martin.api.dto.ScalpOrderRequest;
import com.martin.api.dto.ScalpOrderResponse;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.dto.KrakenOrderRequest;
import com.martin.kraken.dto.KrakenOrderResponse;
import com.martin.kraken.dto.KrakenPositionResponse;
import com.martin.scalping.ScalpingBotService;
import com.martin.scalping.ScalpingBotState;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

import java.util.Set;

@RestController
@RequestMapping("/api/scalp")
@RequiredArgsConstructor
public class ScalpController {

    private static final Logger log = LoggerFactory.getLogger(ScalpController.class);

    private final KrakenFuturesRestClient krakenClient;
    private final ScalpingBotService scalpingBotService;

    // --- Manual scalp order (kept for compatibility) ---

    @PostMapping("/order")
    public ScalpOrderResponse placeOrder(@RequestBody ScalpOrderRequest request) {
        log.info("Scalp order: {} {} {} (demo={}, reduceOnly={})",
                request.getSide(), request.getSize(), request.getInstrument(),
                request.isDemo(), request.isReduceOnly());

        KrakenOrderRequest krakenOrder = KrakenOrderRequest.builder()
                .orderType("mkt")
                .symbol(request.getInstrument())
                .side(request.getSide())
                .size(request.getSize())
                .reduceOnly(request.isReduceOnly() ? true : null)
                .build();

        try {
            KrakenOrderResponse response = krakenClient.sendOrder(krakenOrder, request.isDemo()).block();
            if (response != null && "success".equals(response.getResult())) {
                String orderId = response.getSendStatus() != null ? response.getSendStatus().getOrderId() : null;
                return new ScalpOrderResponse(true, orderId, null);
            } else {
                String error = response != null ? response.getError() : "No response";
                return new ScalpOrderResponse(false, null, error);
            }
        } catch (Exception e) {
            log.error("Scalp order failed: {}", e.getMessage());
            return new ScalpOrderResponse(false, null, e.getMessage());
        }
    }

    @GetMapping("/positions")
    public KrakenPositionResponse getPositions(@RequestParam(defaultValue = "false") boolean demo) {
        return krakenClient.getOpenPositions(demo).block();
    }

    // --- Auto scalping bot ---

    @PostMapping("/bot/start")
    public ScalpingBotState startBot(
            @RequestParam String instrument,
            @RequestParam double capital,
            @RequestParam double leverage,
            @RequestParam(defaultValue = "false") boolean demo,
            @RequestParam(defaultValue = "true") boolean tradingHoursEnabled) {
        return scalpingBotService.startBot(instrument, capital, leverage, demo, tradingHoursEnabled);
    }

    @PostMapping("/bot/trading-hours/{instrument}")
    public String setTradingHours(@PathVariable String instrument,
                                  @RequestParam boolean enabled) {
        scalpingBotService.setTradingHoursEnabled(instrument, enabled);
        return "Trading hours filter " + (enabled ? "enabled" : "disabled") + " for " + instrument;
    }

    @PostMapping("/bot/stop/{instrument}")
    public String stopBot(@PathVariable String instrument) {
        scalpingBotService.stopBot(instrument);
        return "Scalping bot stopped for " + instrument;
    }

    @GetMapping("/bot/status/{instrument}")
    public ScalpingBotState getStatus(@PathVariable String instrument) {
        ScalpingBotState state = scalpingBotService.getState(instrument);
        if (state == null) {
            throw new IllegalStateException("No scalping bot for " + instrument);
        }
        return state;
    }

    @GetMapping("/bot/active")
    public Set<String> getActive() {
        return scalpingBotService.getActiveInstruments();
    }
}
