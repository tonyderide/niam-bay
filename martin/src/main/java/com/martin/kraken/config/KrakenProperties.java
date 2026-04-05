package com.martin.kraken.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "kraken.futures")
public class KrakenProperties {

    private String restUrl;
    private String wsUrl;
    private String demoRestUrl;
    private String demoWsUrl;
    private boolean useDemo;
    private String apiKey;
    private String apiSecret;
    private String demoApiKey;
    private String demoApiSecret;

    public String getActiveRestUrl() {
        return useDemo ? demoRestUrl : restUrl;
    }

    public String getActiveWsUrl() {
        return useDemo ? demoWsUrl : wsUrl;
    }

    public String getApiKey(boolean demo) {
        return demo ? demoApiKey : apiKey;
    }

    public String getApiSecret(boolean demo) {
        return demo ? demoApiSecret : apiSecret;
    }
}
