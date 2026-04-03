package com.martin.engine;

import com.martin.domain.enums.Direction;
import lombok.*;
import java.math.BigDecimal;

@Getter @Setter @Builder @AllArgsConstructor @NoArgsConstructor
public class MartingaleState {
    private String instrument;
    private Direction currentDirection;
    private BigDecimal currentStake;
    private int currentDoubling;
    private boolean active;
}
