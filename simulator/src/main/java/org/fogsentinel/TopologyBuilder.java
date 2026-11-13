package org.fogsentinel;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.power.PowerHost;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;
import org.cloudbus.cloudsim.sdn.overbooking.BwProvisionerOverbooking;
import org.cloudbus.cloudsim.sdn.overbooking.PeProvisionerOverbooking;
import org.fog.entities.Actuator;
import org.fog.entities.FogDevice;
import org.fog.entities.FogDeviceCharacteristics;
import org.fog.entities.Sensor;
import org.fog.policy.AppModuleAllocationPolicy;
import org.fog.scheduler.StreamOperatorScheduler;
import org.fog.utils.FogLinearPowerModel;
import org.fog.utils.FogUtils;
import org.fog.utils.distribution.DeterministicDistribution;
import org.fog.utils.distribution.Distribution;

/**
 * Builds the physical FogSentinel topology consisting of:
 * 1. Cloud Server (High MIPS, WAN latency)
 * 2. Fog Gateway (Intermediate MIPS, Local LAN to IoT, WAN to Cloud)
 * 3. IoT Edge Devices with attached network traffic sensors and alert actuators
 */
public class TopologyBuilder {

    private final List<FogDevice> fogDevices = new ArrayList<>();
    private final List<Sensor> sensors = new ArrayList<>();
    private final List<Actuator> actuators = new ArrayList<>();

    private FogDevice cloud;
    private FogDevice fogGateway;

    public static class TopologyResult {
        public final List<FogDevice> fogDevices;
        public final List<Sensor> sensors;
        public final List<Actuator> actuators;
        public final FogDevice cloud;
        public final FogDevice fogGateway;

        public TopologyResult(List<FogDevice> fogDevices, List<Sensor> sensors, List<Actuator> actuators,
                              FogDevice cloud, FogDevice fogGateway) {
            this.fogDevices = fogDevices;
            this.sensors = sensors;
            this.actuators = actuators;
            this.cloud = cloud;
            this.fogGateway = fogGateway;
        }
    }

    public TopologyResult buildTopology(int userId, String appId, int deviceCount, double recordRatePerSec, double wanLatencyMs) {
        fogDevices.clear();
        sensors.clear();
        actuators.clear();

        // 1. Cloud Data Centre: 44,800 MIPS, 40 GB RAM, 100 Mbps uplink, 10 Gbps downlink
        cloud = createFogDevice("cloud", 44800, 40000, 100, 10000, 0, 0.01, 16 * 103, 16 * 83.25);
        cloud.setParentId(-1);
        fogDevices.add(cloud);

        // 2. Fog Gateway: 4,000 MIPS, 8 GB RAM, 10 Gbps LAN bandwidth
        // WAN latency configured between Fog Gateway and Cloud
        fogGateway = createFogDevice("fog-gateway", 4000, 8000, 10000, 10000, 1, 0.0, 107.339, 83.4333);
        fogGateway.setParentId(cloud.getId());
        fogGateway.setUplinkLatency(wanLatencyMs);
        fogDevices.add(fogGateway);

        // Inter-transmission time in milliseconds (CloudSim simulation clock is in ms)
        // e.g. 1.0 rec/sec -> 1000.0 ms; 5.0 rec/sec -> 200.0 ms
        double interArrivalTimeMs = 1000.0 / recordRatePerSec;
        Distribution transmitDistribution = new DeterministicDistribution(interArrivalTimeMs);

        // 3. IoT Devices: 500 MIPS, 1 GB RAM, 2 ms LAN latency to gateway
        for (int i = 0; i < deviceCount; i++) {
            String deviceId = "iot-" + i;
            FogDevice iotDevice = createFogDevice(deviceId, 500, 1000, 10000, 10000, 2, 0.0, 87.53, 82.44);
            iotDevice.setParentId(fogGateway.getId());
            iotDevice.setUplinkLatency(2.0); // 2 ms local LAN link
            fogDevices.add(iotDevice);

            // Traffic Sensor on IoT device: generates IOT_TRAFFIC tuples
            Sensor sensor = new Sensor("sensor-" + i, "IOT_TRAFFIC", userId, appId, transmitDistribution);
            sensor.setGatewayDeviceId(iotDevice.getId());
            sensor.setLatency(1.0); // 1 ms device bus latency
            sensors.add(sensor);

            // Security Actuator on IoT device: receives SECURITY_ALERT tuples
            Actuator actuator = new Actuator("actuator-" + i, userId, appId, "SECURITY_ALERT");
            actuator.setGatewayDeviceId(iotDevice.getId());
            actuator.setLatency(1.0);
            actuators.add(actuator);
        }

        return new TopologyResult(fogDevices, sensors, actuators, cloud, fogGateway);
    }

    private FogDevice createFogDevice(String nodeName, long mips, int ram, long upBw, long downBw,
                                      int level, double ratePerMips, double busyPower, double idlePower) {
        List<Pe> peList = new ArrayList<>();
        peList.add(new Pe(0, new PeProvisionerOverbooking(mips)));

        int hostId = FogUtils.generateEntityId();
        long storage = 1000000;
        int bw = 10000;

        PowerHost host = new PowerHost(
                hostId,
                new RamProvisionerSimple(ram),
                new BwProvisionerOverbooking(bw),
                storage,
                peList,
                new StreamOperatorScheduler(peList),
                new FogLinearPowerModel(busyPower, idlePower)
        );

        List<Host> hostList = new ArrayList<>();
        hostList.add(host);

        String arch = "x86";
        String os = "Linux";
        String vmm = "Xen";
        double timeZone = 10.0;
        double cost = 3.0;
        double costPerMem = 0.05;
        double costPerStorage = 0.001;
        double costPerBw = 0.0;
        LinkedList<Storage> storageList = new LinkedList<>();

        FogDeviceCharacteristics characteristics = new FogDeviceCharacteristics(
                arch, os, vmm, host, timeZone, cost, costPerMem, costPerStorage, costPerBw
        );

        FogDevice fogDevice = null;
        try {
            fogDevice = new FogDevice(nodeName, characteristics,
                    new AppModuleAllocationPolicy(hostList), storageList, 10, upBw, downBw, 0, ratePerMips);
        } catch (Exception e) {
            e.printStackTrace();
        }

        if (fogDevice != null) {
            fogDevice.setLevel(level);
        }
        return fogDevice;
    }
}
