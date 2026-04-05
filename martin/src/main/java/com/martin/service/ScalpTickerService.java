package com.martin.service;

import com.martin.api.dto.ScalpTickData;
import com.martin.kraken.client.KrakenFuturesWsClient;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

@Service
@RequiredArgsConstructor
public class ScalpTickerService {

    private final KrakenFuturesWsClient krakenWsClient;

    /**
     * Returns a Flux of ScalpTickData for the given instrument.
     * Each tick contains the timestamp and last price from the Kraken WebSocket feed.
     */
    public Flux<ScalpTickData> streamTicks(String instrument, boolean demo) {
        return krakenWsClient.subscribeTicker(instrument, demo)
                .map(price -> new ScalpTickData(System.currentTimeMillis(), price));
    }
}
