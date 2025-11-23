"""
Sensor fusion module for autonomous taxi.

Combines data from all sensors (camera, lidar, sonar, GPS, telemetry)
into a unified representation for the RL agent.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from .camera import CameraSensor
from .lidar import LidarSensor
from .sonar import SonarSensor
from .gps import GPSSensor
from .car_telemetry import CarTelemetry
from .car_control import CarControl


class SensorFusion:
    """
    Integrates all sensors and provides unified sensor data to the RL agent.

    Ensures the RL agent only sees sensor data (with realistic limitations)
    and NOT the complete ground truth state of the environment.
    """

    def __init__(
        self,
        camera_config: Optional[Dict[str, Any]] = None,
        lidar_config: Optional[Dict[str, Any]] = None,
        sonar_config: Optional[Dict[str, Any]] = None,
        gps_config: Optional[Dict[str, Any]] = None,
        telemetry_config: Optional[Dict[str, Any]] = None,
        control_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize sensor fusion system.

        Args:
            camera_config: Configuration for camera sensor
            lidar_config: Configuration for lidar sensor
            sonar_config: Configuration for sonar sensor
            gps_config: Configuration for GPS sensor
            telemetry_config: Configuration for telemetry
            control_config: Configuration for car control
        """
        # Initialize sensors with provided configs or defaults
        self.camera = CameraSensor(**(camera_config or {}))
        self.lidar = LidarSensor(**(lidar_config or {}))
        self.sonar = SonarSensor(**(sonar_config or {}))
        self.gps = GPSSensor(**(gps_config or {}))
        self.telemetry = CarTelemetry(**(telemetry_config or {}))
        self.control = CarControl(**(control_config or {}))

        # Track time for timestamps
        self.start_time = time.time()
        self.simulation_time = 0.0

    def sense_all(
        self,
        car_position: Tuple[float, float],
        car_heading: float,
        car_state: Dict[str, Any],
        environment_state: Dict[str, Any],
        map_data: Optional[Dict[str, Any]] = None,
        destination: Optional[Tuple[float, float]] = None,
        delta_time: float = 0.1
    ) -> Dict[str, Any]:
        """
        Get combined sensor data from all sensors.

        This is the main interface for the RL agent to perceive the environment.

        Args:
            car_position: Current position of the car (x, y)
            car_heading: Current heading in degrees
            car_state: Full car state (velocity, etc.)
            environment_state: Environment state with vehicles and pedestrians
            map_data: Map data from Agent 1
            destination: Optional destination for routing
            delta_time: Time since last update

        Returns:
            Unified sensor data dictionary
        """
        # Update simulation time
        self.simulation_time += delta_time

        # Get current control state
        control_inputs = self.control.get_control_state()

        # Sense from all sensors
        camera_data = self.camera.sense(
            car_position,
            car_heading,
            environment_state,
            map_data
        )

        lidar_data = self.lidar.sense(
            car_position,
            car_heading,
            environment_state,
            map_data
        )

        sonar_data = self.sonar.sense(
            car_position,
            car_heading,
            environment_state,
            map_data
        )

        gps_data = self.gps.sense(
            car_position,
            car_heading,
            map_data,
            destination
        )

        telemetry_data = self.telemetry.sense(
            car_state,
            control_inputs,
            delta_time
        )

        # Combine all sensor data
        fused_data = {
            "camera": camera_data,
            "lidar": lidar_data,
            "sonar": sonar_data,
            "gps": gps_data,
            "telemetry": telemetry_data,
            "control_state": control_inputs,
            "timestamp": self.simulation_time,
            "real_time": time.time() - self.start_time
        }

        return fused_data

    def get_processed_state(
        self,
        raw_sensor_data: Dict[str, Any],
        state_representation: str = "feature_vector"
    ) -> Any:
        """
        Process raw sensor data into a state representation for the RL agent.

        Args:
            raw_sensor_data: Raw sensor data from sense_all()
            state_representation: Type of state representation
                - "feature_vector": Concatenated feature vector
                - "dict": Dictionary of processed features
                - "image": Multi-channel image representation

        Returns:
            Processed state in requested format
        """
        if state_representation == "feature_vector":
            return self._create_feature_vector(raw_sensor_data)
        elif state_representation == "dict":
            return self._create_feature_dict(raw_sensor_data)
        elif state_representation == "image":
            return self._create_image_representation(raw_sensor_data)
        else:
            raise ValueError(f"Unknown state representation: {state_representation}")

    def _create_feature_vector(self, sensor_data: Dict[str, Any]) -> np.ndarray:
        """
        Create a concatenated feature vector from sensor data.

        Returns:
            NumPy array with all relevant features
        """
        features = []

        # GPS features (5)
        gps = sensor_data["gps"]
        if gps["has_signal"]:
            features.extend(gps["position"])  # x, y
            features.append(gps["heading"])
            features.append(gps.get("speed_limit", 50) / 100.0)  # normalized
            features.append(gps.get("distance_to_destination", 1000) / 1000.0)  # normalized
        else:
            features.extend([0, 0, 0, 0.5, 1.0])  # defaults

        # Telemetry features (4)
        telemetry = sensor_data["telemetry"]
        features.append(telemetry["speed"] / 100.0)  # normalized speed
        features.append(telemetry["acceleration"] / 10.0)  # normalized
        features.append(telemetry["steering_angle"] / 35.0)  # normalized
        features.append(telemetry["fuel"] / 100.0)  # normalized

        # Sonar features (8) - distances from each sensor
        sonar = sensor_data["sonar"]["sensors"]
        sonar_names = ["front_left", "front_center", "front_right",
                       "rear_left", "rear_center", "rear_right",
                       "side_left", "side_right"]
        for name in sonar_names:
            distance = sonar.get(name, None)
            if distance is not None:
                features.append(min(1.0, distance / 10.0))  # normalized to 10m
            else:
                features.append(1.0)  # max distance if no detection

        # Camera features - count of detected objects by type
        camera = sensor_data["camera"]
        features.append(min(1.0, len(camera["vehicles"]) / 10.0))  # normalized count
        features.append(min(1.0, len(camera["pedestrians"]) / 10.0))
        features.append(min(1.0, len(camera["obstacles"]) / 10.0))

        # Lidar features - simplified point cloud statistics
        lidar = sensor_data["lidar"]
        points = lidar["points"]
        if len(points) > 0:
            distances = [p["distance"] for p in points]
            features.append(min(distances) / 50.0)  # closest object (normalized)
            features.append(np.mean(distances) / 50.0)  # average distance
            features.append(len(points) / 360.0)  # point density
        else:
            features.extend([1.0, 1.0, 0.0])

        return np.array(features, dtype=np.float32)

    def _create_feature_dict(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a structured dictionary of processed features.

        Returns:
            Dictionary with organized features
        """
        return {
            "position": sensor_data["gps"]["position"] if sensor_data["gps"]["has_signal"] else None,
            "heading": sensor_data["gps"]["heading"] if sensor_data["gps"]["has_signal"] else None,
            "speed": sensor_data["telemetry"]["speed"],
            "acceleration": sensor_data["telemetry"]["acceleration"],
            "steering_angle": sensor_data["telemetry"]["steering_angle"],
            "nearby_vehicles": len(sensor_data["camera"]["vehicles"]),
            "nearby_pedestrians": len(sensor_data["camera"]["pedestrians"]),
            "sonar_distances": sensor_data["sonar"]["sensors"],
            "lidar_points": sensor_data["lidar"]["points"],
            "speed_limit": sensor_data["gps"].get("speed_limit", 50),
            "fuel_level": sensor_data["telemetry"]["fuel"]
        }

    def _create_image_representation(self, sensor_data: Dict[str, Any]) -> np.ndarray:
        """
        Create a multi-channel image representation of sensor data.

        This could be used with CNN-based RL models.

        Returns:
            Multi-channel image (e.g., 84x84x4)
        """
        # This is a placeholder - full implementation would render sensors as images
        # For example:
        # - Channel 1: Lidar point cloud rendered as image
        # - Channel 2: Camera detections rendered as image
        # - Channel 3: Sonar distances rendered
        # - Channel 4: Map/route overlay

        # For now, return a simple representation
        image_size = 84
        channels = 4

        image = np.zeros((image_size, image_size, channels), dtype=np.float32)

        # This would be implemented based on specific visualization needs
        # Placeholder implementation
        return image

    def apply_control(
        self,
        throttle: Optional[float] = None,
        brake: Optional[float] = None,
        steering: Optional[float] = None,
        gear: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Apply control inputs to the car.

        This is the main interface for the RL agent to control the car.

        Args:
            throttle: Throttle position 0.0-1.0
            brake: Brake position 0.0-1.0
            steering: Steering -1.0 to 1.0
            gear: Gear selection (if manual)

        Returns:
            Control status
        """
        return self.control.set_control(throttle, brake, steering, gear)

    def update_control(self, delta_time: float, current_speed: float) -> Dict[str, Any]:
        """
        Update control system with smooth transitions.

        Args:
            delta_time: Time step
            current_speed: Current speed in m/s

        Returns:
            Updated control state
        """
        return self.control.update(delta_time, current_speed)

    def apply_control_to_physics(
        self,
        car_state: Dict[str, Any],
        delta_time: float
    ) -> Dict[str, Any]:
        """
        Apply control inputs to update physics.

        Args:
            car_state: Current car state
            delta_time: Time step

        Returns:
            Updated car state
        """
        return self.control.apply_to_physics(car_state, delta_time)

    def reset(self) -> None:
        """Reset all sensors and control to initial state."""
        self.control.reset()
        self.telemetry.reset()
        self.simulation_time = 0.0
        self.start_time = time.time()

    def get_all_sensor_info(self) -> Dict[str, Any]:
        """Get configuration information for all sensors."""
        return {
            "camera": self.camera.get_sensor_info(),
            "lidar": self.lidar.get_sensor_info(),
            "sonar": self.sonar.get_sensor_info(),
            "gps": self.gps.get_sensor_info(),
            "telemetry": self.telemetry.get_sensor_info(),
            "control": self.control.get_info(),
            "action_space": self.control.get_action_space_info()
        }

    def get_observation_space_info(self) -> Dict[str, Any]:
        """
        Get information about the observation space for the RL agent.

        Returns:
            Dictionary describing observation space dimensions and ranges
        """
        # Create a dummy sensor reading to determine dimensions
        dummy_data = {
            "gps": {"has_signal": True, "position": (0, 0), "heading": 0,
                   "speed_limit": 50, "distance_to_destination": 1000},
            "telemetry": {"speed": 0, "acceleration": 0, "steering_angle": 0, "fuel": 100},
            "sonar": {"sensors": {
                "front_left": 5, "front_center": 5, "front_right": 5,
                "rear_left": 5, "rear_center": 5, "rear_right": 5,
                "side_left": 5, "side_right": 5
            }},
            "camera": {"vehicles": [], "pedestrians": [], "obstacles": []},
            "lidar": {"points": [{"distance": 10, "angle": 0}]}
        }

        feature_vector = self._create_feature_vector(dummy_data)

        return {
            "type": "feature_vector",
            "shape": feature_vector.shape,
            "dimension": len(feature_vector),
            "description": "Fused sensor data as normalized feature vector"
        }
