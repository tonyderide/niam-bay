package com.martin.domain.entity;

import com.martin.domain.enums.SeriesStatus;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "trade_series")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class TradeSeries {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String instrument;
    @Enumerated(EnumType.STRING)
    private SeriesStatus status;
    private int currentDoubling;
    private BigDecimal totalPnl;
    private BigDecimal totalFees;
    private Instant startedAt;
    private Instant endedAt;
    @OneToMany(mappedBy = "series", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Trade> trades = new ArrayList<>();
}
