package com.martin.position;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PositionRepository extends JpaRepository<PositionState, Long> {

    List<PositionState> findByActiveTrue();

    Optional<PositionState> findByInstrument(String instrument);
}
