"""
Traffic simulation module for autonomous taxi simulation.

This module provides realistic traffic simulation including:
- Vehicles (cars, trucks) with physics-based movement
- Pedestrians with realistic behavior
- Temperature-based random driver behavior
- Traffic management and spawning
- Collision detection and spatial queries
"""

# Vehicle components
from .vehicle import (
    Vehicle,
    VehicleType,
    VehicleSpecs,
    VehicleState,
    VEHICLE_SPECS
)

# Pedestrian components
from .pedestrian import (
    Pedestrian,
    PedestrianState,
    PedestrianTarget,
    create_pedestrian_group
)

# Behavior components
from .behavior import (
    DriverBehavior,
    PedestrianBehavior,
    BehaviorType,
    generate_temperature_distribution,
    get_behavior_description
)

# Traffic management
from .traffic_manager import (
    TrafficManager,
    SpatialGrid
)

__all__ = [
    # Vehicle
    'Vehicle',
    'VehicleType',
    'VehicleSpecs',
    'VehicleState',
    'VEHICLE_SPECS',

    # Pedestrian
    'Pedestrian',
    'PedestrianState',
    'PedestrianTarget',
    'create_pedestrian_group',

    # Behavior
    'DriverBehavior',
    'PedestrianBehavior',
    'BehaviorType',
    'generate_temperature_distribution',
    'get_behavior_description',

    # Traffic Manager
    'TrafficManager',
    'SpatialGrid',
]

__version__ = '1.0.0'
__author__ = 'Agent 2 - Traffic Simulation'
