package com.martin.strategy;

import com.martin.domain.enums.Direction;
import org.springframework.stereotype.Service;
import org.ta4j.core.BarSeries;
import org.ta4j.core.BaseBarSeriesBuilder;
import org.ta4j.core.num.DecimalNum;
import org.ta4j.core.indicators.RSIIndicator;
import org.ta4j.core.indicators.EMAIndicator;
import org.ta4j.core.indicators.MACDIndicator;
import org.ta4j.core.indicators.helpers.ClosePriceIndicator;

import java.time.Duration;
import java.time.ZonedDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class TechnicalAnalysisService {

    public SignalResult analyze(List<Double> closePrices) {
        BarSeries series = buildSeries(closePrices);

        int lastIndex = series.getEndIndex();
        ClosePriceIndicator closePrice = new ClosePriceIndicator(series);

        // RSI(14)
        RSIIndicator rsi = new RSIIndicator(closePrice, 14);
        double rsiValue = rsi.getValue(lastIndex).doubleValue();

        // EMA(9) and EMA(21)
        EMAIndicator ema9 = new EMAIndicator(closePrice, 9);
        EMAIndicator ema21 = new EMAIndicator(closePrice, 21);
        double ema9Value = ema9.getValue(lastIndex).doubleValue();
        double ema21Value = ema21.getValue(lastIndex).doubleValue();

        // MACD(12,26) with signal EMA(9)
        MACDIndicator macd = new MACDIndicator(closePrice, 12, 26);
        EMAIndicator macdSignal = new EMAIndicator(macd, 9);
        double macdValue = macd.getValue(lastIndex).doubleValue();
        double macdSignalValue = macdSignal.getValue(lastIndex).doubleValue();

        // Scoring
        int score = 0;
        StringBuilder reason = new StringBuilder();

        if (rsiValue < 30) {
            score += 2;
            reason.append(String.format("RSI=%.2f (oversold, +2); ", rsiValue));
        } else if (rsiValue < 45) {
            score += 1;
            reason.append(String.format("RSI=%.2f (low, +1); ", rsiValue));
        } else if (rsiValue > 70) {
            score -= 2;
            reason.append(String.format("RSI=%.2f (overbought, -2); ", rsiValue));
        } else if (rsiValue > 55) {
            score -= 1;
            reason.append(String.format("RSI=%.2f (high, -1); ", rsiValue));
        } else {
            reason.append(String.format("RSI=%.2f (neutral, 0); ", rsiValue));
        }

        if (ema9Value > ema21Value) {
            score += 1;
            reason.append(String.format("EMA9=%.2f > EMA21=%.2f (+1); ", ema9Value, ema21Value));
        } else {
            score -= 1;
            reason.append(String.format("EMA9=%.2f <= EMA21=%.2f (-1); ", ema9Value, ema21Value));
        }

        if (macdValue > macdSignalValue) {
            score += 1;
            reason.append(String.format("MACD=%.4f > Signal=%.4f (+1)", macdValue, macdSignalValue));
        } else {
            score -= 1;
            reason.append(String.format("MACD=%.4f <= Signal=%.4f (-1)", macdValue, macdSignalValue));
        }

        Direction direction = score >= 0 ? Direction.LONG : Direction.SHORT;
        double confidence = Math.min(1.0, Math.abs(score) / 4.0);

        return new SignalResult(direction, confidence, reason.toString());
    }

    /**
     * Detects a MACD crossover between the last two bars.
     * Bullish crossover (MACD crosses above Signal) → LONG
     * Bearish crossover (MACD crosses below Signal) → SHORT
     * No crossover → empty
     */
    public Optional<Direction> detectCrossover(List<Double> prices) {
        if (prices.size() < 30) return Optional.empty();

        BarSeries series = buildSeries(prices);
        int last = series.getEndIndex();
        if (last < 1) return Optional.empty();

        ClosePriceIndicator closePrice = new ClosePriceIndicator(series);
        MACDIndicator macd = new MACDIndicator(closePrice, 12, 26);
        EMAIndicator signal = new EMAIndicator(macd, 9);

        double prevMacd = macd.getValue(last - 1).doubleValue();
        double prevSignal = signal.getValue(last - 1).doubleValue();
        double currMacd = macd.getValue(last).doubleValue();
        double currSignal = signal.getValue(last).doubleValue();

        if (prevMacd <= prevSignal && currMacd > currSignal) {
            return Optional.of(Direction.LONG);
        }
        if (prevMacd >= prevSignal && currMacd < currSignal) {
            return Optional.of(Direction.SHORT);
        }
        return Optional.empty();
    }

    /**
     * Confirms a crossover direction with RSI: rejects LONG if overbought (>70),
     * rejects SHORT if oversold (<30).
     */
    public boolean confirmWithRsi(List<Double> prices, Direction direction) {
        if (prices.size() < 15) return true;

        BarSeries series = buildSeries(prices);
        ClosePriceIndicator closePrice = new ClosePriceIndicator(series);
        RSIIndicator rsi = new RSIIndicator(closePrice, 14);
        double rsiValue = rsi.getValue(series.getEndIndex()).doubleValue();

        if (direction == Direction.LONG && rsiValue > 70) {
            return false;
        }
        if (direction == Direction.SHORT && rsiValue < 30) {
            return false;
        }
        return true;
    }

    private BarSeries buildSeries(List<Double> prices) {
        BarSeries series = new BaseBarSeriesBuilder()
                .withName("analysis")
                .withNumTypeOf(DecimalNum.class)
                .build();

        ZonedDateTime time = ZonedDateTime.now().minusMinutes(prices.size());
        for (Double price : prices) {
            time = time.plusMinutes(1);
            series.addBar(Duration.ofMinutes(1), time,
                    DecimalNum.valueOf(price),
                    DecimalNum.valueOf(price),
                    DecimalNum.valueOf(price),
                    DecimalNum.valueOf(price),
                    DecimalNum.valueOf(0));
        }
        return series;
    }
}
