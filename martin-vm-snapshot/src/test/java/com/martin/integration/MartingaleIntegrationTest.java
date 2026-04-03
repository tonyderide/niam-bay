package com.martin.integration;

import com.martin.domain.entity.BotConfig;
import com.martin.domain.entity.Trade;
import com.martin.domain.entity.TradeSeries;
import com.martin.domain.enums.Direction;
import com.martin.domain.enums.SeriesStatus;
import com.martin.domain.enums.TradeStatus;
import com.martin.domain.repository.BotConfigRepository;
import com.martin.domain.repository.TradeRepository;
import com.martin.domain.repository.TradeSeriesRepository;
import com.martin.engine.MartingaleEngine;
import com.martin.engine.MartingaleState;
import com.martin.engine.PnlCalculator;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.kraken.client.KrakenFuturesWsClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
class MartingaleIntegrationTest {

    @Autowired
    private MartingaleEngine martingaleEngine;

    @Autowired
    private PnlCalculator pnlCalculator;

    @Autowired
    private BotConfigRepository botConfigRepository;

    @Autowired
    private TradeRepository tradeRepository;

    @Autowired
    private TradeSeriesRepository seriesRepository;

    @MockitoBean
    private KrakenFuturesRestClient krakenRestClient;

    @MockitoBean
    private KrakenFuturesWsClient krakenWsClient;

    private BotConfig config;

    @BeforeEach
    void setUp() {
        tradeRepository.deleteAll();
        seriesRepository.deleteAll();
        botConfigRepository.deleteAll();

        config = BotConfig.builder()
                .instrument("PF_XBTUSD")
                .initialStake(new BigDecimal("100"))
                .maxDoublings(3)
                .takeProfitPct(new BigDecimal("1.5"))
                .stopLossPct(new BigDecimal("1.0"))
                .leverage(5)
                .signalStrategy("MANUAL")
                .active(true)
                .build();
        config = botConfigRepository.save(config);
    }

    @Test
    void shouldPersistBotConfigToDatabase() {
        BotConfig found = botConfigRepository.findById(config.getId()).orElseThrow();

        assertThat(found.getInstrument()).isEqualTo("PF_XBTUSD");
        assertThat(found.getInitialStake()).isEqualByComparingTo("100");
        assertThat(found.getMaxDoublings()).isEqualTo(3);
        assertThat(found.getLeverage()).isEqualTo(5);
        assertThat(found.isActive()).isTrue();
    }

    @Test
    void shouldInitSeriesWithCorrectState() {
        MartingaleState state = martingaleEngine.initSeries(config, Direction.LONG);

        assertThat(state.getInstrument()).isEqualTo("PF_XBTUSD");
        assertThat(state.getCurrentDirection()).isEqualTo(Direction.LONG);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("100");
        assertThat(state.getCurrentDoubling()).isEqualTo(0);
        assertThat(state.isActive()).isTrue();
    }

    @Test
    void shouldPersistTradeSeriesAndTrades() {
        TradeSeries series = TradeSeries.builder()
                .instrument("PF_XBTUSD")
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        Trade trade = Trade.builder()
                .series(series)
                .instrument("PF_XBTUSD")
                .krakenOrderId("test-order-1")
                .direction(Direction.LONG)
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("100"))
                .leverage(5)
                .entryPrice(new BigDecimal("50000"))
                .doublingStep(0)
                .openedAt(Instant.now())
                .build();
        trade = tradeRepository.save(trade);

        assertThat(series.getId()).isNotNull();
        assertThat(trade.getId()).isNotNull();
        assertThat(trade.getSeries().getId()).isEqualTo(series.getId());

