package org.fogsentinel;

import java.util.List;

import org.fog.application.Application;
import org.fog.entities.FogDevice;
import org.fog.placement.ModuleMapping;
import org.fog.placement.ModulePlacement;
import org.fog.placement.ModulePlacementMapping;

/**
 * Implements strict, fair placement strategies for FogSentinel:
 * - FOG Placement: classifier_service is mapped directly to the local Fog Gateway.
 * - CLOUD Placement: classifier_service is mapped directly to the remote Cloud Server.
 * All workloads, topologies, and link characteristics remain completely identical.
 */
public class PlacementStrategy {

    public enum PlacementType {
        FOG,
        CLOUD;

        public static PlacementType fromString(String val) {
            if (val == null) return FOG;
            String lower = val.trim().toLowerCase();
            if (lower.equals("cloud")) return CLOUD;
            return FOG;
        }
    }

    public static ModulePlacement createPlacement(PlacementType placementType, List<FogDevice> fogDevices,
                                                  Application application) {
        ModuleMapping moduleMapping = ModuleMapping.createModuleMapping();

        if (placementType == PlacementType.FOG) {
            moduleMapping.addModuleToDevice(ApplicationBuilder.MODULE_CLASSIFIER, "fog-gateway");
        } else {
            moduleMapping.addModuleToDevice(ApplicationBuilder.MODULE_CLASSIFIER, "cloud");
        }

        return new ModulePlacementMapping(fogDevices, application, moduleMapping);
    }
}

