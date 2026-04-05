package com.martin.domain.entity;

import com.martin.domain.enums.Direction;
import com.martin.domain.enums.TradeStatus;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.assertj.core.api.Assertions.assertThat;

class TradeTest {
    @Test
    void shouldBuildTradeWithAllFields() {
        Trade trade = Trade.builder()
                .instrument("PF_XBTUSD")
                .direction(Direction.LONG)
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("100"))
                .leverage(5)
                .doublingStep(0)
                .build();
        assertThat(trade.getInstrument()).isEqualTo("PF_XBTUSD");
        assertThat(trade.getDirection()).isEqualTo(Direction.LONG);
        assertThat(trade.getStake()).isEqualByComparingTo("100");
        assertThat(trade.getDoublingStep()).isZero();
    }
}
