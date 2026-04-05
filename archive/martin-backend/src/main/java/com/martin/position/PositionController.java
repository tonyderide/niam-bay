package com.martin.position;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/position")
public class PositionController {

    private static final Logger log = LoggerFactory.getLogger(PositionController.class);

    @Autowired
    private PositionService positionService;

    @PostMapping("/short")
    public PositionState openShort(
            @RequestParam String instrument,
            @RequestParam(defaultValue = "23") double capital,
            @RequestParam(defaultValue = "10") int leverage,
            @RequestParam(defaultValue = "2.0") double slPct,
            @RequestParam(defaultValue = "3.0") double tpPct,
            @RequestParam(defaultValue = "false") boolean demo) {
        log.info(">> POST /position/short instrument={} capital={} lev={} sl={}% tp={}%",
                instrument, capital, leverage, slPct, tpPct);
        return positionService.openShort(instrument, capital, leverage, slPct, tpPct, demo);
    }

    @PostMapping("/long")
    public PositionState openLong(
            @RequestParam String instrument,
            @RequestParam(defaultValue = "23") double capital,
            @RequestParam(defaultValue = "10") int leverage,
            @RequestParam(defaultValue = "2.0") double slPct,
            @RequestParam(defaultValue = "3.0") double tpPct,
            @RequestParam(defaultValue = "false") boolean demo) {
        log.info(">> POST /position/long instrument={} capital={} lev={} sl={}% tp={}%",
                instrument, capital, leverage, slPct, tpPct);
        return positionService.openLong(instrument, capital, leverage, slPct, tpPct, demo);
    }

    @PostMapping("/close")
    public PositionState closePosition(@RequestParam String instrument) {
        log.info(">> POST /position/close instrument={}", instrument);
        return positionService.closePosition(instrument);
    }

    @GetMapping("/status")
    public PositionState getStatus(@RequestParam String instrument) {
        PositionState state = positionService.getStatus(instrument);
        if (state == null) throw new IllegalStateException("No position for " + instrument);
        return state;
    }

    @GetMapping("/all")
    public Map<String, PositionState> getAllPositions() {
        return positionService.getAllPositions();
    }
}
