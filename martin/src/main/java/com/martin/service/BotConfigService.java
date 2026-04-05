package com.martin.service;

import com.martin.domain.entity.BotConfig;
import com.martin.domain.repository.BotConfigRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BotConfigService {
    private final BotConfigRepository repository;

    public BotConfig save(BotConfig config) { return repository.save(config); }
    public List<BotConfig> getActiveConfigs() { return repository.findByActiveTrue(); }
    public List<BotConfig> getAllConfigs() { return repository.findAll(); }
    public BotConfig findByInstrument(String instrument) {
        return repository.findByInstrument(instrument).stream().findFirst().orElse(null);
    }
    public BotConfig getById(Long id) {
        return repository.findById(id).orElseThrow(() -> new IllegalArgumentException("Config not found: " + id));
    }
}
