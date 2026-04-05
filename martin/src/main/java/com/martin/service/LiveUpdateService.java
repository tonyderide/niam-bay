package com.martin.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

import java.util.concurrent.ConcurrentHashMap;

@Service
public class LiveUpdateService {

    private static final Logger log = LoggerFactory.getLogger(LiveUpdateService.class);

    private final ConcurrentHashMap<String, Sinks.Many<String>> sinks = new ConcurrentHashMap<>();

    /**
     * Get or create a Sink for the given instrument.
     */
    private Sinks.Many<String> getSink(String instrument) {
        return sinks.computeIfAbsent(instrument, key -> {
            log.info("Creating SSE sink for instrument: {}", key);
            return Sinks.many().multicast().onBackpressureBuffer(256, false);
        });
    }

    /**
     * Returns a Flux of JSON strings representing dashboard state changes for an instrument.
     */
    public Flux<String> getDashboardStream(String instrument) {
        return getSink(instrument).asFlux();
    }

    /**
     * Publish a dashboard state update for an instrument.
     */
    public void publishUpdate(String instrument, String jsonData) {
        Sinks.Many<String> sink = getSink(instrument);
        Sinks.EmitResult result = sink.tryEmitNext(jsonData);
        if (result.isFailure()) {
            log.warn("Failed to emit SSE update for {}: {}", instrument, result);
        }
    }
}
