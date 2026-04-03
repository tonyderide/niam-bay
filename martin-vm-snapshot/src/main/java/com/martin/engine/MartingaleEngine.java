package com.martin.engine;

import com.martin.domain.entity.BotConfig;
import com.martin.domain.enums.Direction;
import org.springframework.stereotype.Component;
import java.math.BigDecimal;
import java.math.RoundingMode;

@Component
public class MartingaleEngine {

    public MartingaleState initSeries(BotConfig config, Direction initialDirection) {
        return MartingaleState.builder()
                .instrument(config.getInstrument())
                .currentDirection(initialDirection)
                .currentStake(config.getInitialStake())
                .currentDoubling(0)
                .active(true)
                .build();
    }

    public MartingaleState onLoss(MartingaleState state, BotConfig config) {
        if (state.getCurrentDoubling() >= config.getMaxDoublings()) {
            state.setActive(false);
            return state;
        }
        state.setCurrentStake(state.getCurrentStake().multiply(BigDecimal.valueOf(2)));
        state.setCurrentDirection(invertDirection(state.getCurrentDirection()));
        state.setCurrentDoubling(state.getCurrentDoubling() + 1);
        return state;
    }

    public MartingaleState onWin(MartingaleState state, BotConfig config, Direction nextDirection) {
        state.setCurrentStake(config.getInitialStake());
        state.setCurrentDirection(nextDirection);
        state.setCurrentDoubling(0);
        state.setActive(true);
        return state;
    }

    public BigDecimal calculateTakeProfitPrice(Direction direction, BigDecimal entryPrice, BigDecimal tpPct) {
        BigDecimal delta = entryPrice.multiply(tpPct).divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
        return direction == Direction.LONG ? entryPrice.add(delta) : entryPrice.subtract(delta);
    }

    public BigDecimal calculateStopLossPrice(Direction direction, BigDecimal entryPrice, BigDecimal slPct) {
        BigDecimal delta = entryPrice.multiply(slPct).divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
        return direction == Direction.LONG ? entryPrice.subtract(delta) : entryPrice.add(delta);
    }

    private Direction invertDirection(Direction d) {
        return d == Direction.LONG ? Direction.SHORT : Direction.LONG;
    }
}
