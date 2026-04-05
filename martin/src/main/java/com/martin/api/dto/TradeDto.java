package com.martin.api.dto;

import lombok.*;
import java.math.BigDecimal;
import java.time.Instant;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class TradeDto {
    private Long id;
    private String instrument;
    private String direction;
    private String status;
    private String source;
    private BigDecimal stake;
    private int leverage;
    private BigDecimal entryPrice;
    private BigDecimal exitPrice;
    private BigDecimal pnl;
    private BigDecimal fees;
    private int doublingStep;
    private Instant openedAt;
    private Instant closedAt;
}
