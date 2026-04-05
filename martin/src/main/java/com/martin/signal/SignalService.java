package com.martin.signal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.ta4j.core.BarSeries;
import org.ta4j.core.BaseBarSeriesBuilder;
import org.ta4j.core.indicators.EMAIndicator;
import org.ta4j.core.indicators.RSIIndicator;
import org.ta4j.core.indicators.adx.ADXIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsMiddleIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsUpperIndicator;
import org.ta4j.core.indicators.bollinger.BollingerBandsLowerIndicator;
import org.ta4j.core.indicators.statistics.StandardDeviationIndicator;
import org.ta4j.core.indicators.SMAIndicator;
import org.ta4j.core.indicators.helpers.ClosePriceIndicator;
import org.ta4j.core.num.DecimalNum;

import java.time.Duration;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

@Service
public class SignalService {

    private static final Logger log = LoggerFactory.getLogger(SignalService.class);

    private static final Map<String, String> INSTRUMENT_MAP = Map.ofEntries(
            Map.entry("PF_XBTUSD", "XXBTZUSD"),
            Map.entry("PF_ETHUSD", "XETHZUSD"),
            Map.entry("PF_SOLUSD", "SOLUSD"),
            Map.entry("PF_DOTUSD", "DOTUSD"),
            Map.entry("PF_ADAUSD", "ADAUSD"),
            Map.entry("PF_XRPUSD", "XRPUSD"),
            Map.entry("PF_DOGEUSD", "XDGUSD"),
            Map.entry("PF_LINKUSD", "LINKUSD"),
            Map.entry("PF_AVAXUSD", "AVAXUSD"),
            Map.entry("PF_SUIUSD", "SUIUSD"),
            Map.entry("PF_NEARUSD", "NEARUSD"),
            Map.entry("PF_LTCUSD", "XLTCZUSD"),
            Map.entry("PF_XLMUSD", "XXLMZUSD"),
            Map.entry("PF_TAOUSD", "TAOUSD"),
            Map.entry("PF_ZECUSD", "ZECUSD"),
            Map.entry("PF_BNBUSD", "BNBUSD"),
            Map.entry("PF_TONUSD", "TONUSD"),
            Map.entry("PF_FILUSD", "FILUSD")
    );

    public static List<String> getSupportedInstruments() {
        return List.copyOf(INSTRUMENT_MAP.keySet());
    }

    private final WebClient krakenPublicClient;

    public SignalService() {
        this.krakenPublicClient = WebClient.create("https://api.kraken.com");
    }

