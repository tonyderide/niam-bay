package com.martin.engine;

import com.martin.domain.enums.Direction;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.assertj.core.api.Assertions.assertThat;

class PnlCalculatorTest {
    private final PnlCalculator calculator = new PnlCalculator();

    @Test
    void shouldCalculateLongProfit() {
        BigDecimal pnl = calculator.calculatePnl(Direction.LONG, new BigDecimal("100"), 5,
                new BigDecimal("50000"), new BigDecimal("50500"));
        assertThat(pnl).isEqualByComparingTo("5.00");
    }

    @Test
    void shouldCalculateShortProfit() {
        BigDecimal pnl = calculator.calculatePnl(Direction.SHORT, new BigDecimal("100"), 5,
                new BigDecimal("50000"), new BigDecimal("49500"));
        assertThat(pnl).isEqualByComparingTo("5.00");
    }

    @Test
    void shouldCalculateLongLoss() {
        BigDecimal pnl = calculator.calculatePnl(Direction.LONG, new BigDecimal("100"), 5,
                new BigDecimal("50000"), new BigDecimal("49500"));
        assertThat(pnl).isEqualByComparingTo("-5.00");
    }

    @Test
    void shouldCalculateFees() {
        BigDecimal fees = calculator.calculateFees(new BigDecimal("100"), 5, new BigDecimal("0.05"));
        assertThat(fees).isEqualByComparingTo("0.50");
    }

    @Test
    void shouldCalculateNetPnl() {
        BigDecimal netPnl = calculator.calculateNetPnl(Direction.LONG, new BigDecimal("100"), 5,
                new BigDecimal("50000"), new BigDecimal("50500"), new BigDecimal("0.05"));
        assertThat(netPnl).isEqualByComparingTo("4.50");
    }
}
