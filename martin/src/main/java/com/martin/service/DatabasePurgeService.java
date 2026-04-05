package com.martin.service;

import com.martin.domain.repository.TradeRepository;
import com.martin.domain.repository.TradeSeriesRepository;
import com.martin.grid.GridStateRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

@Service
@RequiredArgsConstructor
public class DatabasePurgeService {

    private static final Logger log = LoggerFactory.getLogger(DatabasePurgeService.class);

    private final TradeRepository tradeRepository;
    private final TradeSeriesRepository tradeSeriesRepository;
    private final GridStateRepository gridStateRepository;

    /**
     * Purge data older than 1 month. Runs daily at 3:00 AM.
     */
    @Scheduled(cron = "0 0 3 * * *")
    @Transactional
    public void purgeOldData() {
        Instant cutoff = Instant.now().minus(30, ChronoUnit.DAYS);
        log.info("DB purge started — deleting data older than {}", cutoff);

        // Purge old trades
        int tradesDeleted = tradeRepository.deleteByClosedAtBeforeAndStatusNot(cutoff);
        log.info("Purged {} old trades", tradesDeleted);

        // Purge old trade series (completed only)
        int seriesDeleted = tradeSeriesRepository.deleteByEndedAtBefore(cutoff);
        log.info("Purged {} old trade series", seriesDeleted);

        // Purge inactive grid states older than 1 month
        int gridsDeleted = gridStateRepository.deleteByActiveFalseAndStartedAtBefore(cutoff);
        log.info("Purged {} old inactive grids", gridsDeleted);

        log.info("DB purge completed — trades={}, series={}, grids={}", tradesDeleted, seriesDeleted, gridsDeleted);
    }
}
