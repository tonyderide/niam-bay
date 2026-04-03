package com.martin.signal;

import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/signal")
@RequiredArgsConstructor
public class SignalController {

    private static final Logger log = LoggerFactory.getLogger(SignalController.class);

    private final SignalService signalService;
    private final AutoGridScheduler autoGridScheduler;

    // ── Signal endpoint ──

    @GetMapping("/ema_trend")
    public ResponseEntity<SignalResult> checkEmaTrend(
            @RequestParam(defaultValue = "PF_XBTUSD") String instrument) {
        log.info(">> GET /signal/ema_trend instrument={}", instrument);
        SignalResult result = signalService.checkEMATrend(instrument);
        return ResponseEntity.ok(result);
    }

    // ── Scan all supported pairs ──

    @GetMapping("/scan")
    public ResponseEntity<List<SignalResult>> scanAll() {
        log.info(">> GET /signal/scan — scanning all supported instruments");
        List<String> instruments = SignalService.getSupportedInstruments();
        List<SignalResult> results = new ArrayList<>();
        for (String inst : instruments) {
            try {
                results.add(signalService.checkEMATrend(inst));
                Thread.sleep(500); // rate limit
            } catch (Exception e) {
                log.warn("Scan failed for {}: {}", inst, e.getMessage());
            }
        }
        // Sort: OPEN first, then WAIT, then DANGER. Within same signal, sort by RSI desc
        results.sort(Comparator
                .comparingInt((SignalResult r) -> r.getSignal() == SignalResult.Signal.OPEN ? 0 : r.getSignal() == SignalResult.Signal.WAIT ? 1 : 2)
                .thenComparingDouble(r -> -r.getRsi()));
        return ResponseEntity.ok(results);
    }

    // ── Regime endpoints ──

    @GetMapping("/regime")
    public ResponseEntity<RegimeResult> checkRegime(
            @RequestParam(defaultValue = "PF_SOLUSD") String instrument) {
        log.info(">> GET /signal/regime instrument={}", instrument);
        RegimeResult result = signalService.checkRegime(instrument);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/regime/scan")
    public ResponseEntity<List<RegimeResult>> scanRegimes() {
        log.info(">> GET /signal/regime/scan — scanning all supported instruments");
        List<RegimeResult> results = signalService.scanRegimes();
        return ResponseEntity.ok(results);
    }

    // ── Auto-grid endpoints ──

    @PostMapping("/auto/enable")
    public ResponseEntity<Map<String, Object>> enableAutoGrid() {
        log.info(">> POST /signal/auto/enable");
        autoGridScheduler.enable();
        return ResponseEntity.ok(Map.of("enabled", true, "message", "Auto-grid scheduler enabled"));
    }

    @PostMapping("/auto/disable")
    public ResponseEntity<Map<String, Object>> disableAutoGrid() {
        log.info(">> POST /signal/auto/disable");
        autoGridScheduler.disable();
        return ResponseEntity.ok(Map.of("enabled", false, "message", "Auto-grid scheduler disabled"));
    }

    @PostMapping("/auto/config")
    public ResponseEntity<Map<String, Object>> setAutoGridConfig(
            @RequestParam String instrument,
            @RequestParam(defaultValue = "28.59") double capital,
            @RequestParam(defaultValue = "3") int leverage,
            @RequestParam(defaultValue = "false") boolean demo,
            @RequestParam(defaultValue = "0.7") double gridSpacingPct,
            @RequestParam(defaultValue = "6") int totalLevels,
            @RequestParam(defaultValue = "50") double maxLossPercent,
            @RequestParam(defaultValue = "NEUTRAL") String gridMode) {
        log.info(">> POST /signal/auto/config instrument={} capital={} leverage={}", instrument, capital, leverage);

        AutoGridConfig config = AutoGridConfig.builder()
                .instrument(instrument)
                .capital(capital)
                .leverage(leverage)
                .demo(demo)
                .gridSpacingPct(gridSpacingPct)
                .totalLevels(totalLevels)
                .maxLossPercent(maxLossPercent)
                .gridMode(gridMode.toUpperCase())
                .build();

        autoGridScheduler.setConfig(config);
        return ResponseEntity.ok(Map.of("message", "Config set for " + instrument, "config", config));
    }

    @DeleteMapping("/auto/config")
    public ResponseEntity<Map<String, Object>> removeAutoGridConfig(@RequestParam String instrument) {
        log.info(">> DELETE /signal/auto/config instrument={}", instrument);
        autoGridScheduler.removeConfig(instrument);
        return ResponseEntity.ok(Map.of("message", "Config removed for " + instrument));
    }

    @GetMapping("/auto/status")
    public ResponseEntity<Map<String, Object>> getAutoGridStatus() {
        DrawdownManager dd = autoGridScheduler.getDrawdownManager();
        return ResponseEntity.ok(Map.ofEntries(
                Map.entry("enabled", autoGridScheduler.isEnabled()),
                Map.entry("configs", autoGridScheduler.getConfigs()),
                Map.entry("lastSignals", autoGridScheduler.getLastSignals()),
                Map.entry("lastRegimes", autoGridScheduler.getLastRegimes()),
                Map.entry("drawdown", Map.of(
                        "peakEquity", dd.getPeakEquity(),
                        "killed", dd.isKilled(),
                        "pauseUntil", dd.getPauseUntil() != null ? dd.getPauseUntil().toString() : "none"
                )),
                Map.entry("lastCheckTime", autoGridScheduler.getLastCheckTime() != null
                        ? autoGridScheduler.getLastCheckTime().toString() : "never")
        ));
    }
}
