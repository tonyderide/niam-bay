package com.martin.service;

import com.martin.domain.entity.BotConfig;
import com.martin.domain.entity.Trade;
import com.martin.domain.entity.TradeSeries;
import com.martin.domain.enums.*;
import com.martin.domain.repository.*;
import com.martin.engine.*;
import com.martin.kraken.client.*;
import com.martin.kraken.dto.KrakenOrderResponse;
import com.martin.kraken.dto.KrakenTickerResponse;
import com.martin.strategy.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import java.math.BigDecimal;
import java.util.Collections;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TradingOrchestratorTest {
    @InjectMocks private TradingOrchestrator orchestrator;
    @Mock private MartingaleEngine martingaleEngine;
    @Mock private PnlCalculator pnlCalculator;
    @Mock private TechnicalAnalysisService technicalAnalysis;
    @Mock private KrakenFuturesRestClient krakenClient;
    @Mock private KrakenFuturesWsClient krakenWsClient;
    @Mock private TradeRepository tradeRepository;
    @Mock private TradeSeriesRepository seriesRepository;
    @Mock private LiveUpdateService liveUpdateService;
    @Spy private ObjectMapper objectMapper = new ObjectMapper();

    private BotConfig config;

    @BeforeEach
    void setUp() {
        config = BotConfig.builder()
                .instrument("PF_XBTUSD")
                .initialStake(new BigDecimal("100"))
                .maxDoublings(5)
                .takeProfitPct(new BigDecimal("1.5"))
                .stopLossPct(new BigDecimal("1.0"))
                .leverage(5)
                .signalStrategy("RSI_EMA")
                .active(true)
                .demo(false)
                .build();
    }

    @Test
    void shouldStartSeriesWithDirection() {
        MartingaleState state = MartingaleState.builder()
                .instrument("PF_XBTUSD")
                .currentDirection(Direction.LONG)
                .currentStake(new BigDecimal("100"))
                .currentDoubling(0)
                .active(true)
                .build();

        when(martingaleEngine.initSeries(any(), eq(Direction.LONG))).thenReturn(state);
        when(seriesRepository.save(any())).thenAnswer(i -> i.getArgument(0));

        // Seed REST fallback price
        KrakenTickerResponse tickerResp = new KrakenTickerResponse();
        KrakenTickerResponse.Ticker ticker = new KrakenTickerResponse.Ticker();
        ticker.setSymbol("PF_XBTUSD");
        ticker.setLast(80000.0);
        tickerResp.setTickers(java.util.List.of(ticker));
        tickerResp.setResult("success");
        when(krakenClient.getTickers(anyBoolean())).thenReturn(Mono.just(tickerResp));

        KrakenOrderResponse response = new KrakenOrderResponse();
        KrakenOrderResponse.SendStatus sendStatus = new KrakenOrderResponse.SendStatus();
        sendStatus.setOrderId("order-123");
        sendStatus.setStatus("placed");
        response.setSendStatus(sendStatus);
        response.setResult("success");
        when(krakenClient.sendOrder(any(), anyBoolean())).thenReturn(Mono.just(response));
        when(tradeRepository.save(any())).thenAnswer(i -> i.getArgument(0));
        when(tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD"))
                .thenReturn(Collections.emptyList());

        orchestrator.startSeriesWithDirection(config, Direction.LONG);
        try { Thread.sleep(300); } catch (InterruptedException ignored) {}

        verify(krakenClient, times(3)).sendOrder(any(), anyBoolean());
        verify(seriesRepository).save(any(TradeSeries.class));
    }

    @Test
    void placeOrderShouldSendThreeOrdersOnSuccess() {
        MartingaleState state = MartingaleState.builder()
                .instrument("PF_XBTUSD")
                .currentDirection(Direction.LONG)
                .currentStake(new BigDecimal("1"))
                .currentDoubling(0)
                .active(true)
                .build();
        TradeSeries series = TradeSeries.builder().build();

        KrakenOrderResponse mktResponse = buildOrderResponse("mkt-001");
        KrakenOrderResponse tpResponse  = buildOrderResponse("tp-001");
        KrakenOrderResponse slResponse  = buildOrderResponse("sl-001");

        when(krakenClient.sendOrder(any(), anyBoolean()))
                .thenReturn(Mono.just(mktResponse))
                .thenReturn(Mono.just(tpResponse))
                .thenReturn(Mono.just(slResponse));
        when(tradeRepository.save(any())).thenAnswer(i -> i.getArgument(0));

        // Seed REST fallback price
        com.martin.kraken.dto.KrakenTickerResponse tickerResp =
                new com.martin.kraken.dto.KrakenTickerResponse();
        com.martin.kraken.dto.KrakenTickerResponse.Ticker ticker =
                new com.martin.kraken.dto.KrakenTickerResponse.Ticker();
        ticker.setSymbol("PF_XBTUSD");
        ticker.setLast(80000.0);
        tickerResp.setTickers(java.util.List.of(ticker));
        tickerResp.setResult("success");
        when(krakenClient.getTickers(anyBoolean())).thenReturn(Mono.just(tickerResp));

        orchestrator.placeOrder(config, state, series);
        try { Thread.sleep(300); } catch (InterruptedException ignored) {}

        verify(krakenClient, times(3)).sendOrder(any(), anyBoolean());
    }

    @Test
    void handleWinShouldCancelPendingTPSLOrders() {
        Trade openTrade = Trade.builder()
                .instrument("PF_XBTUSD")
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("1"))
                .entryPrice(new BigDecimal("80000"))
                .direction(Direction.LONG)
                .series(TradeSeries.builder().totalPnl(BigDecimal.ZERO).totalFees(BigDecimal.ZERO).build())
                .build();

        MartingaleState state = MartingaleState.builder()
                .instrument("PF_XBTUSD")
                .currentDirection(Direction.LONG)
                .currentStake(new BigDecimal("1"))
                .currentDoubling(0)
                .active(true)
                .build();

        when(tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD"))
                .thenReturn(java.util.List.of(openTrade));
        when(tradeRepository.save(any())).thenAnswer(i -> i.getArgument(0));
        when(seriesRepository.save(any())).thenAnswer(i -> i.getArgument(0));
        when(pnlCalculator.calculateNetPnl(any(), any(), anyInt(), any(), any(), any()))
                .thenReturn(new BigDecimal("0.14"));
        when(pnlCalculator.calculateFees(any(), anyInt(), any()))
                .thenReturn(new BigDecimal("0.01"));
        when(krakenClient.cancelOrder(any(), anyBoolean())).thenReturn(Mono.just(new KrakenOrderResponse()));

        injectPendingOrders(orchestrator, "PF_XBTUSD", "tp-001", "sl-001");

        orchestrator.handleWin(config, state, openTrade, openTrade.getSeries(),
                new BigDecimal("81200"));
        try { Thread.sleep(300); } catch (InterruptedException ignored) {}

        verify(krakenClient, times(2)).cancelOrder(any(), anyBoolean());
    }

    @Test
    void handleLossShouldCancelPendingTPSLOrders() {
        Trade openTrade = Trade.builder()
                .instrument("PF_XBTUSD")
                .status(TradeStatus.OPEN)
                .stake(new BigDecimal("1"))
                .entryPrice(new BigDecimal("80000"))
                .direction(Direction.LONG)
                .series(TradeSeries.builder().totalPnl(BigDecimal.ZERO).totalFees(BigDecimal.ZERO).build())
                .build();

        MartingaleState updatedState = MartingaleState.builder()
                .instrument("PF_XBTUSD")
                .currentDirection(Direction.SHORT)
                .currentStake(new BigDecimal("2"))
                .currentDoubling(1)
                .active(true)
                .build();

        MartingaleState state = MartingaleState.builder()
                .instrument("PF_XBTUSD")
                .currentDirection(Direction.LONG)
                .currentStake(new BigDecimal("1"))
                .currentDoubling(0)
                .active(true)
                .build();

        when(tradeRepository.findByInstrumentOrderByOpenedAtDesc("PF_XBTUSD"))
                .thenReturn(java.util.List.of(openTrade));
        when(tradeRepository.save(any())).thenAnswer(i -> i.getArgument(0));
        when(seriesRepository.save(any())).thenAnswer(i -> i.getArgument(0));
        when(pnlCalculator.calculateNetPnl(any(), any(), anyInt(), any(), any(), any()))
                .thenReturn(new BigDecimal("-0.11"));
        when(pnlCalculator.calculateFees(any(), anyInt(), any()))
                .thenReturn(new BigDecimal("0.01"));
        when(martingaleEngine.onLoss(any(), any())).thenReturn(updatedState);
        when(krakenClient.cancelOrder(any(), anyBoolean())).thenReturn(Mono.just(new KrakenOrderResponse()));
        when(krakenClient.sendOrder(any(), anyBoolean())).thenReturn(Mono.just(buildOrderResponse("mkt-002")));

        // Seed REST fallback price so placeOrder gets past the early-return guard
        com.martin.kraken.dto.KrakenTickerResponse tickerResp =
                new com.martin.kraken.dto.KrakenTickerResponse();
        com.martin.kraken.dto.KrakenTickerResponse.Ticker ticker =
                new com.martin.kraken.dto.KrakenTickerResponse.Ticker();
        ticker.setSymbol("PF_XBTUSD");
        ticker.setLast(80000.0);
        tickerResp.setTickers(java.util.List.of(ticker));
        tickerResp.setResult("success");
        when(krakenClient.getTickers(anyBoolean())).thenReturn(Mono.just(tickerResp));

        injectPendingOrders(orchestrator, "PF_XBTUSD", "tp-001", "sl-001");

        orchestrator.handleLoss(config, state, openTrade, openTrade.getSeries(),
                new BigDecimal("79200"));
        try { Thread.sleep(300); } catch (InterruptedException ignored) {}

        verify(krakenClient, atLeastOnce()).cancelOrder(any(), anyBoolean());
    }

    // Helper methods
    private KrakenOrderResponse buildOrderResponse(String orderId) {
        KrakenOrderResponse r = new KrakenOrderResponse();
        KrakenOrderResponse.SendStatus s = new KrakenOrderResponse.SendStatus();
        s.setOrderId(orderId);
        s.setStatus("placed");
        r.setResult("success");
        r.setSendStatus(s);
        return r;
    }

    private void injectPendingOrders(TradingOrchestrator orchestrator,
                                      String instrument, String tpId, String slId) {
        try {
            var tpField = TradingOrchestrator.class.getDeclaredField("pendingTPOrders");
            var slField = TradingOrchestrator.class.getDeclaredField("pendingSLOrders");
            tpField.setAccessible(true);
            slField.setAccessible(true);
            ((java.util.concurrent.ConcurrentHashMap<String, String>) tpField.get(orchestrator))
                    .put(instrument, tpId);
            ((java.util.concurrent.ConcurrentHashMap<String, String>) slField.get(orchestrator))
                    .put(instrument, slId);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
