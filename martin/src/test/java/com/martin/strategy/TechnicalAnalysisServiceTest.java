package com.martin.strategy;

import com.martin.domain.enums.Direction;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

class TechnicalAnalysisServiceTest {

    private TechnicalAnalysisService service;

    @BeforeEach
    void setUp() {
        service = new TechnicalAnalysisService();
    }

    @Test
    void analyze_withTrendingUpAfterDip_returnsValidSignal() {
        // 30 prices: dip then trending up
        List<Double> prices = new ArrayList<>();
        // Initial prices around 100, dip to ~90, then recover and trend up
        double[] raw = {
            100, 99, 98, 96, 94, 92, 91, 90, 90, 91,
            92, 93, 94, 95, 96, 97, 98, 99, 100, 101,
            102, 103, 104, 105, 106, 107, 108, 109, 110, 111
        };
        for (double p : raw) {
            prices.add(p);
        }

        SignalResult result = service.analyze(prices);

        assertThat(result).isNotNull();
        assertThat(result.getDirection()).isIn(Direction.LONG, Direction.SHORT);
        assertThat(result.getConfidence()).isBetween(0.0, 1.0);
        assertThat(result.getReason()).isNotBlank();
    }

    @Test
    void detectCrossover_bullishCrossover_returnsLong() {
        // Accelerating downtrend keeps MACD < signal until the very last bar.
        // A large final up bar forces MACD above signal → bullish crossover.
        List<Double> prices = new ArrayList<>();
        double price = 2000.0;
        double drop = 1.0;
        for (int i = 0; i < 34; i++) {
            prices.add(price);
            price -= drop;
            drop += 0.5; // accelerate decline so MACD stays < signal
        }
        prices.add(price + 500); // huge reversal at last bar

        Optional<Direction> result = service.detectCrossover(prices);

        assertThat(result).isPresent();
        assertThat(result.get()).isEqualTo(Direction.LONG);
    }

    @Test
    void detectCrossover_bearishCrossover_returnsShort() {
        // Accelerating uptrend keeps MACD > signal until the very last bar.
        // A large final down bar forces MACD below signal → bearish crossover.
        List<Double> prices = new ArrayList<>();
        double price = 1000.0;
        double rise = 1.0;
        for (int i = 0; i < 34; i++) {
            prices.add(price);
            price += rise;
            rise += 0.5; // accelerate rise so MACD stays > signal
        }
        prices.add(price - 500); // huge drop at last bar

        Optional<Direction> result = service.detectCrossover(prices);

        assertThat(result).isPresent();
        assertThat(result.get()).isEqualTo(Direction.SHORT);
    }

    @Test
    void detectCrossover_noCrossover_returnsEmpty() {
        // Steady uptrend: MACD stabilises above signal, no crossover at last bar
        List<Double> prices = new ArrayList<>();
        for (int i = 0; i < 35; i++) prices.add(80.0 + i * 0.5);

        Optional<Direction> result = service.detectCrossover(prices);

        assertThat(result).isEmpty();
    }

    @Test
    void detectCrossover_tooFewPrices_returnsEmpty() {
        List<Double> prices = List.of(100.0, 101.0, 102.0);
        assertThat(service.detectCrossover(prices)).isEmpty();
    }

    @Test
    void analyze_withMinimumCandles_returnsValidSignal() {
        // 15 prices
        List<Double> prices = new ArrayList<>();
        for (int i = 0; i < 15; i++) {
            prices.add(100.0 + i);
        }

        SignalResult result = service.analyze(prices);

        assertThat(result).isNotNull();
        assertThat(result.getDirection()).isIn(Direction.LONG, Direction.SHORT);
        assertThat(result.getConfidence()).isBetween(0.0, 1.0);
        assertThat(result.getReason()).isNotBlank();
    }
}
