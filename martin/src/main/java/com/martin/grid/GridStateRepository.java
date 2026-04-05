package com.martin.grid;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.Optional;

public interface GridStateRepository extends JpaRepository<GridStateEntity, Long> {
    Optional<GridStateEntity> findByInstrument(String instrument);
    Optional<GridStateEntity> findByInstrumentAndActiveTrue(String instrument);
    java.util.List<GridStateEntity> findAllByActiveTrue();

    @Modifying
    @Query("DELETE FROM GridStateEntity g WHERE g.active = false AND g.startedAt < :cutoff")
    int deleteByActiveFalseAndStartedAtBefore(Instant cutoff);
}
