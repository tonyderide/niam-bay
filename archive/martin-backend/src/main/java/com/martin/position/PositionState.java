package com.martin.position;

import jakarta.persistence.*;
import lombok.Data;

import java.time.Instant;

@Data
@Entity
@Table(name = "positions")
public class PositionState {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String instrument;

    @Column(nullable = false)
    private boolean active;

    @Column
    private String direction; // "SHORT" or "LONG"

    @Column
    private double entryPrice;

    @Column
    private double size;        // in BTC

    @Column
    private double capital;     // in USD

    @Column
    private int leverage;

    @Column
    private double slPrice;

    @Column
    private double tpPrice;

    @Column
    private double slPct;

    @Column
    private double tpPct;

    @Column
    private String entryOrderId;

    @Column
    private String slOrderId;

    @Column
    private String tpOrderId;

    @Column
    private double realizedPnl;

    @Column
    private String status;      // OPENING, OPEN, CLOSING, CLOSED

    @Column
    private Instant startedAt;

    @Column
    private String demo;

    public boolean isDemo() { return "true".equals(demo); }
}
