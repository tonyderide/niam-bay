package com.martin.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

@Service
public class KeepAliveService {

    private static final Logger log = LoggerFactory.getLogger(KeepAliveService.class);
    private final WebClient client = WebClient.create("http://localhost:8081");

    /**
     * Self-ping every 5 minutes to keep the application warm.
     */
    @Scheduled(fixedRate = 300_000)
    public void keepAlive() {
        try {
            String status = client.get()
                    .uri("/api/bot/health")
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
            log.debug("Keep-alive ping OK: {}", status);
        } catch (Exception e) {
            log.warn("Keep-alive ping failed: {}", e.getMessage());
        }
    }
}
