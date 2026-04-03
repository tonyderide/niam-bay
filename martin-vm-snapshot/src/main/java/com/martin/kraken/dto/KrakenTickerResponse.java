package com.martin.kraken.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class KrakenTickerResponse {

    private String result;
    private List<Ticker> tickers;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Ticker {
        private String symbol;
        private Double last;
        private Double bid;
        private Double ask;
        private Double markPrice;
    }
}
