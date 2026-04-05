package com.martin.grid;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "grid_state")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class GridStateEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true)
    private String instrument;
    private boolean active;
    private boolean demo;
    private double centerPrice;
    private double upperBound;
    private double lowerBound;
    private double gridSpacing;
    private int totalLevels;
    private int leverage;
    private double amountPerLevel;
    private double capital;
    private double maxLossPercent;
    private BigDecimal totalProfit;
    private int completedRoundTrips;
    private Instant startedAt;

    @Builder.Default
    @Column(nullable = false)
    private String gridMode = "NEUTRAL";

    @OneToMany(mappedBy = "gridState", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    @OrderBy("idx ASC")
    @Builder.Default
    private List<GridLevelEntity> levels = new ArrayList<>();

    @OneToMany(mappedBy = "gridState", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    @OrderBy("filledAt DESC")
    @Builder.Default
    private List<GridFillEntity> fills = new ArrayList<>();
}
