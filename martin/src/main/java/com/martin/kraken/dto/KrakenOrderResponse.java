package com.martin.kraken.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class KrakenOrderResponse {

    private String result;
    private String error;
    private SendStatus sendStatus;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class SendStatus {
        @JsonProperty("order_id")
        private String orderId;
        private String status;
        private String receivedTime;
    }
}
