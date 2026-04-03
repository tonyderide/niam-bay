package com.martin.api;

import com.martin.api.controller.BotController;
import com.martin.domain.entity.Trade;
import com.martin.domain.enums.Direction;
import com.martin.domain.enums.TradeStatus;
import com.martin.domain.repository.TradeRepository;
import com.martin.engine.MartingaleEngine;
import com.martin.engine.MartingaleState;
import com.martin.kraken.client.KrakenFuturesRestClient;
import com.martin.service.BotConfigService;
import com.martin.service.TradingOrchestrator;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.reactive.server.WebTestClient;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

import static org.mockito.Mockito.when;

@WebFluxTest(BotController.class)
class BotControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockitoBean
    private TradingOrchestrator orchestrator;

    @MockitoBean
    private BotConfigService botConfigService;

    @MockitoBean
    private TradeRepository tradeRepository;

    @MockitoBean
    private MartingaleEngine martingaleEngine;

    @MockitoBean
    private KrakenFuturesRestClient krakenClient;

    @Test
    void dashboardReturnsCorrectData() {
        String instrument = "PF_XBTUSD";

        MartingaleState state = MartingaleState.builder()
                .instrument(instrument)
                .currentDirection(Direction.LONG)
                .currentStake(new BigDecimal("10"))
                .currentDoubling(1)
                .active(true)
                .build();

        Trade wonTrade = Trade.builder()
                .id(1L)
                .instrument(instrument)
                .direction(Direction.LONG)
                .status(TradeStatus.WON)
                .pnl(new BigDecimal("5.00"))
                .openedAt(Instant.now())
                .build();

        Trade lostTrade = Trade.builder()
                .id(2L)
                .instrument(instrument)
                .direction(Direction.SHORT)
                .status(TradeStatus.LOST)
                .pnl(new BigDecimal("-3.00"))
                .openedAt(Instant.now())
                .build();

        when(orchestrator.getState(instrument)).thenReturn(state);
        when(tradeRepository.findByInstrumentOrderByOpenedAtDesc(instrument))
                .thenReturn(List.of(wonTrade, lostTrade));

        webTestClient.get()
                .uri("/api/bot/dashboard/{instrument}", instrument)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.instrument").isEqualTo(instrument)
                .jsonPath("$.botActive").isEqualTo(true)
                .jsonPath("$.currentDirection").isEqualTo("LONG")
                .jsonPath("$.currentStake").isEqualTo(10)
                .jsonPath("$.currentDoubling").isEqualTo(1)
                .jsonPath("$.totalPnl").isEqualTo(2.0)
                .jsonPath("$.totalTrades").isEqualTo(2)
                .jsonPath("$.wins").isEqualTo(1)
                .jsonPath("$.losses").isEqualTo(1);
    }
}
