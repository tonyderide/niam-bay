package com.martin.config;

import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.AppenderBase;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

public class LogStreamAppender extends AppenderBase<ILoggingEvent> {

    private static final Sinks.Many<String> sink = Sinks.many().multicast().onBackpressureBuffer(512, false);
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HH:mm:ss.SSS")
            .withZone(ZoneId.systemDefault());

    @Override
    protected void append(ILoggingEvent event) {
        String ts = TIME_FMT.format(Instant.ofEpochMilli(event.getTimeStamp()));
        String level = event.getLevel().toString();
        String logger = event.getLoggerName();
        // Use short logger name
        int lastDot = logger.lastIndexOf('.');
        if (lastDot >= 0) {
            logger = logger.substring(lastDot + 1);
        }
        String msg = event.getFormattedMessage()
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "");

        String json = String.format("{\"ts\":\"%s\",\"level\":\"%s\",\"logger\":\"%s\",\"msg\":\"%s\"}",
                ts, level, logger, msg);

        sink.tryEmitNext(json);
    }

    public static Flux<String> getLogStream() {
        return sink.asFlux();
    }
}
