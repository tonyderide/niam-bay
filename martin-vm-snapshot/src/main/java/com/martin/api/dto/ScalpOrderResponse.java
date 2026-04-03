package com.martin.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ScalpOrderResponse {
    private boolean success;
    private String orderId;
    private String error;
}
