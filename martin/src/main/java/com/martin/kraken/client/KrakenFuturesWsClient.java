package com.martin.kraken.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.martin.kraken.config.KrakenProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import io.netty.resolver.DefaultAddressResolverGroup;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.socket.client.ReactorNettyWebSocketClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;
import reactor.netty.http.client.HttpClient;

import java.net.URI;
import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class KrakenFuturesWsClient {

    private static final Logger log = LoggerFactory.getLogger(KrakenFuturesWsClient.class);

    private final KrakenProperties properties;
    private final ReactorNettyWebSocketClient wsClient;
    private final ObjectMapper objectMapper;
    private final ConcurrentHashMap<String, Sinks.Many<Double>> priceFeeds = new ConcurrentHashMap<>();

    public KrakenFuturesWsClient(KrakenProperties properties) {
        this.properties = properties;
        HttpClient httpClient = HttpClient.create()
                .resolver(DefaultAddressResolverGroup.INSTANCE);
        this.wsClient = new ReactorNettyWebSocketClient(httpClient);
        this.objectMapper = new ObjectMapper();
    }

    /**
     * Subscribes to ticker feed for a given instrument and returns a Flux of last prices.
     * Uses demo or live WebSocket URL based on the demo flag.
     */
    public Flux<Double> subscribeTicker(String instrument, boolean demo) {
        String key = instrument + (demo ? ":demo" : ":live");
        Sinks.Many<Double> sink = priceFeeds.computeIfAbsent(key, k -> {
            Sinks.Many<Double> newSink = Sinks.many().multicast().onBackpressureBuffer();
            connectTicker(k, instrument, demo, newSink);
            return newSink;
        });
        return sink.asFlux();
    }

    private void connectTicker(String key, String instrument, boolean demo, Sinks.Many<Double> sink) {
        String url = demo ? properties.getDemoWsUrl() : properties.getWsUrl();
        String subscribeMsg = String.format(
                "{\"event\":\"subscribe\",\"feed\":\"ticker\",\"product_ids\":[\"%s\"]}",
                instrument
        );

        wsClient.execute(URI.create(url), session -> {
            // Send subscription message
            var sendSub = session.send(Flux.just(session.textMessage(subscribeMsg)));

            // Send ping every 30 seconds
            var sendPing = session.send(
                    Flux.interval(Duration.ofSeconds(30))
                            .map(i -> session.textMessage("{\"event\":\"ping\"}"))
            );

            // Receive messages and extract last price
            var receive = session.receive()
                    .map(msg -> msg.getPayloadAsText())
                    .doOnNext(text -> {
                        try {
                            JsonNode node = objectMapper.readTree(text);
                            if (node.has("last")) {
                                double lastPrice = node.get("last").asDouble();
                                sink.tryEmitNext(lastPrice);
                            }
                        } catch (Exception e) {
                            log.warn("Failed to parse WebSocket message: {}", text, e);
                        }
                    })
                    .then();

            return Flux.merge(sendSub, sendPing, receive).then();
        }).subscribe(
                null,
                error -> {
                    log.error("WebSocket error for {}: {}", instrument, error.getMessage());
                    priceFeeds.remove(key);
                    sink.tryEmitComplete();
                },
                () -> {
                    log.info("WebSocket closed for {}", instrument);
                    priceFeeds.remove(key);
                    sink.tryEmitComplete();
                }
        );
    }
}
