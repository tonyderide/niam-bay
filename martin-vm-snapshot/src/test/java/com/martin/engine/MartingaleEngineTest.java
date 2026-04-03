package com.martin.engine;

import com.martin.domain.entity.BotConfig;
import com.martin.domain.enums.Direction;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.assertj.core.api.Assertions.assertThat;

class MartingaleEngineTest {
    private MartingaleEngine engine;
    private BotConfig config;

    @BeforeEach
    void setUp() {
        engine = new MartingaleEngine();
        config = BotConfig.builder()
                .instrument("PF_XBTUSD")
                .initialStake(new BigDecimal("100"))
                .maxDoublings(5)
                .takeProfitPct(new BigDecimal("1.5"))
                .stopLossPct(new BigDecimal("1.0"))
                .leverage(5)
                .build();
    }

    @Test
    void shouldInitializeWithInitialStake() {
        MartingaleState state = engine.initSeries(config, Direction.LONG);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("100");
        assertThat(state.getCurrentDirection()).isEqualTo(Direction.LONG);
        assertThat(state.getCurrentDoubling()).isZero();
        assertThat(state.isActive()).isTrue();
    }

    @Test
    void shouldDoubleStakeAndInvertOnLoss() {
        MartingaleState state = engine.initSeries(config, Direction.LONG);
        state = engine.onLoss(state, config);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("200");
        assertThat(state.getCurrentDirection()).isEqualTo(Direction.SHORT);
        assertThat(state.getCurrentDoubling()).isEqualTo(1);
    }

    @Test
    void shouldDoubleMultipleTimes() {
        MartingaleState state = engine.initSeries(config, Direction.LONG);
        state = engine.onLoss(state, config); // 200, SHORT, d=1
        state = engine.onLoss(state, config); // 400, LONG, d=2
        state = engine.onLoss(state, config); // 800, SHORT, d=3
        assertThat(state.getCurrentStake()).isEqualByComparingTo("800");
        assertThat(state.getCurrentDirection()).isEqualTo(Direction.SHORT);
        assertThat(state.getCurrentDoubling()).isEqualTo(3);
    }

    @Test
    void shouldStopWhenMaxDoublingsReached() {
        MartingaleState state = engine.initSeries(config, Direction.LONG);
        for (int i = 0; i < 5; i++) { state = engine.onLoss(state, config); }
        state = engine.onLoss(state, config);
        assertThat(state.isActive()).isFalse();
    }

    @Test
    void shouldResetOnWin() {
        MartingaleState state = engine.initSeries(config, Direction.LONG);
        state = engine.onLoss(state, config);
        state = engine.onLoss(state, config);
        state = engine.onWin(state, config, Direction.SHORT);
        assertThat(state.getCurrentStake()).isEqualByComparingTo("100");
        assertThat(state.getCurrentDirection()).isEqualTo(Direction.SHORT);
        assertThat(state.getCurrentDoubling()).isZero();
    }

    @Test
    void shouldCalculateTakeProfitPrice() {
        BigDecimal tp = engine.calculateTakeProfitPrice(Direction.LONG, new BigDecimal("50000"), new BigDecimal("1.5"));
        assertThat(tp).isEqualByComparingTo("50750.00");
    }

    @Test
    void shouldCalculateStopLossPrice() {
        BigDecimal sl = engine.calculateStopLossPrice(Direction.LONG, new BigDecimal("50000"), new BigDecimal("1.0"));
        assertThat(sl).isEqualByComparingTo("49500.00");
    }

    @Test
    void shouldCalculateShortTakeProfitPrice() {
        BigDecimal tp = engine.calculateTakeProfitPrice(Direction.SHORT, new BigDecimal("50000"), new BigDecimal("1.5"));
        assertThat(tp).isEqualByComparingTo("49250.00");
    }

    @Test
    void shouldCalculateShortStopLossPrice() {
        BigDecimal sl = engine.calculateStopLossPrice(Direction.SHORT, new BigDecimal("50000"), new BigDecimal("1.0"));
        assertThat(sl).isEqualByComparingTo("50500.00");
    }
}
