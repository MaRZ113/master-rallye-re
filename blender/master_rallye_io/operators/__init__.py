from .import_dx import IMPORT_SCENE_OT_master_rallye_dx
from .import_vehicle import IMPORT_SCENE_OT_master_rallye_vehicle
from .export_dx_positions import EXPORT_SCENE_OT_master_rallye_dx_positions

from .export_dx_attributes import EXPORT_SCENE_OT_master_rallye_dx_attributes
from .export_dx_topology import CLASSES as TOPOLOGY_CLASSES
from .vehicle_project import CLASSES as VEHICLE_PROJECT_CLASSES

CLASSES = (
    EXPORT_SCENE_OT_master_rallye_dx_attributes,
    IMPORT_SCENE_OT_master_rallye_dx,
    IMPORT_SCENE_OT_master_rallye_vehicle,
    EXPORT_SCENE_OT_master_rallye_dx_positions,
) + TOPOLOGY_CLASSES + VEHICLE_PROJECT_CLASSES
