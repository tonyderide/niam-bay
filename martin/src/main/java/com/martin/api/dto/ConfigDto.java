package com.martin.api.dto;

import lombok.*;
import java.math.BigDecimal;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class ConfigDto {
    private Long id;
    private String instrument;
    private BigDecimal initialStake;
    private int maxDoublings;
    private BigDecimal takeProfitPct;
    private BigDecimal stopLossPct;
    private int leverage;
    private String signalStrategy;
    private boolean active;
    private boolean demo;
}
