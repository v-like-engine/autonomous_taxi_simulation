"""
Camera sensor simulation for autonomous taxi.

Characteristics:
- Wide field of view (50-100m radius)
- Ambiguous/inaccurate position data
- Confidence scores that degrade with distance
- May miss small objects or confuse object types
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional


class CameraSensor:
    """
    Simulates a camera sensor with wide field of view but noisy data.

    The camera can detect vehicles, pedestrians, obstacles, and lane markers
    within a large circular area, but with decreasing accuracy at greater distances.
    """

    def __init__(
        self,
        max_range: float = 75.0,  # meters
        position_noise_min: float = 2.0,  # meters
        position_noise_max: float = 5.0,  # meters
        min_confidence: float = 0.3,  # minimum confidence at max range
        detection_threshold: float = 0.4,  # objects below this confidence may be missed
        confusion_probability: float = 0.1  # probability of confusing object types
    ):
        """
        Initialize the camera sensor.

        Args:
            max_range: Maximum detection range in meters
            position_noise_min: Minimum position noise at close range
            position_noise_max: Maximum position noise at far range
            min_confidence: Minimum confidence score at maximum range
            detection_threshold: Confidence threshold below which objects may be missed
            confusion_probability: Probability of misidentifying object types
        """
        self.max_range = max_range
        self.position_noise_min = position_noise_min
        self.position_noise_max = position_noise_max
        self.min_confidence = min_confidence
        self.detection_threshold = detection_threshold
        self.confusion_probability = confusion_probability

    def sense(
        self,
        car_position: Tuple[float, float],
        car_heading: float,
        environment_state: Dict[str, Any],
        map_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get camera sensor data from the environment.

        Args:
            car_position: Current position of the car (x, y)
            car_heading: Current heading in degrees (0 = East, 90 = North)
            environment_state: Current state of the environment with vehicles and pedestrians
            map_data: Optional map data for lane markers and road boundaries

        Returns:
            Dictionary with detected vehicles, pedestrians, lane markers, and obstacles
        """
        detected_vehicles = []
        detected_pedestrians = []
        detected_obstacles = []
        detected_lane_markers = []

        # Detect vehicles
        if "vehicles" in environment_state:
            for vehicle in environment_state["vehicles"]:
                detection = self._detect_object(
                    car_position,
                    vehicle.get("position", (0, 0)),
                    object_type="vehicle",
                    object_data=vehicle
                )
                if detection is not None:
                    detected_vehicles.append(detection)

        # Detect pedestrians
        if "pedestrians" in environment_state:
            for pedestrian in environment_state["pedestrians"]:
                detection = self._detect_object(
                    car_position,
                    pedestrian.get("position", (0, 0)),
                    object_type="pedestrian",
                    object_data=pedestrian
                )
                if detection is not None:
                    detected_pedestrians.append(detection)

        # Detect lane markers from map data
        if map_data and "roads" in map_data:
            detected_lane_markers = self._detect_lane_markers(
                car_position,
                map_data["roads"]
            )

        # Detect obstacles from environment
        if "obstacles" in environment_state:
            for obstacle in environment_state["obstacles"]:
                detection = self._detect_object(
                    car_position,
                    obstacle.get("position", (0, 0)),
                    object_type="obstacle",
                    object_data=obstacle
                )
                if detection is not None:
                    detected_obstacles.append(detection)

        return {
            "vehicles": detected_vehicles,
            "pedestrians": detected_pedestrians,
            "lane_markers": detected_lane_markers,
            "obstacles": detected_obstacles,
            "sensor_type": "camera",
            "max_range": self.max_range
        }

    def _detect_object(
        self,
        car_position: Tuple[float, float],
        object_position: Tuple[float, float],
        object_type: str,
        object_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to detect a single object with realistic camera limitations.

        Args:
            car_position: Position of the car
            object_position: Position of the object
            object_type: Type of object (vehicle, pedestrian, obstacle)
            object_data: Additional data about the object

        Returns:
            Detection dictionary if detected, None otherwise
        """
        # Calculate distance to object
        distance = self._calculate_distance(car_position, object_position)

        # Check if object is within range
        if distance > self.max_range:
            return None

        # Calculate confidence based on distance
        confidence = self._calculate_confidence(distance)

        # Check if object is detected (may miss low-confidence detections)
        if confidence < self.detection_threshold and np.random.random() > confidence:
            return None

        # Add position noise
        noisy_position = self._add_position_noise(object_position, distance)

        # Determine detected type (may confuse object types)
        detected_type = self._determine_detected_type(object_type)

        # Build detection dictionary
        detection = {
            "type": detected_type,
            "position": noisy_position,
            "confidence": confidence,
            "distance": distance
        }

        # Add additional data for vehicles
        if object_type == "vehicle" and "vehicle_type" in object_data:
            detection["vehicle_type"] = object_data["vehicle_type"]

        return detection

    def _detect_lane_markers(
        self,
        car_position: Tuple[float, float],
        roads_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect lane markers within camera range.

        Lane markers are more accurately detected than moving objects.

        Args:
            car_position: Current position of the car
            roads_data: Road network data from map

        Returns:
            List of detected lane marker segments
        """
        detected_markers = []

        # Extract lane information if available
        if "lanes" not in roads_data:
            return detected_markers

        for lane in roads_data["lanes"]:
            # Get lane center line or edges
            if "center_line" in lane:
                points = lane["center_line"]
            elif "points" in lane:
                points = lane["points"]
            else:
                continue

            # Check each segment of the lane
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]

                # Calculate distance to segment midpoint
                midpoint = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                distance = self._calculate_distance(car_position, midpoint)

                if distance <= self.max_range:
                    # Lane markers are detected more accurately
                    noise_factor = 0.3  # Less noise than objects
                    noise = self._interpolate_noise(distance) * noise_factor

                    detected_markers.append({
                        "start": self._add_noise_to_point(p1, noise),
                        "end": self._add_noise_to_point(p2, noise),
                        "type": lane.get("type", "solid"),
                        "confidence": min(1.0, self._calculate_confidence(distance) + 0.2)
                    })

        return detected_markers

    def _calculate_distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions."""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)

    def _calculate_confidence(self, distance: float) -> float:
        """
        Calculate detection confidence based on distance.

        Confidence degrades linearly from 1.0 at distance 0 to min_confidence at max_range.
        """
        if distance <= 0:
            return 1.0
        if distance >= self.max_range:
            return self.min_confidence

        # Linear interpolation
        confidence = 1.0 - (1.0 - self.min_confidence) * (distance / self.max_range)
        return max(self.min_confidence, min(1.0, confidence))

    def _interpolate_noise(self, distance: float) -> float:
        """
        Calculate position noise magnitude based on distance.

        Noise increases linearly from min to max as distance increases.
        """
        if distance <= 0:
            return self.position_noise_min
        if distance >= self.max_range:
            return self.position_noise_max

        # Linear interpolation
        noise = self.position_noise_min + (
            (self.position_noise_max - self.position_noise_min) *
            (distance / self.max_range)
        )
        return noise

    def _add_position_noise(
        self,
        position: Tuple[float, float],
        distance: float
    ) -> Tuple[float, float]:
        """
        Add realistic position noise based on distance.

        Args:
            position: Original position
            distance: Distance from camera

        Returns:
            Noisy position
        """
        noise_magnitude = self._interpolate_noise(distance)

        # Add random noise in x and y directions
        noise_x = np.random.normal(0, noise_magnitude)
        noise_y = np.random.normal(0, noise_magnitude)

        return (position[0] + noise_x, position[1] + noise_y)

    def _add_noise_to_point(
        self,
        point: Tuple[float, float],
        noise_magnitude: float
    ) -> Tuple[float, float]:
        """Add noise to a point with given magnitude."""
        noise_x = np.random.normal(0, noise_magnitude)
        noise_y = np.random.normal(0, noise_magnitude)
        return (point[0] + noise_x, point[1] + noise_y)

    def _determine_detected_type(self, actual_type: str) -> str:
        """
        Determine the detected object type, possibly with confusion.

        Camera may sometimes confuse pedestrians with obstacles or vice versa.
        """
        if np.random.random() < self.confusion_probability:
            # Confuse object type
            if actual_type == "pedestrian":
                return np.random.choice(["pedestrian", "obstacle"], p=[0.7, 0.3])
            elif actual_type == "obstacle":
                return np.random.choice(["obstacle", "pedestrian"], p=[0.8, 0.2])

        return actual_type

    def get_sensor_info(self) -> Dict[str, Any]:
        """Get information about the sensor configuration."""
        return {
            "type": "camera",
            "max_range": self.max_range,
            "position_noise_range": (self.position_noise_min, self.position_noise_max),
            "min_confidence": self.min_confidence,
            "field_of_view": "360 degrees (omnidirectional)",
            "detection_threshold": self.detection_threshold
        }
