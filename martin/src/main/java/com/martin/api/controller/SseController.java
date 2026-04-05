package com.martin.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.martin.config.LogStreamAppender;
import com.martin.service.LiveUpdateService;
import com.martin.service.ScalpTickerService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/api/sse")
@RequiredArgsConstructor
public class SseController {

    private final LiveUpdateService liveUpdateService;
    private final ScalpTickerService scalpTickerService;
    private final ObjectMapper objectMapper;

    @GetMapping(value = "/dashboard/{instrument}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamDashboard(@PathVariable String instrument) {
        return liveUpdateService.getDashboardStream(instrument);
    }

    @GetMapping(value = "/logs", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamLogs() {
        return LogStreamAppender.getLogStream();
    }

    @GetMapping(value = "/scalp-ticker/{instrument}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamScalpTicker(@PathVariable String instrument,
                                          @RequestParam(defaultValue = "false") boolean demo) {
        return scalpTickerService.streamTicks(instrument, demo)
                .map(tick -> {
                    try {
                        return objectMapper.writeValueAsString(tick);
                    } catch (Exception e) {
                        return "{}";
                    }
                });
    }
}
