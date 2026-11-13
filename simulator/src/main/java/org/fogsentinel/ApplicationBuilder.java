package org.fogsentinel;

import java.util.ArrayList;
import java.util.List;

import org.fog.application.AppEdge;
import org.fog.application.AppLoop;
import org.fog.application.Application;
import org.fog.application.selectivity.FractionalSelectivity;
import org.fog.entities.Tuple;

/**
 * Builds the DDF Application model for FogSentinel:
 * - Module: classifier_service (simulates feature processing + neural net forward inference)
 * - Sensor Tuple: IOT_TRAFFIC (115 float64 features, 920 bytes payload, 1000 MIPS)
 * - Actuator Tuple: SECURITY_ALERT (classification label, confidence, action, 128 bytes payload, 50 MIPS)
 * - Loop: IOT_TRAFFIC -> classifier_service -> SECURITY_ALERT
 */
public class ApplicationBuilder {

    public static final String MODULE_CLASSIFIER = "classifier_service";
    public static final String TUPLE_TRAFFIC = "IOT_TRAFFIC";
    public static final String TUPLE_ALERT = "SECURITY_ALERT";

    // 115 features * 8 bytes = 920 bytes network payload
    public static final long TRAFFIC_NW_LENGTH = 920;
    // Estimated computational length in million instructions (MIPS) for MLP inference
    public static final long CLASSIFIER_CPU_LENGTH = 1000;
    // Alert response payload (128 bytes)
    public static final long ALERT_NW_LENGTH = 128;
    public static final long ALERT_CPU_LENGTH = 50;

    public static Application buildApplication(String appId, int userId) {
        Application application = Application.createApplication(appId, userId);

        // 1. Add application module: classifier_service with 20 MB RAM requirement
        application.addAppModule(MODULE_CLASSIFIER, 20);

        // 2. Add edges:
        // Sensor (IOT_TRAFFIC) -> classifier_service
        application.addAppEdge(TUPLE_TRAFFIC, MODULE_CLASSIFIER, CLASSIFIER_CPU_LENGTH, TRAFFIC_NW_LENGTH,
                TUPLE_TRAFFIC, Tuple.UP, AppEdge.SENSOR);

        // classifier_service -> Actuator (SECURITY_ALERT)
        application.addAppEdge(MODULE_CLASSIFIER, TUPLE_ALERT, ALERT_CPU_LENGTH, ALERT_NW_LENGTH,
                TUPLE_ALERT, Tuple.DOWN, AppEdge.ACTUATOR);

        // 3. Tuple mapping: 1 incoming IOT_TRAFFIC produces 1 outgoing SECURITY_ALERT
        application.addTupleMapping(MODULE_CLASSIFIER, TUPLE_TRAFFIC, TUPLE_ALERT, new FractionalSelectivity(1.0));

        // 4. Application loop to monitor end-to-end latency
        final AppLoop loop = new AppLoop(new ArrayList<String>() {{
            add(TUPLE_TRAFFIC);
            add(MODULE_CLASSIFIER);
            add(TUPLE_ALERT);
        }});

        List<AppLoop> loops = new ArrayList<>();
        loops.add(loop);
        application.setLoops(loops);

        return application;
    }
}