    /**
     * Check EMA trend for a given futures instrument.
     * Fetches 250 1h candles from Kraken public OHLC API,
     * calculates EMA50, EMA200, RSI(14) and returns a signal.
     */
    public SignalResult checkEMATrend(String instrument) {
        String pair = INSTRUMENT_MAP.getOrDefault(instrument, "XXBTZUSD");
        log.info("Checking EMA trend for {} (pair={})", instrument, pair);

        try {
            // Fetch 1h candles from Kraken public API
            @SuppressWarnings("unchecked")
            Map<String, Object> response = krakenPublicClient.get()
                    .uri("/0/public/OHLC?pair={pair}&interval=60", pair)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (response == null || response.containsKey("error")) {
                List<?> errors = response != null ? (List<?>) response.get("error") : List.of("null response");
                if (errors != null && !errors.isEmpty()) {
                    String errorMsg = "Kraken API error: " + errors;
                    log.error(errorMsg);
                    return buildErrorResult(errorMsg);
                }
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> result = (Map<String, Object>) response.get("result");
            if (result == null) {
                return buildErrorResult("No result in Kraken response");
            }

            // The result key is the pair name (may differ from input)
            List<List<Object>> candles = null;
            for (Map.Entry<String, Object> entry : result.entrySet()) {
                if (!"last".equals(entry.getKey())) {
                    @SuppressWarnings("unchecked")
                    List<List<Object>> c = (List<List<Object>>) entry.getValue();
                    candles = c;
                    break;
                }
            }

            if (candles == null || candles.size() < 250) {
                log.warn("Only {} candles available for {}, need 250", candles != null ? candles.size() : 0, instrument);
                if (candles == null || candles.size() < 210) {
                    return buildErrorResult("Not enough candles: " + (candles != null ? candles.size() : 0));
                }
            }

            // Extract close prices (index 4 in OHLC array)
            // Take last 250 candles (or all if less)
            int start = Math.max(0, candles.size() - 250);
            List<List<Object>> subset = candles.subList(start, candles.size());

            BarSeries series = new BaseBarSeriesBuilder()
                    .withName("ema_trend_" + instrument)
                    .withNumTypeOf(DecimalNum.class)
                    .build();

            ZonedDateTime time = ZonedDateTime.now().minusHours(subset.size());
            for (List<Object> candle : subset) {
                time = time.plusHours(1);
                double open = parseDouble(candle.get(1));
                double high = parseDouble(candle.get(2));
                double low = parseDouble(candle.get(3));
                double close = parseDouble(candle.get(4));
                double volume = parseDouble(candle.get(6));

                series.addBar(Duration.ofHours(1), time,
                        DecimalNum.valueOf(open),
                        DecimalNum.valueOf(high),
                        DecimalNum.valueOf(low),
                        DecimalNum.valueOf(close),
                        DecimalNum.valueOf(volume));
            }

            int lastIndex = series.getEndIndex();
            ClosePriceIndicator closePrice = new ClosePriceIndicator(series);

            EMAIndicator ema50 = new EMAIndicator(closePrice, 50);
            EMAIndicator ema200 = new EMAIndicator(closePrice, 200);
            RSIIndicator rsi = new RSIIndicator(closePrice, 14);

            double ema50Value = ema50.getValue(lastIndex).doubleValue();
            double ema200Value = ema200.getValue(lastIndex).doubleValue();
            double rsiValue = rsi.getValue(lastIndex).doubleValue();

            // Determine signal
            SignalResult.EmaStatus emaStatus = ema50Value > ema200Value
                    ? SignalResult.EmaStatus.UPTREND
                    : SignalResult.EmaStatus.DOWNTREND;

            SignalResult.Signal signal;
            String reason;

            if (rsiValue < 25) {
                signal = SignalResult.Signal.DANGER;
                reason = String.format("CIRCUIT BREAKER: RSI=%.2f < 35, market in panic. Never open grid.", rsiValue);
            } else if (ema50Value > ema200Value && rsiValue > 50) {
                signal = SignalResult.Signal.OPEN;
                reason = String.format("EMA50=%.2f > EMA200=%.2f AND RSI=%.2f > 50. Uptrend confirmed.", ema50Value, ema200Value, rsiValue);
            } else {
                signal = SignalResult.Signal.WAIT;
                StringBuilder sb = new StringBuilder("Conditions not met: ");
                if (ema50Value <= ema200Value) {
                    sb.append(String.format("EMA50=%.2f <= EMA200=%.2f (downtrend). ", ema50Value, ema200Value));
                }
                if (rsiValue <= 50) {
                    sb.append(String.format("RSI=%.2f <= 50 (weak momentum). ", rsiValue));
                }
                reason = sb.toString();
            }

            // Calculate price and volatility (ATR-based)
            double lastPrice = closePrice.getValue(lastIndex).doubleValue();
            double volPct = 0;
            if (series.getBarCount() > 14) {
                double atrSum = 0;
                for (int i = lastIndex - 13; i <= lastIndex; i++) {
                    double h = series.getBar(i).getHighPrice().doubleValue();
                    double l = series.getBar(i).getLowPrice().doubleValue();
                    double pc = series.getBar(i - 1).getClosePrice().doubleValue();
                    atrSum += Math.max(h - l, Math.max(Math.abs(h - pc), Math.abs(l - pc)));
                }
                volPct = (atrSum / 14.0) / lastPrice * 100;
            }

            log.info("Signal for {}: {} — EMA50={}, EMA200={}, RSI={}, vol={}%", instrument, signal, ema50Value, ema200Value, rsiValue, String.format("%.2f", volPct));

            return SignalResult.builder()
                    .instrument(instrument)
                    .price(lastPrice)
                    .emaStatus(emaStatus)
                    .ema50(ema50Value)
                    .ema200(ema200Value)
                    .rsi(rsiValue)
                    .volatilityPct(volPct)
                    .signal(signal)
                    .reason(reason)
                    .timestamp(Instant.now())
                    .build();

        } catch (Exception e) {
            log.error("Failed to check EMA trend for {}: {}", instrument, e.getMessage(), e);
            return buildErrorResult("Exception: " + e.getMessage());
        }
    }

    /**
     * Check market regime for a given futures instrument using ADX and Bollinger Band Width.
     * Fetches 100 15-minute candles from Kraken public OHLC API.
     * ADX < 25 AND bbWidth < 4.0 → RANGING (tradeable for grid)
     * Otherwise → TRENDING (not tradeable for grid)
     */
    public RegimeResult checkRegime(String instrument) {
        String pair = INSTRUMENT_MAP.getOrDefault(instrument, "XXBTZUSD");
        log.info("Checking regime for {} (pair={})", instrument, pair);

        try {
            // Fetch 15m candles from Kraken public API
            @SuppressWarnings("unchecked")
            Map<String, Object> response = krakenPublicClient.get()
                    .uri("/0/public/OHLC?pair={pair}&interval=15", pair)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (response == null || response.containsKey("error")) {
                List<?> errors = response != null ? (List<?>) response.get("error") : List.of("null response");
                if (errors != null && !errors.isEmpty()) {
                    String errorMsg = "Kraken API error: " + errors;
                    log.error(errorMsg);
                    return buildRegimeError(instrument, errorMsg);
                }
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> result = (Map<String, Object>) response.get("result");
            if (result == null) {
                return buildRegimeError(instrument, "No result in Kraken response");
            }

            // The result key is the pair name (may differ from input)
            List<List<Object>> candles = null;
            for (Map.Entry<String, Object> entry : result.entrySet()) {
                if (!"last".equals(entry.getKey())) {
                    @SuppressWarnings("unchecked")
                    List<List<Object>> c = (List<List<Object>>) entry.getValue();
                    candles = c;
                    break;
                }
            }

            if (candles == null || candles.size() < 50) {
                return buildRegimeError(instrument, "Not enough candles: " + (candles != null ? candles.size() : 0));
            }

            // Take last 100 candles (or all if less)
            int start = Math.max(0, candles.size() - 100);
            List<List<Object>> subset = candles.subList(start, candles.size());

            BarSeries series = new BaseBarSeriesBuilder()
                    .withName("regime_" + instrument)
                    .withNumTypeOf(DecimalNum.class)
                    .build();

            ZonedDateTime time = ZonedDateTime.now().minusMinutes(subset.size() * 15L);
            for (List<Object> candle : subset) {
                time = time.plusMinutes(15);
                double open = parseDouble(candle.get(1));
                double high = parseDouble(candle.get(2));
                double low = parseDouble(candle.get(3));
                double close = parseDouble(candle.get(4));
                double volume = parseDouble(candle.get(6));

                series.addBar(Duration.ofMinutes(15), time,
                        DecimalNum.valueOf(open),
                        DecimalNum.valueOf(high),
                        DecimalNum.valueOf(low),
                        DecimalNum.valueOf(close),
                        DecimalNum.valueOf(volume));
            }

            int lastIndex = series.getEndIndex();
            ClosePriceIndicator closePrice = new ClosePriceIndicator(series);

            // ADX(14)
            ADXIndicator adx = new ADXIndicator(series, 14);
            double adxValue = adx.getValue(lastIndex).doubleValue();

            // Bollinger Band Width(20, 2)
            SMAIndicator sma20 = new SMAIndicator(closePrice, 20);
            StandardDeviationIndicator stdDev = new StandardDeviationIndicator(closePrice, 20);
            BollingerBandsMiddleIndicator bbMiddle = new BollingerBandsMiddleIndicator(sma20);
            BollingerBandsUpperIndicator bbUpper = new BollingerBandsUpperIndicator(bbMiddle, stdDev);
            BollingerBandsLowerIndicator bbLower = new BollingerBandsLowerIndicator(bbMiddle, stdDev);

            double upperVal = bbUpper.getValue(lastIndex).doubleValue();
            double lowerVal = bbLower.getValue(lastIndex).doubleValue();
            double middleVal = bbMiddle.getValue(lastIndex).doubleValue();
            double bbWidth = middleVal > 0 ? (upperVal - lowerVal) / middleVal * 100 : 0;

            boolean tradeable = adxValue < 40 && bbWidth < 4.0;
            RegimeResult.Regime regime = tradeable ? RegimeResult.Regime.RANGING : RegimeResult.Regime.TRENDING;

            log.info("Regime for {}: {} — ADX={}, BBWidth={}, tradeable={}",
                    instrument, regime,
                    String.format("%.2f", adxValue),
                    String.format("%.2f", bbWidth),
                    tradeable);

            return RegimeResult.builder()
                    .instrument(instrument)
                    .regime(regime)
                    .adx(adxValue)
                    .bbWidth(bbWidth)
                    .tradeable(tradeable)
                    .timestamp(Instant.now())
                    .build();

        } catch (Exception e) {
            log.error("Failed to check regime for {}: {}", instrument, e.getMessage(), e);
            return buildRegimeError(instrument, "Exception: " + e.getMessage());
        }
    }

    /**
     * Scan all supported instruments for regime status.
     * Returns list sorted by tradeable first, then by ADX ascending.
     */
    public List<RegimeResult> scanRegimes() {
        List<String> instruments = getSupportedInstruments();
        List<RegimeResult> results = new ArrayList<>();

        for (String inst : instruments) {
            try {
                results.add(checkRegime(inst));
                Thread.sleep(500); // rate limit
            } catch (Exception e) {
                log.warn("Regime scan failed for {}: {}", inst, e.getMessage());
            }
        }

        results.sort(Comparator
                .comparing((RegimeResult r) -> !r.isTradeable()) // tradeable first
                .thenComparingDouble(RegimeResult::getAdx));      // lowest ADX first

        return results;
    }

    private RegimeResult buildRegimeError(String instrument, String reason) {
        log.error("Regime check error for {}: {}", instrument, reason);
        return RegimeResult.builder()
                .instrument(instrument)
                .regime(RegimeResult.Regime.TRENDING) // default to non-tradeable on error
                .adx(100)
                .bbWidth(100)
                .tradeable(false)
                .timestamp(Instant.now())
                .build();
    }

    private SignalResult buildErrorResult(String reason) {
        return SignalResult.builder()
                .signal(SignalResult.Signal.WAIT)
                .reason(reason)
                .timestamp(Instant.now())
                .build();
    }

    private double parseDouble(Object value) {
        if (value == null) return 0.0;
        if (value instanceof Number) return ((Number) value).doubleValue();
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }
}
