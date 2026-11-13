package org.fogsentinel;

import java.util.List;

import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.SimEvent;
import org.fog.entities.Actuator;
import org.fog.entities.FogDevice;
import org.fog.entities.Sensor;
import org.fog.placement.Controller;
import org.fog.utils.FogEvents;

/**
 * Custom FogSentinel Controller:
 * Subclasses standard iFogSim Controller to gracefully terminate simulation
 * WITHOUT calling System.exit(0), allowing multi-scenario parameter sweeps
 * and batch experimentation in the same JVM session.
 */
public class FogSentinelController extends Controller {

    public FogSentinelController(String name, List<FogDevice> fogDevices, List<Sensor> sensors,
                                 List<Actuator> actuators) {
        super(name, fogDevices, sensors, actuators);
    }

    @Override
    public void processEvent(SimEvent ev) {
        switch (ev.getTag()) {
            case FogEvents.APP_SUBMIT:
            case FogEvents.CONTROLLER_RESOURCE_MANAGE:
                manageResources();
                break;
            case FogEvents.STOP_SIMULATION:
                CloudSim.abruptallyTerminate();
                break;
            default:
                // Handle any other events
                break;
        }
    }
}
