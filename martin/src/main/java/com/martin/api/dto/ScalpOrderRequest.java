package com.martin.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ScalpOrderRequest {
    private String instrument;
    private String side;
    private double size;
    private boolean demo;
    private boolean reduceOnly;
}
