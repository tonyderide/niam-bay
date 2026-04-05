package com.martin.api.controller;

import com.martin.grid.GridState;
import com.martin.grid.GridTradingService;
import com.martin.grid.GridMode;
import com.martin.grid.TrailingStopService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/grid")
@RequiredArgsConstructor
public class GridController {

    private static final Logger log = LoggerFactory.getLogger(GridController.class);
    private final GridTradingService gridService;
    private final TrailingStopService trailingStopService;

    @PostMapping("/start")
    public ResponseEntity<?> startGrid(
            @RequestParam(defaultValue = "PF_ETHUSD") String instrument,
            @RequestParam(defaultValue = "28.59") double capital,
            @RequestParam(defaultValue = "3") int leverage,
            @RequestParam(defaultValue = "false") boolean demo,
            @RequestParam(defaultValue = "0.7") double gridSpacingPct,
            @RequestParam(defaultValue = "6") int totalLevels,
            @RequestParam(defaultValue = "50") double maxLossPercent,
            @RequestParam(defaultValue = "NEUTRAL") String gridMode) {
        log.info(">> POST /grid/start instrument={}, capital={}, leverage={}, demo={}, spacing={}%, levels={}, maxLoss={}%, mode={}",
                instrument, capital, leverage, demo, gridSpacingPct, totalLevels, maxLossPercent, gridMode);
        try {
            GridState state = gridService.startGrid(instrument, capital, leverage, demo,
                    gridSpacingPct / 100.0, totalLevels, maxLossPercent, GridMode.valueOf(gridMode != null ? gridMode.toUpperCase() : "NEUTRAL"));
            return ResponseEntity.ok(state);
        } catch (Exception e) {
            log.error("Failed to start grid: {}", e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @PostMapping("/sync")
    public ResponseEntity<?> syncGrid(
            @RequestParam(defaultValue = "PF_ETHUSD") String instrument,
            @RequestParam(defaultValue = "14.69") double capital,
            @RequestParam(defaultValue = "10") int leverage,
            @RequestParam(defaultValue = "false") boolean demo,
            @RequestParam(defaultValue = "0.7") double gridSpacingPct,
            @RequestParam(defaultValue = "6") int totalLevels,
            @RequestParam(defaultValue = "50") double maxLossPercent,
            @RequestParam(defaultValue = "NEUTRAL") String gridMode) {
        log.info(">> POST /grid/sync instrument={}, capital={}, leverage={}, demo={}, mode={}", instrument, capital, leverage, demo, gridMode);
        try {
            GridState state = gridService.syncFromKraken(instrument, capital, leverage, demo,
                    gridSpacingPct / 100.0, totalLevels, maxLossPercent, GridMode.valueOf(gridMode != null ? gridMode.toUpperCase() : "NEUTRAL"));
            return ResponseEntity.ok(state);
        } catch (Exception e) {
            log.error("Failed to sync grid: {}", e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/analyze/{instrument}")
    public ResponseEntity<?> analyzeMarket(
            @PathVariable String instrument,
            @RequestParam(defaultValue = "false") boolean demo) {
        log.info(">> GET /grid/analyze/{}", instrument);
        return ResponseEntity.ok(gridService.analyzeMarket(instrument, demo));
    }

    @PostMapping("/stop/{instrument}")
    public ResponseEntity<String> stopGrid(@PathVariable String instrument) {
        log.info(">> POST /grid/stop/{}", instrument);
        gridService.stopGrid(instrument);
        return ResponseEntity.ok("Grid stopped for " + instrument);
    }

    @GetMapping("/status/{instrument}")
    public ResponseEntity<?> getStatus(@PathVariable String instrument) {
        GridState state = gridService.getState(instrument);
        if (state == null) {
            return ResponseEntity.ok(Map.of("active", false, "instrument", instrument));
        }
        return ResponseEntity.ok(state);
    }

    @GetMapping("/active")
    public ResponseEntity<Set<String>> getActiveGrids() {
        return ResponseEntity.ok(gridService.getActiveInstruments());
    }

    // ── Trailing Stop endpoints ──

    @PostMapping("/trailing/enable")
    public ResponseEntity<Map<String, Object>> enableTrailingStop(
            @RequestParam String instrument,
            @RequestParam(defaultValue = "0.30") double trail,
            @RequestParam(defaultValue = "0.20") double minProfit) {
        log.info(">> POST /grid/trailing/enable instrument={} trail={} minProfit={}", instrument, trail, minProfit);
        trailingStopService.enable(instrument, trail, minProfit);
        return ResponseEntity.ok(Map.of(
                "message", "Trailing stop enabled for " + instrument,
                "trail", trail,
                "minProfit", minProfit
        ));
    }

    @PostMapping("/trailing/disable")
    public ResponseEntity<Map<String, Object>> disableTrailingStop(@RequestParam String instrument) {
        log.info(">> POST /grid/trailing/disable instrument={}", instrument);
        trailingStopService.disable(instrument);
        return ResponseEntity.ok(Map.of("message", "Trailing stop disabled for " + instrument));
    }

    @GetMapping("/trailing/status")
    public ResponseEntity<Map<String, TrailingStopService.TrailingState>> getTrailingStatus() {
        return ResponseEntity.ok(trailingStopService.getAll());
    }

    @GetMapping("/trailing/status/{instrument}")
    public ResponseEntity<?> getTrailingStatusForInstrument(@PathVariable String instrument) {
        TrailingStopService.TrailingState state = trailingStopService.getState(instrument);
        if (state == null) {
            return ResponseEntity.ok(Map.of("active", false, "instrument", instrument));
        }
        return ResponseEntity.ok(state);
    }
}
