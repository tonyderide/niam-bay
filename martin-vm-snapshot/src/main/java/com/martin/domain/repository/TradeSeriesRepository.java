package com.martin.domain.repository;

import com.martin.domain.entity.TradeSeries;
import com.martin.domain.enums.SeriesStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.List;

public interface TradeSeriesRepository extends JpaRepository<TradeSeries, Long> {
    List<TradeSeries> findByInstrumentAndStatus(String instrument, SeriesStatus status);

    @Modifying
    @Query("DELETE FROM TradeSeries ts WHERE ts.endedAt < :cutoff AND ts.status <> 'ACTIVE'")
    int deleteByEndedAtBefore(Instant cutoff);
}
