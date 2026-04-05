package com.martin.kraken.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class KrakenFillsResponse {

    private String result;
    private List<Fill> fills;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Fill {
        @JsonProperty("fill_id")
        private String fillId;
        private String symbol;
        private String side;
        @JsonProperty("order_id")
        private String orderId;
        private Double size;
        private Double price;
        private String fillTime;
        private String fillType;
    }
}
