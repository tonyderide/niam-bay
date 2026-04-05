package com.martin.kraken.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class KrakenOpenOrdersResponse {

    private String result;
    private List<Order> openOrders;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Order {
        @JsonProperty("order_id")
        private String orderId;
        private String symbol;
        private String side;
        private String orderType;
        private Double quantity;
        private Double filled;
        private Double limitPrice;
        private Double stopPrice;
        private Boolean reduceOnly;
        private String status;
    }
}
