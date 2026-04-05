package com.martin.kraken.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.List;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class KrakenPositionResponse {

    private String result;
    private List<Position> openPositions;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Position {
        private String symbol;
        private String side;
        private Double size;
        private Double price;
        private Double unrealizedPnl;
    }
}
