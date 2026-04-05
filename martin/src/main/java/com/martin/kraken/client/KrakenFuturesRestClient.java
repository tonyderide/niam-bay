package com.martin.kraken.client;

import com.martin.api.dto.AccountSummaryResponse;
import com.martin.kraken.auth.KrakenAuthenticator;
import com.martin.kraken.config.KrakenProperties;
import com.martin.kraken.dto.*;
import org.springframework.http.MediaType;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Component
public class KrakenFuturesRestClient {

    private final WebClient webClient;
    private final WebClient demoWebClient;
    private final KrakenProperties properties;
    private final KrakenAuthenticator authenticator;

    @Autowired
    public KrakenFuturesRestClient(KrakenProperties properties, KrakenAuthenticator authenticator) {
        this.properties = properties;
        this.authenticator = authenticator;
        this.webClient = WebClient.builder()
                .baseUrl(properties.getRestUrl())
                .build();
        this.demoWebClient = WebClient.builder()
                .baseUrl(properties.getDemoRestUrl())
                .build();
    }

    // Visible for testing
    KrakenFuturesRestClient(WebClient webClient, WebClient demoWebClient,
                            KrakenProperties properties, KrakenAuthenticator authenticator) {
        this.webClient = webClient;
        this.demoWebClient = demoWebClient;
        this.properties = properties;
        this.authenticator = authenticator;
    }

    private WebClient client(boolean demo) {
        return demo ? demoWebClient : webClient;
    }

    /**
     * Public endpoint - get all tickers.
     */
    public Mono<KrakenTickerResponse> getTickers(boolean demo) {
        return client(demo).get()
                .uri("/tickers")
                .retrieve()
                .bodyToMono(KrakenTickerResponse.class);
    }

    /**
     * Authenticated endpoint - send an order.
     */
    public Mono<KrakenOrderResponse> sendOrder(KrakenOrderRequest order, boolean demo) {
        String endpointPath = "/api/v3/sendorder";
        String nonce = authenticator.generateNonce();

        StringBuilder postData = new StringBuilder();
        postData.append("orderType=").append(order.getOrderType());
        postData.append("&symbol=").append(order.getSymbol());
        postData.append("&side=").append(order.getSide());
        postData.append("&size=").append(order.getSize());
        if (order.getLimitPrice() != null) {
            postData.append("&limitPrice=").append(order.getLimitPrice());
        }
        if (order.getStopPrice() != null) {
            postData.append("&stopPrice=").append(order.getStopPrice());
        }
        if (Boolean.TRUE.equals(order.getReduceOnly())) {
            postData.append("&reduceOnly=true");
        }
        if (order.getTriggerSignal() != null) {
            postData.append("&triggerSignal=").append(order.getTriggerSignal());
        }
        if (Boolean.TRUE.equals(order.getPostOnly())) {
            postData.append("&postOnly=true");
        }

        String signature = authenticator.sign(properties.getApiSecret(demo), postData.toString(), nonce, endpointPath);

        return client(demo).post()
                .uri("/sendorder")
                .header("APIKey", properties.getApiKey(demo))
                .header("Nonce", nonce)
                .header("Authent", signature)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .body(BodyInserters.fromValue(postData.toString()))
                .retrieve()
                .bodyToMono(KrakenOrderResponse.class);
    }

    /**
     * Authenticated endpoint - cancel an order by ID.
     */
    public Mono<KrakenOrderResponse> cancelOrder(String orderId, boolean demo) {
        String endpointPath = "/api/v3/cancelorder";
        String nonce = authenticator.generateNonce();
        String postData = "order_id=" + orderId;

        String signature = authenticator.sign(properties.getApiSecret(demo), postData, nonce, endpointPath);

        return client(demo).post()
                .uri("/cancelorder")
                .header("APIKey", properties.getApiKey(demo))
                .header("Nonce", nonce)
                .header("Authent", signature)
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .body(BodyInserters.fromValue(postData))
                .retrieve()
                .bodyToMono(KrakenOrderResponse.class);
    }

    /**
     * Authenticated endpoint - get open orders.
     */
    public Mono<KrakenOpenOrdersResponse> getOpenOrders(boolean demo) {
        String endpointPath = "/api/v3/openorders";
        String nonce = authenticator.generateNonce();
        String postData = "";

        String signature = authenticator.sign(properties.getApiSecret(demo), postData, nonce, endpointPath);

        return client(demo).get()
                .uri("/openorders")
                .header("APIKey", properties.getApiKey(demo))
                .header("Nonce", nonce)
                .header("Authent", signature)
                .retrieve()
                .bodyToMono(KrakenOpenOrdersResponse.class);
    }

    /**
     * Authenticated endpoint - get recent fills (to retrieve actual fill prices).
     */
    public Mono<KrakenFillsResponse> getFills(boolean demo) {
        String endpointPath = "/api/v3/fills";
        String nonce = authenticator.generateNonce();
        String postData = "";

        String signature = authenticator.sign(properties.getApiSecret(demo), postData, nonce, endpointPath);

        return client(demo).get()
                .uri("/fills")
                .header("APIKey", properties.getApiKey(demo))
                .header("Nonce", nonce)
                .header("Authent", signature)
                .retrieve()
                .bodyToMono(KrakenFillsResponse.class);
    }

