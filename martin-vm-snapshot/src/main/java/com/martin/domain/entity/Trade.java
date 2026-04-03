package com.martin.domain.entity;

import com.martin.domain.enums.Direction;
import com.martin.domain.enums.TradeStatus;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "trades")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Trade {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "series_id")
    private TradeSeries series;
    private String instrument;
    private String krakenOrderId;
    private String krakenFillId;
    private String source;
    @Enumerated(EnumType.STRING)
    private Direction direction;
    @Enumerated(EnumType.STRING)
    private TradeStatus status;
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
