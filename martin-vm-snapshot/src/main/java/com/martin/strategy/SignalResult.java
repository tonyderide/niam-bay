package com.martin.strategy;

import com.martin.domain.enums.Direction;
import lombok.*;

@Getter
@AllArgsConstructor
public class SignalResult {
    private final Direction direction;
    private final double confidence;
    private final String reason;
}
