"""
Sensors module for autonomous taxi simulation.

This module provides realistic sensor simulation for the self-driving car:
- Camera: Wide field of view with noisy/ambiguous data
- Lidar: Accurate point cloud with limited range
- Sonar: Very accurate short-range distance sensors
- GPS: Position with realistic error, map integration
- Car Telemetry: Internal vehicle sensors
- Car Control: Control interface for the RL agent
- Sensor Fusion: Unified sensor data representation

The RL agent receives ONLY sensor data (not ground truth environment state),
forcing it to work with realistic sensor limitations.
"""

from .camera import CameraSensor
from .lidar import LidarSensor
from .sonar import SonarSensor
from .gps import GPSSensor
from .car_telemetry import CarTelemetry
from .car_control import CarControl
from .sensor_fusion import SensorFusion

__all__ = [
    "CameraSensor",
    "LidarSensor",
    "SonarSensor",
    "GPSSensor",
    "CarTelemetry",
    "CarControl",
    "SensorFusion"
]

__version__ = "1.0.0"
__author__ = "Agent 4 - Sensor Simulation Agent"
