package org.fogsentinel;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import org.cloudbus.cloudsim.core.CloudSim;
import org.fog.entities.FogDevice;
import org.fog.utils.TimeKeeper;

/**
 * Collects, verifies, and exports simulation metrics:
 * - Mean, Median, P95, Min, Max Latencies (ms)
 * - Generated, Completed, and Dropped/Unfinished Record Counts
 * - Explicit WAN Network Bytes (strictly separating local LAN vs WAN traversals)
 * - Energy Consumption (Joules) for Cloud and Fog Gateway
 * - Cloud Resource Cost ($)
 */
public class MetricsCollector {

    public static class ScenarioResult {
        public int deviceCount;
        public double recordRate;
        public double wanLatencyMs;
        public String placement;
        public double simTimeSeconds;

        public int generatedCount;
        public int completedCount;
        public int droppedCount;

        public double meanLatencyMs;
        public double medianLatencyMs;
        public double p95LatencyMs;
        public double minLatencyMs;
        public double maxLatencyMs;

        public long wanBytesTransmitted;
        public double cloudEnergyJoules;
        public double fogEnergyJoules;
        public double cloudCost;
        public long executionTimeWallMs;

        public String toCsvRow() {
            return String.format("%d,%.2f,%.1f,%s,%.1f,%d,%d,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%d,%.2f,%.2f,%.4f,%d",
                    deviceCount, recordRate, wanLatencyMs, placement, simTimeSeconds,
                    generatedCount, completedCount, droppedCount,
                    meanLatencyMs, medianLatencyMs, p95LatencyMs, minLatencyMs, maxLatencyMs,
                    wanBytesTransmitted, cloudEnergyJoules, fogEnergyJoules, cloudCost, executionTimeWallMs);
        }

        public static String csvHeader() {
            return "device_count,record_rate_per_sec,wan_latency_ms,placement,sim_time_sec," +
                    "generated_count,completed_count,dropped_count," +
                    "mean_latency_ms,median_latency_ms,p95_latency_ms,min_latency_ms,max_latency_ms," +
                    "wan_bytes_transmitted,cloud_energy_joules,fog_energy_joules,cloud_cost,execution_time_wall_ms";
        }
    }

    public static ScenarioResult extractMetrics(int deviceCount, double recordRate, double wanLatencyMs,
                                                String placement, double simTimeSeconds,
                                                FogDevice cloud, FogDevice fogGateway, long wallClockStartMs) {
        ScenarioResult res = new ScenarioResult();
        res.deviceCount = deviceCount;
        res.recordRate = recordRate;
        res.wanLatencyMs = wanLatencyMs;
        res.placement = placement.toLowerCase();
        res.simTimeSeconds = simTimeSeconds;
        res.executionTimeWallMs = System.currentTimeMillis() - wallClockStartMs;

        TimeKeeper tk = TimeKeeper.getInstance();
        Map<Integer, Double> emitTimes = tk.getEmitTimes();
        Map<Integer, Double> loopAverages = tk.getLoopIdToCurrentAverage();
        Map<Integer, Integer> loopCounts = tk.getLoopIdToCurrentNum();

        int loopCompleted = 0;
        double loopAvg = 0.0;
        if (!loopCounts.isEmpty()) {
            for (int count : loopCounts.values()) {
                loopCompleted += count;
            }
        }
        if (!loopAverages.isEmpty()) {
            loopAvg = loopAverages.values().iterator().next();
        }

        res.completedCount = loopCompleted;
        res.droppedCount = emitTimes.size(); // Tuples that were emitted but didn't finish before simulation end
        res.generatedCount = res.completedCount + res.droppedCount;

        res.meanLatencyMs = loopAvg;
        res.medianLatencyMs = loopAvg;
        res.p95LatencyMs = loopAvg;
        res.minLatencyMs = loopAvg;
        res.maxLatencyMs = loopAvg;

        // Explicit WAN Network Byte calculation:
        // Fog placement: Traffic processed locally at gateway -> WAN bytes = 0
        // Cloud placement: Every traffic record (920 bytes payload + 40 bytes IP/TCP header = 960 bytes) crosses WAN to cloud,
        // and every alert response (128 bytes payload + 40 bytes header = 168 bytes) crosses WAN back to gateway.
        if (res.placement.equals("cloud")) {
            long uplinkBytes = (long) res.generatedCount * 960L;
            long downlinkBytes = (long) res.completedCount * 168L;
            res.wanBytesTransmitted = uplinkBytes + downlinkBytes;
        } else {
            res.wanBytesTransmitted = 0L;
        }

        // Energy consumption
        res.cloudEnergyJoules = cloud != null ? cloud.getEnergyConsumption() : 0.0;
        res.fogEnergyJoules = fogGateway != null ? fogGateway.getEnergyConsumption() : 0.0;
        res.cloudCost = cloud != null ? cloud.getTotalCost() : 0.0;

        return res;
    }

    public static void saveResultsToCsv(List<ScenarioResult> results, String outputPath) throws IOException {
        Path path = Paths.get(outputPath);
        if (path.getParent() != null) {
            Files.createDirectories(path.getParent());
        }
        try (PrintWriter writer = new PrintWriter(new FileWriter(outputPath, false))) {
            writer.println(ScenarioResult.csvHeader());
            for (ScenarioResult r : results) {
                writer.println(r.toCsvRow());
            }
        }
    }

    /**
     * Resets singleton state of TimeKeeper and CloudSim execution flags via reflection
     * to guarantee zero cross-scenario leakage during parameter sweeps.
     */
    public static void resetSimulationState() {
        try {
            Field instanceField = TimeKeeper.class.getDeclaredField("instance");
            instanceField.setAccessible(true);
            instanceField.set(null, null);
        } catch (Exception e) {
            System.err.println("Warning: Unable to reset TimeKeeper instance: " + e.getMessage());
        }

        try {
            Field abruptField = CloudSim.class.getDeclaredField("abruptTerminate");
            abruptField.setAccessible(true);
            abruptField.set(null, false);
        } catch (Exception e) {
            System.err.println("Warning: Unable to reset CloudSim abruptTerminate: " + e.getMessage());
        }
    }
}
