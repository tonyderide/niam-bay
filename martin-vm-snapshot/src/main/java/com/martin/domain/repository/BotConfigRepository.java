package com.martin.domain.repository;

import com.martin.domain.entity.BotConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface BotConfigRepository extends JpaRepository<BotConfig, Long> {
    List<BotConfig> findByActiveTrue();
    List<BotConfig> findByInstrument(String instrument);
}
