package com.martin.engine;

import com.martin.domain.enums.Direction;
import org.springframework.stereotype.Component;
import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;

@Component
public class PnlCalculator {
    private static final MathContext MC = new MathContext(10, RoundingMode.HALF_UP);

    public BigDecimal calculatePnl(Direction direction, BigDecimal stake, int leverage,
                                    BigDecimal entryPrice, BigDecimal exitPrice) {
        BigDecimal notional = stake.multiply(BigDecimal.valueOf(leverage));
        BigDecimal priceChange = direction == Direction.LONG
                ? exitPrice.subtract(entryPrice)
                : entryPrice.subtract(exitPrice);
        return notional.multiply(priceChange).divide(entryPrice, MC)
                .setScale(2, RoundingMode.HALF_UP);
    }

    public BigDecimal calculateFees(BigDecimal stake, int leverage, BigDecimal feePercent) {
        BigDecimal notional = stake.multiply(BigDecimal.valueOf(leverage));
        BigDecimal feeRate = feePercent.divide(BigDecimal.valueOf(100), MC);
        return notional.multiply(feeRate).multiply(BigDecimal.valueOf(2))
                .setScale(2, RoundingMode.HALF_UP);
    }

    public BigDecimal calculateNetPnl(Direction direction, BigDecimal stake, int leverage,
                                       BigDecimal entryPrice, BigDecimal exitPrice,
                                       BigDecimal feePercent) {
        BigDecimal grossPnl = calculatePnl(direction, stake, leverage, entryPrice, exitPrice);
        BigDecimal fees = calculateFees(stake, leverage, feePercent);
        return grossPnl.subtract(fees);
    }
}
