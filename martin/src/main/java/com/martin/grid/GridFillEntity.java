package com.martin.grid;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;

@Entity
@Table(name = "grid_fill")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class GridFillEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "grid_state_id")
    private GridStateEntity gridState;

    private String side;
    private double price;
    private Instant filledAt;
    private double profit;
}
