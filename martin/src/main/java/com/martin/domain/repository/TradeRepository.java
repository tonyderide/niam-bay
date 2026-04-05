package com.martin.domain.repository;

import com.martin.domain.entity.Trade;
import com.martin.domain.enums.TradeStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.List;

public interface TradeRepository extends JpaRepository<Trade, Long> {
    List<Trade> findByInstrumentOrderByOpenedAtDesc(String instrument);
    List<Trade> findByStatus(TradeStatus status);
    List<Trade> findAllByOrderByClosedAtAsc();
    List<Trade> findByInstrumentOrderByClosedAtAsc(String instrument);
    boolean existsByKrakenFillId(String krakenFillId);

    @Modifying
    @Query("DELETE FROM Trade t WHERE t.closedAt < :cutoff AND t.status <> 'OPEN'")
    int deleteByClosedAtBeforeAndStatusNot(Instant cutoff);

    @Modifying
    @Query("DELETE FROM Trade t WHERE t.source = :source")
    int deleteBySource(String source);
}
