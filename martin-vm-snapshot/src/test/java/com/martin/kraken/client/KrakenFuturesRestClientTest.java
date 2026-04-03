package com.martin.kraken.client;

import com.martin.kraken.auth.KrakenAuthenticator;
import com.martin.kraken.config.KrakenProperties;
import com.martin.kraken.dto.KrakenOrderResponse;
import com.martin.kraken.dto.KrakenTickerResponse;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.IOException;

import static org.assertj.core.api.Assertions.assertThat;

class KrakenFuturesRestClientTest {

    private MockWebServer mockWebServer;
    private KrakenFuturesRestClient restClient;

    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        String baseUrl = mockWebServer.url("/").toString();
        // Remove trailing slash
        if (baseUrl.endsWith("/")) {
            baseUrl = baseUrl.substring(0, baseUrl.length() - 1);
        }

        KrakenProperties properties = new KrakenProperties();
        properties.setRestUrl(baseUrl);
        properties.setDemoRestUrl(baseUrl);
        properties.setUseDemo(false);
        properties.setApiKey("test-api-key");
        properties.setApiSecret("dGVzdC1zZWNyZXQ="); // base64("test-secret")

        WebClient webClient = WebClient.builder().baseUrl(baseUrl).build();
        KrakenAuthenticator authenticator = new KrakenAuthenticator();

        // Pass same WebClient for both live and demo — both point to MockWebServer in tests
        restClient = new KrakenFuturesRestClient(webClient, webClient, properties, authenticator);
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void getTickersShouldReturnParsedResponse() {
        String jsonResponse = """
                {
                    "result": "success",
                    "tickers": [
                        {
                            "symbol": "PF_XBTUSD",
                            "last": 45000.5,
                            "bid": 44999.0,
                            "ask": 45001.0,
                            "markPrice": 45000.0
                        },
                        {
                            "symbol": "PF_ETHUSD",
                            "last": 3200.0,
                            "bid": 3199.0,
                            "ask": 3201.0,
                            "markPrice": 3200.5
                        }
                    ]
                }
                """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse));

        KrakenTickerResponse response = restClient.getTickers(false).block();

        assertThat(response).isNotNull();
        assertThat(response.getResult()).isEqualTo("success");
        assertThat(response.getTickers()).hasSize(2);
        assertThat(response.getTickers().get(0).getSymbol()).isEqualTo("PF_XBTUSD");
        assertThat(response.getTickers().get(0).getLast()).isEqualTo(45000.5);
        assertThat(response.getTickers().get(0).getBid()).isEqualTo(44999.0);
        assertThat(response.getTickers().get(0).getAsk()).isEqualTo(45001.0);
        assertThat(response.getTickers().get(0).getMarkPrice()).isEqualTo(45000.0);
        assertThat(response.getTickers().get(1).getSymbol()).isEqualTo("PF_ETHUSD");
    }

    @Test
    void sendOrderShouldIncludeReduceOnlyWhenTrue() throws InterruptedException {
        String jsonResponse = """
                {"result": "success", "sendStatus": {"order_id": "tp-001", "status": "placed"}}
                """;
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse));

        com.martin.kraken.dto.KrakenOrderRequest order = com.martin.kraken.dto.KrakenOrderRequest.builder()
                .orderType("take_profit")
                .symbol("PF_XBTUSD")
                .side("sell")
                .size(0.0001)
                .stopPrice(85000.0)
                .reduceOnly(true)
                .build();

        restClient.sendOrder(order, false).block();

        okhttp3.mockwebserver.RecordedRequest request = mockWebServer.takeRequest();
        String body = request.getBody().readUtf8();
        assertThat(body).contains("reduceOnly=true");
        assertThat(body).contains("orderType=take_profit");
        assertThat(body).contains("stopPrice=85000.0");
        assertThat(body).doesNotContain("takeProfitPrice");
    }

    @Test
    void cancelOrderShouldSendCorrectRequest() throws InterruptedException {
        String jsonResponse = """
                {
                    "result": "success",
                    "cancelStatus": {
                        "order_id": "order-abc",
                        "status": "cancelled"
                    }
                }
                """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse));

        KrakenOrderResponse response = restClient.cancelOrder("order-abc", false).block();

        assertThat(response).isNotNull();
        assertThat(response.getResult()).isEqualTo("success");

        okhttp3.mockwebserver.RecordedRequest request = mockWebServer.takeRequest();
        assertThat(request.getMethod()).isEqualTo("POST");
        assertThat(request.getPath()).isEqualTo("/cancelorder");
        assertThat(request.getBody().readUtf8()).contains("order_id=order-abc");
    }

    @Test
    void getTickersShouldHandleUnknownFields() {
        String jsonResponse = """
                {
                    "result": "success",
                    "serverTime": "2024-01-01T00:00:00Z",
                    "tickers": [
                        {
                            "symbol": "PF_XBTUSD",
                            "last": 45000.5,
                            "bid": 44999.0,
                            "ask": 45001.0,
                            "markPrice": 45000.0,
                            "unknownField": "should be ignored"
                        }
                    ]
                }
                """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse));

        KrakenTickerResponse response = restClient.getTickers(false).block();

        assertThat(response).isNotNull();
        assertThat(response.getResult()).isEqualTo("success");
        assertThat(response.getTickers()).hasSize(1);
    }
}
