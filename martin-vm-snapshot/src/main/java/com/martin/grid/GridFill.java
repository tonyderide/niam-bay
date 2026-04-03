package com.martin.grid;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class GridFill {
    private String side;
    private double price;
    private Instant filledAt;
    private double profit;
}
