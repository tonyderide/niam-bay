package com.martin.domain.entity;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;

@Entity
@Table(name = "bot_config")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class BotConfig {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String instrument;           // e.g. "PF_XBTUSD"
    private BigDecimal initialStake;     // mise initiale en USD
    private int maxDoublings;            // nombre max de doublements
    private BigDecimal takeProfitPct;    // ex: 1.5 pour 1.5%
    private BigDecimal stopLossPct;      // ex: 1.0 pour 1.0%
    private int leverage;                // max 10
    private String signalStrategy;       // "RSI_EMA", "MANUAL"
    private boolean active;              // bot actif ou non
    private boolean demo;               // true → demo-futures.kraken.com, false → futures.kraken.com
}
