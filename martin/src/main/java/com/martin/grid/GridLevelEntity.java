package com.martin.grid;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;

@Entity
@Table(name = "grid_level")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class GridLevelEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "grid_state_id")
    private GridStateEntity gridState;

    private int idx;
    private double price;
    private String side;
    private String status;
    private String krakenOrderId;
    private Instant filledAt;
    private int roundTrips;
    @Builder.Default
    private boolean hasBuyFill = false;
    @Builder.Default
    private boolean hasSellFill = false;
}
