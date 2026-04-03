package com.martin.api.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.RuntimeMXBean;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/system")
public class SystemController {

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> status() {
        Map<String, Object> info = new LinkedHashMap<>();

        // Uptime
        RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();
        long uptimeMs = runtime.getUptime();
        long uptimeSec = uptimeMs / 1000;
        info.put("uptime_seconds", uptimeSec);
        info.put("uptime_human", formatUptime(uptimeSec));
        info.put("started_at", Instant.ofEpochMilli(System.currentTimeMillis() - uptimeMs).toString());

        // Memory (JVM)
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        long heapUsed = mem.getHeapMemoryUsage().getUsed() / 1024 / 1024;
        long heapMax  = mem.getHeapMemoryUsage().getMax()  / 1024 / 1024;
        info.put("heap_used_mb", heapUsed);
        info.put("heap_max_mb", heapMax);

        // System memory
        long totalRam = ((com.sun.management.OperatingSystemMXBean)
                ManagementFactory.getOperatingSystemMXBean()).getTotalMemorySize() / 1024 / 1024;
        long freeRam  = ((com.sun.management.OperatingSystemMXBean)
                ManagementFactory.getOperatingSystemMXBean()).getFreeMemorySize()  / 1024 / 1024;
        info.put("system_ram_total_mb", totalRam);
        info.put("system_ram_free_mb",  freeRam);

        // CPU
        double cpu = ((com.sun.management.OperatingSystemMXBean)
                ManagementFactory.getOperatingSystemMXBean()).getCpuLoad() * 100;
        info.put("cpu_pct", Math.round(cpu * 10.0) / 10.0);

        // Disk
        File disk = new File("/");
        long diskTotal = disk.getTotalSpace()  / 1024 / 1024 / 1024;
        long diskFree  = disk.getUsableSpace() / 1024 / 1024 / 1024;
        info.put("disk_total_gb", diskTotal);
        info.put("disk_free_gb",  diskFree);

        info.put("timestamp", Instant.now().toString());
        info.put("status", "UP");

        return ResponseEntity.ok(info);
    }

    private String formatUptime(long sec) {
        long d = sec / 86400;
        long h = (sec % 86400) / 3600;
        long m = (sec % 3600) / 60;
        if (d > 0) return d + "d " + h + "h " + m + "m";
        if (h > 0) return h + "h " + m + "m";
        return m + "m " + (sec % 60) + "s";
    }
}
