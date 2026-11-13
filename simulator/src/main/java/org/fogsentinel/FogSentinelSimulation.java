package org.fogsentinel;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;

import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.core.CloudSim;
import org.fog.application.Application;
import org.fog.entities.FogBroker;
import org.fog.placement.ModulePlacement;
import org.fog.utils.Config;
import org.fog.utils.TimeKeeper;

/**
 * Main simulation runner for FogSentinel:
 * Supports:
 * 1. Quick Faculty Demo Mode (--quick):
 *    Compares Fog vs Cloud under 10 devices, 1.0 rec/sec, 100 ms WAN latency.
 * 2. Full Parameter Sweep Mode (--sweep):
 *    Evaluates 48 scenarios across:
 *    - 4 device counts: 10, 50, 100, 200
 *    - 2 traffic rates: 1.0, 5.0 records/sec
 *    - 3 WAN latencies: 25.0, 100.0, 200.0 ms
 *    - 2 placements: fog, cloud
 * 3. Individual custom scenario execution via CLI options.
 */
public class FogSentinelSimulation {

    public static MetricsCollector.ScenarioResult runScenario(int deviceCount, double recordRate,
                                                             double wanLatencyMs, String placementStr,
                                                             double simDurationSec, int runIndex) {
        long wallStart = System.currentTimeMillis();
        PlacementStrategy.PlacementType placementType = PlacementStrategy.PlacementType.fromString(placementStr);

        try {
            Log.disable();
            MetricsCollector.resetSimulationState();

            int numUser = 1;
            Calendar calendar = Calendar.getInstance();
            CloudSim.init(numUser, calendar, false);

            String appId = "fogsentinel_app_" + runIndex;
            FogBroker broker = new FogBroker("broker_" + runIndex);

            Application application = ApplicationBuilder.buildApplication(appId, broker.getId());
            application.setUserId(broker.getId());

            TopologyBuilder topologyBuilder = new TopologyBuilder();
            TopologyBuilder.TopologyResult topology = topologyBuilder.buildTopology(
                    broker.getId(), appId, deviceCount, recordRate, wanLatencyMs
            );

            // Duration in milliseconds (simDurationSec * 1000)
            Config.MAX_SIMULATION_TIME = (int) (Config.TRANSMISSION_START_DELAY + (simDurationSec * 1000.0));

            ModulePlacement placement = PlacementStrategy.createPlacement(placementType, topology.fogDevices, application);

            FogSentinelController controller = new FogSentinelController("master-controller-" + runIndex, topology.fogDevices,
                    topology.sensors, topology.actuators);

            controller.submitApplication(application, placement);

            TimeKeeper.getInstance().setSimulationStartTime(System.currentTimeMillis());

            CloudSim.startSimulation();
            CloudSim.stopSimulation();

            return MetricsCollector.extractMetrics(deviceCount, recordRate, wanLatencyMs,
                    placementStr, simDurationSec, topology.cloud, topology.fogGateway, wallStart);

        } catch (Exception e) {
            System.err.printf("Error running scenario [Dev=%d, Rate=%.1f, Lat=%.1f, Place=%s]: %s%n",
                    deviceCount, recordRate, wanLatencyMs, placementStr, e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    public static void runQuickDemo(String outputCsv) {
        System.out.println("=========================================================================");
        System.out.println("            FogSentinel — Quick Simulation Demo (Faculty Mode)           ");
        System.out.println("=========================================================================");
        System.out.println("Parameters: 10 IoT Devices | 1.0 record/sec | 100 ms WAN Latency (one-way)");
        System.out.println("-------------------------------------------------------------------------");

        List<MetricsCollector.ScenarioResult> results = new ArrayList<>();

        System.out.print("[1/2] Running Fog-Side Placement... ");
        MetricsCollector.ScenarioResult fogRes = runScenario(10, 1.0, 100.0, "fog", 60.0, 1);
        if (fogRes != null) {
            results.add(fogRes);
            System.out.printf("DONE. Completed: %d | Mean Latency: %.2f ms | WAN Bytes: %d%n",
                    fogRes.completedCount, fogRes.meanLatencyMs, fogRes.wanBytesTransmitted);
        }

        System.out.print("[2/2] Running Cloud-Side Placement... ");
        MetricsCollector.ScenarioResult cloudRes = runScenario(10, 1.0, 100.0, "cloud", 60.0, 2);
        if (cloudRes != null) {
            results.add(cloudRes);
            System.out.printf("DONE. Completed: %d | Mean Latency: %.2f ms | WAN Bytes: %d%n",
                    cloudRes.completedCount, cloudRes.meanLatencyMs, cloudRes.wanBytesTransmitted);
        }

        try {
            MetricsCollector.saveResultsToCsv(results, outputCsv);
            System.out.println("\nResults saved to: " + outputCsv);
        } catch (IOException e) {
            System.err.println("Failed to write CSV: " + e.getMessage());
        }

        printComparisonTable(results);
    }

    public static void runSweep(String outputCsv) {
        System.out.println("=========================================================================");
        System.out.println("          FogSentinel — Full 48-Scenario Parameter Sweep                 ");
        System.out.println("=========================================================================");

        int[] deviceCounts = {10, 50, 100, 200};
        double[] trafficRates = {1.0, 5.0};
        double[] wanLatencies = {25.0, 100.0, 200.0};
        String[] placements = {"fog", "cloud"};

        int totalScenarios = deviceCounts.length * trafficRates.length * wanLatencies.length * placements.length;
        System.out.printf("Total configurations: %d (4 devices x 2 rates x 3 latencies x 2 placements)%n", totalScenarios);

        List<MetricsCollector.ScenarioResult> results = new ArrayList<>();
        int count = 0;

        for (int dev : deviceCounts) {
            for (double rate : trafficRates) {
                for (double lat : wanLatencies) {
                    for (String place : placements) {
                        count++;
                        System.out.printf("[%2d/%2d] Dev=%-3d Rate=%-3.1f Lat=%-5.1f Place=%-5s ... ",
                                count, totalScenarios, dev, rate, lat, place);

                        MetricsCollector.ScenarioResult res = runScenario(dev, rate, lat, place, 60.0, count);
                        if (res != null) {
                            results.add(res);
                            System.out.printf("Done. Comp=%-4d Mean=%.2f ms Med=%.2f ms P95=%.2f ms WAN=%d KB%n",
                                    res.completedCount, res.meanLatencyMs, res.medianLatencyMs, res.p95LatencyMs,
                                    res.wanBytesTransmitted / 1024);
                        } else {
                            System.out.println("FAILED.");
                        }
                    }
                }
            }
        }

        try {
            MetricsCollector.saveResultsToCsv(results, outputCsv);
            System.out.println("\nSweep complete! Saved all " + results.size() + " records to: " + outputCsv);
        } catch (IOException e) {
            System.err.println("Failed to write CSV: " + e.getMessage());
        }
    }

    private static void printComparisonTable(List<MetricsCollector.ScenarioResult> results) {
        System.out.println("\n+--------------------+--------------+----------------+---------------+---------------+--------------------+");
        System.out.println("| Placement          | Completed    | Mean Lat (ms)  | Med Lat (ms)  | P95 Lat (ms)  | WAN Traffic (KB)   |");
        System.out.println("+--------------------+--------------+----------------+---------------+---------------+--------------------+");
        for (MetricsCollector.ScenarioResult r : results) {
            System.out.printf("| %-18s | %-12d | %-14.2f | %-13.2f | %-13.2f | %-18.2f |%n",
                    r.placement.toUpperCase(), r.completedCount, r.meanLatencyMs, r.medianLatencyMs,
                    r.p95LatencyMs, r.wanBytesTransmitted / 1024.0);
        }
        System.out.println("+--------------------+--------------+----------------+---------------+---------------+--------------------+");
    }

    public static void main(String[] args) {
        boolean sweep = false;
        boolean quick = false;
        int devices = 10;
        double rate = 1.0;
        double latency = 100.0;
        String placement = "fog";
        double simTime = 60.0;
        String outputCsv = "outputs/simulation/simulation_results.csv";

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--sweep":
                    sweep = true;
                    break;
                case "--quick":
                    quick = true;
                    break;
                case "--devices":
                    devices = Integer.parseInt(args[++i]);
                    break;
                case "--rate":
                    rate = Double.parseDouble(args[++i]);
                    break;
                case "--latency":
                    latency = Double.parseDouble(args[++i]);
                    break;
                case "--placement":
                    placement = args[++i];
                    break;
                case "--sim-time":
                    simTime = Double.parseDouble(args[++i]);
                    break;
                case "--output-csv":
                    outputCsv = args[++i];
                    break;
            }
        }

        if (sweep) {
            runSweep(outputCsv);
        } else if (quick || args.length == 0) {
            String quickCsv = outputCsv.replace("simulation_results.csv", "quick_demo_results.csv");
            runQuickDemo(quickCsv);
        } else {
            System.out.printf("Running single scenario: Dev=%d, Rate=%.1f, Lat=%.1f, Place=%s%n",
                    devices, rate, latency, placement);
            MetricsCollector.ScenarioResult r = runScenario(devices, rate, latency, placement, simTime, 1);
            if (r != null) {
                List<MetricsCollector.ScenarioResult> single = new ArrayList<>();
                single.add(r);
                try {
                    MetricsCollector.saveResultsToCsv(single, outputCsv);
                    System.out.println("Result saved to " + outputCsv);
                } catch (IOException e) {
                    System.err.println("Error saving result: " + e.getMessage());
                }
                printComparisonTable(single);
            }
        }
    }
}
