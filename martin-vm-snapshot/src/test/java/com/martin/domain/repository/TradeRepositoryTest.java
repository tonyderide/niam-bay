package com.martin.domain.repository;

import com.martin.domain.entity.Trade;
import com.martin.domain.entity.TradeSeries;
import com.martin.domain.enums.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import java.math.BigDecimal;
import java.time.Instant;
import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class TradeRepositoryTest {
    @Autowired TradeRepository tradeRepository;
    @Autowired TradeSeriesRepository seriesRepository;

    @Test
    void shouldPersistAndRetrieveTrade() {
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
                .direction(Direction.LONG)
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("100"))
                .leverage(5)
                .doublingStep(0)
                .openedAt(Instant.now())
                .build();
        trade = tradeRepository.save(trade);

        assertThat(trade.getId()).isNotNull();
        var found = tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD");
        assertThat(found).hasSize(1);
    }
}
