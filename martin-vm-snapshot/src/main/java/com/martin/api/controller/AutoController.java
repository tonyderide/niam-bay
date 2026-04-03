package com.martin.api.controller;

import com.martin.auto.AutoBotState;
import com.martin.auto.AutoTradingService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/auto")
@RequiredArgsConstructor
public class AutoController {

    private static final Logger log = LoggerFactory.getLogger(AutoController.class);
    private final AutoTradingService autoService;

    @PostMapping("/start")
    public ResponseEntity<?> startBot(
            @RequestParam(defaultValue = "PF_ETHUSD") String instrument,
            @RequestParam(defaultValue = "14") double capital,
            @RequestParam(defaultValue = "10") double leverage,
            @RequestParam(defaultValue = "false") boolean demo) {
        log.info(">> POST /auto/start instrument={}, capital={}, leverage={}, demo={}", instrument, capital, leverage, demo);
        try {
            AutoBotState state = autoService.startBot(instrument, capital, leverage, demo);
            return ResponseEntity.ok(state);
        } catch (Exception e) {
            log.error("Failed to start auto bot: {}", e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @PostMapping("/stop/{instrument}")
    public ResponseEntity<?> stopBot(@PathVariable String instrument) {
        log.info(">> POST /auto/stop/{}", instrument);
        try {
            autoService.stopBot(instrument);
            return ResponseEntity.ok(Map.of("message", "Auto bot stopped for " + instrument));
        } catch (Exception e) {
            log.error("Failed to stop auto bot: {}", e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/status/{instrument}")
    public ResponseEntity<?> getStatus(@PathVariable String instrument) {
        AutoBotState state = autoService.getState(instrument);
        if (state == null) {
            return ResponseEntity.ok(Map.of("active", false, "instrument", instrument));
        }
        return ResponseEntity.ok(state);
    }

    @GetMapping("/active")
    public ResponseEntity<Set<String>> getActiveBots() {
        return ResponseEntity.ok(autoService.getActiveInstruments());
    }
}
