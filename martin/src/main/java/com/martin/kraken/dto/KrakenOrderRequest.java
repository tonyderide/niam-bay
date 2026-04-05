package com.martin.kraken.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class KrakenOrderRequest {

    private String orderType;
    private String symbol;
    private String side;
    private double size;
    private Double limitPrice;
    private Double stopPrice;
    private Boolean reduceOnly;
    private String triggerSignal;
    private Boolean postOnly;
}
