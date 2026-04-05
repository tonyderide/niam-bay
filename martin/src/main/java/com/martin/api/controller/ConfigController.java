package com.martin.api.controller;

import com.martin.api.dto.ConfigDto;
import com.martin.domain.entity.BotConfig;
import com.martin.domain.repository.BotConfigRepository;
import com.martin.service.BotConfigService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/config")
@RequiredArgsConstructor
public class ConfigController {

    private static final Logger log = LoggerFactory.getLogger(ConfigController.class);

    private final BotConfigService botConfigService;
    private final BotConfigRepository botConfigRepository;

    @GetMapping
    public ResponseEntity<List<ConfigDto>> getActiveConfigs() {
        List<ConfigDto> configs = botConfigService.getActiveConfigs().stream()
                .map(this::toDto)
                .toList();
        log.debug(">> GET /config -> {} configs", configs.size());
        return ResponseEntity.ok(configs);
    }

    @PostMapping
    public ResponseEntity<ConfigDto> saveConfig(@RequestBody ConfigDto dto) {
        log.info(">> POST /config instrument={} id={}", dto.getInstrument(), dto.getId());
        BotConfig config = BotConfig.builder()
                .id(dto.getId())
                .instrument(dto.getInstrument())
                .initialStake(dto.getInitialStake())
                .maxDoublings(dto.getMaxDoublings())
                .takeProfitPct(dto.getTakeProfitPct())
                .stopLossPct(dto.getStopLossPct())
                .leverage(dto.getLeverage())
                .signalStrategy(dto.getSignalStrategy())
                .active(dto.isActive())
                .demo(dto.isDemo())
                .build();
        BotConfig saved = botConfigService.save(config);
        return ResponseEntity.ok(toDto(saved));
    }

    @DeleteMapping
    public ResponseEntity<String> deleteAllConfigs() {
        log.info(">> DELETE /config (all)");
        botConfigRepository.deleteAll();
        return ResponseEntity.ok("All configurations deleted");
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<String> deleteConfig(@PathVariable Long id) {
        log.info(">> DELETE /config/{}", id);
        botConfigRepository.deleteById(id);
        return ResponseEntity.ok("Configuration deleted");
    }

    private ConfigDto toDto(BotConfig config) {
        return ConfigDto.builder()
                .id(config.getId())
                .instrument(config.getInstrument())
                .initialStake(config.getInitialStake())
                .maxDoublings(config.getMaxDoublings())
                .takeProfitPct(config.getTakeProfitPct())
                .stopLossPct(config.getStopLossPct())
                .leverage(config.getLeverage())
                .signalStrategy(config.getSignalStrategy())
                .active(config.isActive())
                .demo(config.isDemo())
                .build();
    }
}