        List<Trade> foundTrades = tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD");
        assertThat(foundTrades).hasSize(1);
        assertThat(foundTrades.get(0).getKrakenOrderId()).isEqualTo("test-order-1");
    }

    @Test
    void shouldResetOnWin() {
        // 1. Init series LONG
        MartingaleState state = martingaleEngine.initSeries(config, Direction.LONG);

        // 2. Create series and trade in DB
        TradeSeries series = TradeSeries.builder()
                .instrument("PF_XBTUSD")
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        BigDecimal entryPrice = new BigDecimal("50000");
        BigDecimal exitPrice = new BigDecimal("50750"); // +1.5% = TP hit

        Trade trade = Trade.builder()
                .series(series)
                .instrument("PF_XBTUSD")
                .krakenOrderId("win-order")
                .direction(Direction.LONG)
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("100"))
                .leverage(5)
                .entryPrice(entryPrice)
                .doublingStep(0)
                .openedAt(Instant.now())
                .build();
        trade = tradeRepository.save(trade);

        // 3. Calculate P&L using PnlCalculator
        BigDecimal feePercent = new BigDecimal("0.05");
        BigDecimal grossPnl = pnlCalculator.calculatePnl(Direction.LONG, trade.getStake(),
                config.getLeverage(), entryPrice, exitPrice);
        BigDecimal fees = pnlCalculator.calculateFees(trade.getStake(), config.getLeverage(), feePercent);
        BigDecimal netPnl = pnlCalculator.calculateNetPnl(Direction.LONG, trade.getStake(),
                config.getLeverage(), entryPrice, exitPrice, feePercent);

        // Verify P&L is positive for a winning LONG trade
        assertThat(grossPnl).isGreaterThan(BigDecimal.ZERO);
        assertThat(netPnl).isEqualByComparingTo(grossPnl.subtract(fees));

        // 4. Close trade as WON
        trade.setExitPrice(exitPrice);
        trade.setPnl(netPnl);
        trade.setFees(fees);
        trade.setStatus(TradeStatus.WON);
        trade.setClosedAt(Instant.now());
        tradeRepository.save(trade);

        // 5. Apply onWin to state - should reset
        MartingaleState resetState = martingaleEngine.onWin(state, config, Direction.LONG);

        assertThat(resetState.getCurrentStake()).isEqualByComparingTo(config.getInitialStake());
        assertThat(resetState.getCurrentDoubling()).isEqualTo(0);
        assertThat(resetState.isActive()).isTrue();

        // 6. Update series as COMPLETED
        series.setTotalPnl(netPnl);
        series.setTotalFees(fees);
        series.setStatus(SeriesStatus.COMPLETED);
        series.setEndedAt(Instant.now());
        seriesRepository.save(series);

        // 7. Verify DB state
        Trade savedTrade = tradeRepository.findById(trade.getId()).orElseThrow();
        assertThat(savedTrade.getStatus()).isEqualTo(TradeStatus.WON);
        assertThat(savedTrade.getPnl()).isGreaterThan(BigDecimal.ZERO);

        TradeSeries savedSeries = seriesRepository.findById(series.getId()).orElseThrow();
        assertThat(savedSeries.getStatus()).isEqualTo(SeriesStatus.COMPLETED);
        assertThat(savedSeries.getTotalPnl()).isGreaterThan(BigDecimal.ZERO);
    }

    @Test
    void shouldDoubleStakeAndInvertOnLoss() {
        // 1. Init series LONG
        MartingaleState state = martingaleEngine.initSeries(config, Direction.LONG);

        // 2. Create series and losing trade
        TradeSeries series = TradeSeries.builder()
                .instrument("PF_XBTUSD")
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        BigDecimal entryPrice = new BigDecimal("50000");
        BigDecimal exitPrice = new BigDecimal("49500"); // -1.0% = SL hit

        Trade trade = Trade.builder()
                .series(series)
                .instrument("PF_XBTUSD")
                .krakenOrderId("loss-order")
                .direction(Direction.LONG)
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("100"))
                .leverage(5)
                .entryPrice(entryPrice)
                .doublingStep(0)
                .openedAt(Instant.now())
                .build();
        trade = tradeRepository.save(trade);

        // 3. Calculate P&L - should be negative for a LONG losing trade
        BigDecimal feePercent = new BigDecimal("0.05");
        BigDecimal netPnl = pnlCalculator.calculateNetPnl(Direction.LONG, trade.getStake(),
                config.getLeverage(), entryPrice, exitPrice, feePercent);
        BigDecimal fees = pnlCalculator.calculateFees(trade.getStake(), config.getLeverage(), feePercent);

        assertThat(netPnl).isLessThan(BigDecimal.ZERO);

        // 4. Close trade as LOST
        trade.setExitPrice(exitPrice);
        trade.setPnl(netPnl);
        trade.setFees(fees);
        trade.setStatus(TradeStatus.LOST);
        trade.setClosedAt(Instant.now());
        tradeRepository.save(trade);

        // 5. Apply onLoss - should double stake and invert direction
        MartingaleState updatedState = martingaleEngine.onLoss(state, config);

        assertThat(updatedState.getCurrentStake()).isEqualByComparingTo("200"); // 100 x 2
        assertThat(updatedState.getCurrentDirection()).isEqualTo(Direction.SHORT); // inverted
        assertThat(updatedState.getCurrentDoubling()).isEqualTo(1);
        assertThat(updatedState.isActive()).isTrue();

        // 6. Update series doubling
        series.setCurrentDoubling(updatedState.getCurrentDoubling());
        series.setTotalPnl(netPnl);
        series.setTotalFees(fees);
        seriesRepository.save(series);

        // 7. Verify DB state
        Trade savedTrade = tradeRepository.findById(trade.getId()).orElseThrow();
        assertThat(savedTrade.getStatus()).isEqualTo(TradeStatus.LOST);
        assertThat(savedTrade.getPnl()).isLessThan(BigDecimal.ZERO);

        TradeSeries savedSeries = seriesRepository.findById(series.getId()).orElseThrow();
        assertThat(savedSeries.getStatus()).isEqualTo(SeriesStatus.ACTIVE);
        assertThat(savedSeries.getCurrentDoubling()).isEqualTo(1);
    }

    @Test
    void shouldStopAfterMaxDoublings() {
        // Config: maxDoublings = 3
        MartingaleState state = martingaleEngine.initSeries(config, Direction.LONG);

        TradeSeries series = TradeSeries.builder()
                .instrument("PF_XBTUSD")
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        BigDecimal feePercent = new BigDecimal("0.05");
        BigDecimal entryPrice = new BigDecimal("50000");

        // Simulate losses until max doublings
        Direction[] expectedDirections = {Direction.LONG, Direction.SHORT, Direction.LONG, Direction.SHORT};
        BigDecimal[] expectedStakes = {
                new BigDecimal("100"),
                new BigDecimal("200"),
                new BigDecimal("400"),
                new BigDecimal("800")
        };

        for (int i = 0; i <= config.getMaxDoublings(); i++) {
            // Verify current state before each trade
            assertThat(state.getCurrentDirection()).isEqualTo(expectedDirections[i]);
            assertThat(state.getCurrentStake()).isEqualByComparingTo(expectedStakes[i]);

            // Calculate exit price for a loss based on direction
            BigDecimal exitPrice;
            if (state.getCurrentDirection() == Direction.LONG) {
                exitPrice = entryPrice.subtract(
                        entryPrice.multiply(config.getStopLossPct())
                                .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP));
            } else {
                exitPrice = entryPrice.add(
                        entryPrice.multiply(config.getStopLossPct())
                                .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP));
            }

            BigDecimal netPnl = pnlCalculator.calculateNetPnl(state.getCurrentDirection(),
                    state.getCurrentStake(), config.getLeverage(), entryPrice, exitPrice, feePercent);
            BigDecimal fees = pnlCalculator.calculateFees(state.getCurrentStake(), config.getLeverage(), feePercent);

            Trade trade = Trade.builder()
                    .series(series)
                    .instrument("PF_XBTUSD")
                    .krakenOrderId("loss-order-" + i)
                    .direction(state.getCurrentDirection())
                    .status(TradeStatus.LOST)
                    .stake(state.getCurrentStake())
                    .leverage(config.getLeverage())
                    .entryPrice(entryPrice)
                    .exitPrice(exitPrice)
                    .pnl(netPnl)
                    .fees(fees)
                    .doublingStep(state.getCurrentDoubling())
                    .openedAt(Instant.now())
                    .closedAt(Instant.now())
                    .build();
            tradeRepository.save(trade);

            series.setTotalPnl(series.getTotalPnl().add(netPnl));
            series.setTotalFees(series.getTotalFees().add(fees));

            // Apply loss
            state = martingaleEngine.onLoss(state, config);
            series.setCurrentDoubling(state.getCurrentDoubling());
        }

        // After maxDoublings (3) losses, the engine should deactivate
        assertThat(state.isActive()).isFalse();

        // Mark series as STOPPED
        series.setStatus(SeriesStatus.STOPPED);
        series.setEndedAt(Instant.now());
        seriesRepository.save(series);

        // Verify all trades are persisted
        List<Trade> allTrades = tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD");
        assertThat(allTrades).hasSize(config.getMaxDoublings() + 1); // 4 trades (0, 1, 2, 3)

        // All trades should be LOST
        assertThat(allTrades).allMatch(t -> t.getStatus() == TradeStatus.LOST);

        // All trades should have negative P&L
        assertThat(allTrades).allMatch(t -> t.getPnl().compareTo(BigDecimal.ZERO) < 0);

        // Verify series is stopped
        TradeSeries savedSeries = seriesRepository.findById(series.getId()).orElseThrow();
        assertThat(savedSeries.getStatus()).isEqualTo(SeriesStatus.STOPPED);
        assertThat(savedSeries.getTotalPnl()).isLessThan(BigDecimal.ZERO);
        assertThat(savedSeries.getEndedAt()).isNotNull();
    }

    @Test
    void shouldTrackFullMartingaleFlowEndToEnd() {
        // Full flow: LONG win -> reset -> LONG loss -> double SHORT -> SHORT win -> reset
        MartingaleState state = martingaleEngine.initSeries(config, Direction.LONG);

        TradeSeries series = TradeSeries.builder()
                .instrument("PF_XBTUSD")
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series = seriesRepository.save(series);

        BigDecimal feePercent = new BigDecimal("0.05");
        BigDecimal entryPrice = new BigDecimal("50000");

        // --- Trade 1: LONG WIN ---
        BigDecimal exitPrice1 = new BigDecimal("50750"); // +1.5%
        BigDecimal netPnl1 = pnlCalculator.calculateNetPnl(Direction.LONG,
                state.getCurrentStake(), config.getLeverage(), entryPrice, exitPrice1, feePercent);
        BigDecimal fees1 = pnlCalculator.calculateFees(state.getCurrentStake(), config.getLeverage(), feePercent);

        Trade trade1 = Trade.builder()
                .series(series)
                .instrument("PF_XBTUSD")
                .krakenOrderId("flow-order-1")
                .direction(Direction.LONG)
                .status(TradeStatus.WON)
                .stake(state.getCurrentStake())
                .leverage(config.getLeverage())
                .entryPrice(entryPrice)
                .exitPrice(exitPrice1)
                .pnl(netPnl1)
                .fees(fees1)
                .doublingStep(0)
                .openedAt(Instant.now())
                .closedAt(Instant.now())
                .build();
        tradeRepository.save(trade1);

        series.setTotalPnl(series.getTotalPnl().add(netPnl1));
        series.setTotalFees(series.getTotalFees().add(fees1));
        series.setStatus(SeriesStatus.COMPLETED);
        series.setEndedAt(Instant.now());
        seriesRepository.save(series);

        // Win resets state
        state = martingaleEngine.onWin(state, config, Direction.LONG);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("100");
        assertThat(state.getCurrentDoubling()).isEqualTo(0);

        // --- New series for Trade 2: LONG LOSS ---
        TradeSeries series2 = TradeSeries.builder()
                .instrument("PF_XBTUSD")
                .status(SeriesStatus.ACTIVE)
                .currentDoubling(0)
                .totalPnl(BigDecimal.ZERO)
                .totalFees(BigDecimal.ZERO)
                .startedAt(Instant.now())
                .build();
        series2 = seriesRepository.save(series2);

        BigDecimal exitPrice2 = new BigDecimal("49500"); // -1.0%
        BigDecimal netPnl2 = pnlCalculator.calculateNetPnl(Direction.LONG,
                state.getCurrentStake(), config.getLeverage(), entryPrice, exitPrice2, feePercent);
        BigDecimal fees2 = pnlCalculator.calculateFees(state.getCurrentStake(), config.getLeverage(), feePercent);

        Trade trade2 = Trade.builder()
                .series(series2)
                .instrument("PF_XBTUSD")
                .krakenOrderId("flow-order-2")
                .direction(Direction.LONG)
                .status(TradeStatus.LOST)
                .stake(state.getCurrentStake())
                .leverage(config.getLeverage())
                .entryPrice(entryPrice)
                .exitPrice(exitPrice2)
                .pnl(netPnl2)
                .fees(fees2)
                .doublingStep(0)
                .openedAt(Instant.now())
                .closedAt(Instant.now())
                .build();
        tradeRepository.save(trade2);

        series2.setTotalPnl(series2.getTotalPnl().add(netPnl2));
        series2.setTotalFees(series2.getTotalFees().add(fees2));

        // Loss doubles and inverts
        state = martingaleEngine.onLoss(state, config);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("200");
        assertThat(state.getCurrentDirection()).isEqualTo(Direction.SHORT);
        assertThat(state.getCurrentDoubling()).isEqualTo(1);

        series2.setCurrentDoubling(1);
        seriesRepository.save(series2);

        // --- Trade 3: SHORT WIN (recovers) ---
        BigDecimal exitPrice3 = new BigDecimal("49250"); // SHORT from 50000, exit at 49250 = +1.5%
        BigDecimal netPnl3 = pnlCalculator.calculateNetPnl(Direction.SHORT,
                state.getCurrentStake(), config.getLeverage(), entryPrice, exitPrice3, feePercent);
        BigDecimal fees3 = pnlCalculator.calculateFees(state.getCurrentStake(), config.getLeverage(), feePercent);

        Trade trade3 = Trade.builder()
                .series(series2)
                .instrument("PF_XBTUSD")
                .krakenOrderId("flow-order-3")
                .direction(Direction.SHORT)
                .status(TradeStatus.WON)
                .stake(state.getCurrentStake())
                .leverage(config.getLeverage())
                .entryPrice(entryPrice)
                .exitPrice(exitPrice3)
                .pnl(netPnl3)
                .fees(fees3)
                .doublingStep(1)
                .openedAt(Instant.now())
                .closedAt(Instant.now())
                .build();
        tradeRepository.save(trade3);

        series2.setTotalPnl(series2.getTotalPnl().add(netPnl3));
        series2.setTotalFees(series2.getTotalFees().add(fees3));
        series2.setStatus(SeriesStatus.COMPLETED);
        series2.setEndedAt(Instant.now());
        seriesRepository.save(series2);

        // Win resets again
        state = martingaleEngine.onWin(state, config, Direction.LONG);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("100");
        assertThat(state.getCurrentDoubling()).isEqualTo(0);

        // --- Verify all persisted data ---
        List<Trade> allTrades = tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD");
        assertThat(allTrades).hasSize(3);

        long wonCount = allTrades.stream().filter(t -> t.getStatus() == TradeStatus.WON).count();
        long lostCount = allTrades.stream().filter(t -> t.getStatus() == TradeStatus.LOST).count();
        assertThat(wonCount).isEqualTo(2);
        assertThat(lostCount).isEqualTo(1);

        List<TradeSeries> allSeries = seriesRepository.findAll();
        assertThat(allSeries).hasSize(2);
        assertThat(allSeries).allMatch(s -> s.getStatus() == SeriesStatus.COMPLETED);

        // Verify bot config is still active
        BotConfig savedConfig = botConfigRepository.findById(config.getId()).orElseThrow();
        assertThat(savedConfig.isActive()).isTrue();
        assertThat(botConfigRepository.findByActiveTrue()).hasSize(1);
    }
}