    /**
     * Authenticated endpoint - get account balances.
     */
    public Mono<java.util.Map> getAccounts(boolean demo) {
        String endpointPath = "/api/v3/accounts";
        String nonce = authenticator.generateNonce();
        String postData = "";

        String signature = authenticator.sign(properties.getApiSecret(demo), postData, nonce, endpointPath);

        return client(demo).get()
                .uri("/accounts")
                .header("APIKey", properties.getApiKey(demo))
                .header("Nonce", nonce)
                .header("Authent", signature)
                .retrieve()
                .bodyToMono(java.util.Map.class);
    }

    /**
     * Public endpoint - get OHLC candles for chart history.
     */
    public Mono<java.util.Map> getOhlc(String instrument, int minutes) {
        return getOhlc(instrument, minutes, "1m");
    }

    public Mono<java.util.Map> getOhlc(String instrument, int minutes, String resolution) {
        long now = System.currentTimeMillis() / 1000;
        long from = now - (minutes * 60L);

        return WebClient.create("https://futures.kraken.com")
                .get()
                .uri("/api/charts/v1/trade/{instrument}/{resolution}?from={from}&to={to}",
                        instrument, resolution, from, now)
                .retrieve()
                .bodyToMono(java.util.Map.class);
    }

    /**
     * Returns a summary of the account: balance, margin, unrealized PnL, open positions count.
     */
    @SuppressWarnings("unchecked")
    public AccountSummaryResponse getAccountSummary(boolean demo) {
        try {
            java.util.Map<?, ?> accountResp = getAccounts(demo).block();
            KrakenPositionResponse posResp = getOpenPositions(demo).block();

            double balance = 0.0;
            double availableMargin = 0.0;
            double initialMargin = 0.0;

            if (accountResp != null) {
                Object accounts = accountResp.get("accounts");
                if (accounts instanceof java.util.Map) {
                    Object flex = ((java.util.Map<?, ?>) accounts).get("flex");
                    if (flex instanceof java.util.Map) {
                        java.util.Map<?, ?> flexMap = (java.util.Map<?, ?>) flex;
                        balance = toDouble(flexMap.get("balanceValue"));
                        availableMargin = toDouble(flexMap.get("availableMargin"));
                        initialMargin = toDouble(flexMap.get("initialMargin"));
                    }
                }
            }

            double unrealizedPnl = 0.0;
            int openPositionsCount = 0;

            if (posResp != null && posResp.getOpenPositions() != null) {
                for (KrakenPositionResponse.Position pos : posResp.getOpenPositions()) {
                    if (pos.getUnrealizedPnl() != null) {
                        unrealizedPnl += pos.getUnrealizedPnl();
                    }
                    openPositionsCount++;
                }
            }

            return AccountSummaryResponse.builder()
                    .balance(balance)
                    .availableMargin(availableMargin)
                    .initialMargin(initialMargin)
                    .unrealizedPnl(unrealizedPnl)
                    .pnl24h(0.0)
                    .openPositionsCount(openPositionsCount)
                    .lastUpdatedAt(System.currentTimeMillis())
                    .error(false)
                    .build();
        } catch (Exception e) {
            return AccountSummaryResponse.builder()
                    .error(true)
                    .errorMessage(e.getMessage())
                    .lastUpdatedAt(System.currentTimeMillis())
                    .build();
        }
    }

    /**
     * Returns the list of available perpetual futures instruments (PF_ prefix).
     */
    public List<String> getAvailableFuturesInstruments(boolean demo) {
        try {
            KrakenTickerResponse resp = getTickers(demo).block();
            if (resp == null || resp.getTickers() == null) {
                return Arrays.asList("PF_XBTUSD", "PF_ETHUSD");
            }
            List<String> instruments = new ArrayList<>();
            for (KrakenTickerResponse.Ticker ticker : resp.getTickers()) {
                if (ticker.getSymbol() != null && ticker.getSymbol().startsWith("PF_")) {
                    instruments.add(ticker.getSymbol());
                }
            }
            instruments.sort(String::compareTo);
            return instruments.isEmpty() ? Arrays.asList("PF_XBTUSD", "PF_ETHUSD") : instruments;
        } catch (Exception e) {
            return Arrays.asList("PF_XBTUSD", "PF_ETHUSD");
        }
    }

    private double toDouble(Object val) {
        if (val == null) return 0.0;
        if (val instanceof Number) return ((Number) val).doubleValue();
        try {
            return Double.parseDouble(val.toString());
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }

    /**
     * Authenticated endpoint - get open positions.
     */
    public Mono<KrakenPositionResponse> getOpenPositions(boolean demo) {
        String endpointPath = "/api/v3/openpositions";
        String nonce = authenticator.generateNonce();
        String postData = "";

        String signature = authenticator.sign(properties.getApiSecret(demo), postData, nonce, endpointPath);

        return client(demo).get()
                .uri("/openpositions")
                .header("APIKey", properties.getApiKey(demo))
                .header("Nonce", nonce)
                .header("Authent", signature)
                .retrieve()
                .bodyToMono(KrakenPositionResponse.class);
    }
}
